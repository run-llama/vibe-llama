"""
Workflow editing handler for AI Agent CLI.

Handles editing existing workflows and runbooks using diff-based iterative editing.
"""

import difflib
from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage
from workflows import Context
from workflows.events import InputRequiredEvent
from typing import Optional
from llama_index.core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vibe_llama.docuflows.commons.core import generate_runbook, load_context_files
from vibe_llama.docuflows.editing import DiffEditingWorkflow
from vibe_llama.docuflows.commons import CLIFormatter, StreamEvent
from vibe_llama.docuflows.commons.typed_state import WorkflowState


async def handle_edit_workflow(
    ctx: Context[WorkflowState],
    edit_request: str,
    llm: LLM,
    conversation_history: Optional[list[ChatMessage]] = None,
) -> InputRequiredEvent:
    """Edit the current workflow using diff-based iterative editing."""
    # Use pending workflow edit as the starting point if it exists (for iterative editing)
    # Otherwise fall back to the current workflow
    pending_workflow = (await ctx.store.get_state()).pending_workflow_edit
    current_workflow = (
        pending_workflow
        if pending_workflow
        else (await ctx.store.get_state()).current_workflow
    )

    if not current_workflow:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "❌ No workflow to edit. Please generate a workflow first."
                ),
                newline_after=True,
            )
        )
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text("What would you like to do?"),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore

    if not edit_request:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "What changes would you like to make to the workflow?"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore

    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.tool_action(
                "EditWorkflow", f"request='{edit_request}'"
            ),
            newline_after=True,
        )
    )

    try:
        # Load context data
        context_str = await load_context_files(ctx)

        # Get generation context
        original_task = (await ctx.store.get_state()).generation_task
        reference_path = (await ctx.store.get_state()).generation_reference_path

        # Use provided conversation history or fall back to general chat history
        if conversation_history:
            recent_context = conversation_history
        else:
            # Get recent chat history for additional context (legacy behavior)
            chat_history = (await ctx.store.get_state()).chat_history
            recent_context = ""
            if len(chat_history) > 4:
                recent_messages = chat_history[-4:]
                recent_context = "\n".join(
                    [f"{msg.role}: {msg.content}" for msg in recent_messages]
                )

        # Create and run the diff editing workflow with event streaming
        diff_workflow = DiffEditingWorkflow(llm=llm, timeout=None)

        # Run the diff editing workflow and stream events
        handler = diff_workflow.run(
            current_workflow=current_workflow,
            edit_request=edit_request,
            context_str=context_str,
            original_task=original_task,
            reference_path=reference_path,
            recent_context=recent_context,
            max_iterations=3,
        )

        # Stream events from the sub-workflow to the main workflow
        edited_workflow = None
        edit_history = None

        async for event in handler.stream_events():
            # Forward all StreamEvents to the main workflow
            if isinstance(event, StreamEvent):
                ctx.write_event_to_stream(event)

        # Get the final result
        result = await handler
        edited_workflow = result.final_code
        edit_history = result.edit_history

        ctx.write_event_to_stream(
            StreamEvent(rich_content=CLIFormatter.indented_text(""), newline_after=True)  # type: ignore
        )

        # Store the edited workflow temporarily for FIRST review (diff only)
        async with ctx.store.edit_state() as state:
            state.pending_workflow_edit = edited_workflow
            state.edit_session_history = edit_history

        # Generate and show diff

        # Create unified diff
        original_lines = current_workflow.splitlines(keepends=True)
        edited_lines = edited_workflow.splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                original_lines,
                edited_lines,
                fromfile="original_workflow.py",
                tofile="edited_workflow.py",
                lineterm="",
            )
        )

        if diff:
            ctx.write_event_to_stream(
                StreamEvent(
                    rich_content=CLIFormatter.indented_text(  # type: ignore
                        "📋 Final changes made to workflow:"
                    ),
                    newline_after=True,
                )
            )

            # Display diff with Rich syntax highlighting
            diff_text = "".join(diff)
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.diff_preview(diff_text),
                    newline_after=True,
                )
            )
        else:
            ctx.write_event_to_stream(
                StreamEvent(
                    rich_content=CLIFormatter.indented_text(  # type: ignore
                        "ℹ️ No changes detected in workflow code"
                    ),
                    newline_after=True,
                )
            )

        # Update editing conversation history with this session
        edit_conversation = (await ctx.store.get_state()).edit_conversation_history

        # Add user's edit request
        edit_conversation.append(
            ChatMessage(role=MessageRole.USER, content=edit_request)
        )

        # Create assistant response with the actual diff
        diff_text = "".join(diff) if diff else "No changes to code structure"
        assistant_response = f"I applied {result.total_iterations} iterations with {sum(len(h['applied_changes']) for h in edit_history)} changes:\n\n```diff\n{diff_text}\n```"

        edit_conversation.append(
            ChatMessage(role=MessageRole.ASSISTANT, content=assistant_response)
        )
        async with ctx.store.edit_state() as state:
            state.edit_conversation_history = edit_conversation

        # Show edit session summary
        if edit_history:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        f"✨ Editing completed in {result.total_iterations} iterations with {sum(len(h['applied_changes']) for h in edit_history)} total changes applied"
                    ),
                    newline_after=True,
                )
            )

        # Set status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = f"Successfully edited workflow using diff-based approach: '{edit_request}'. Applied {result.total_iterations} iterations of changes."

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "Approve these changes? (y/yes to approve, or describe what to change differently, or 'cancel'/'test'/'load' to exit):"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="", tag="review_diff_conversational")  # type: ignore

    except Exception as e:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"❌ Error editing workflow: {str(e)}"
                ),
                newline_after=True,
            )
        )
        # Set error status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = (
                f"Failed to edit workflow due to error: {str(e)}"
            )

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "Let's try again. What would you like to do?"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore


async def handle_generate_runbook_after_diff(
    ctx: Context[WorkflowState], llm: LLM
) -> InputRequiredEvent:
    """Generate runbook after diff approval (second stage of editing)"""
    pending_workflow = (await ctx.store.get_state()).pending_workflow_edit

    if not pending_workflow:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "❌ No pending workflow changes found."
                ),
                newline_after=True,
            )
        )
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text("What would you like to do?"),  # type: ignore
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore

    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.indented_text("📋 Generating updated runbook..."),
            newline_after=True,
        )
    )

    try:
        # Get context for runbook generation
        (await ctx.store.get_state()).generation_task
        edit_request = "Updated workflow based on user edits"

        updated_runbook = await generate_runbook(
            pending_workflow, edit_request, llm, ctx
        )

        # Store runbook for final review
        async with ctx.store.edit_state() as state:
            state.pending_runbook_edit = updated_runbook

        ctx.write_event_to_stream(
            StreamEvent(rich_content=CLIFormatter.indented_text(""), newline_after=True)  # type: ignore
        )

        # Display the generated runbook for review
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.runbook_output(
                    updated_runbook, "📋 Updated Runbook"
                ),
                newline_after=True,
            )
        )

        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(  # type: ignore
                    "✅ Runbook generated! Ready for final review."
                ),
                newline_after=True,
            )
        )

        # Set status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = "Generated updated runbook after diff approval. Both workflow and runbook are ready for final save."

        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(  # type: ignore
                    "Would you like to save both the code changes and updated runbook? (y/n):"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="", tag="review_edit")  # type: ignore

    except Exception as e:
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(  # type: ignore
                    f"⚠️ Failed to generate runbook: {e}"
                ),
                newline_after=True,
            )
        )
        # Fallback: keep current runbook and proceed to final review
        current_runbook = (await ctx.store.get_state()).current_runbook
        async with ctx.store.edit_state() as state:
            state.pending_runbook_edit = current_runbook

        # Set error status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = f"Failed to generate updated runbook: {str(e)}. Proceeding with code changes only."

        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(  # type: ignore
                    "Runbook generation failed, but code changes are ready. Save code changes? (y/n):"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="", tag="review_edit")  # type: ignore


async def interpret_user_intent(user_input: str, llm: LLM) -> str:
    """Use LLM to interpret user intent: approve, continue, or exit"""

    class UserIntent(BaseModel):
        """User's intent for the edit review."""

        intent: str = Field(..., description="One of: 'approve', 'continue', or 'exit'")
        reasoning: str = Field(
            ..., description="Brief explanation of why this intent was chosen"
        )

    intent_prompt = f"""Analyze this user response to determine their intent regarding code changes they just reviewed.

User response: "{user_input}"

Classify the intent as one of:
- "approve": User is satisfied and wants to proceed (e.g., "yes", "looks good", "perfect", "approve this")
- "continue": User wants to make additional changes or refinements (e.g., "change X instead", "also add Y", "fix the formatting")
- "exit": User wants to stop editing and do something else (e.g., "cancel", "let me test this first", "load a different workflow")

Focus on the user's actual intent, not just keywords."""

    chat_template = ChatPromptTemplate([ChatMessage.from_str(intent_prompt, "user")])

    try:
        result = await llm.astructured_predict(
            UserIntent, chat_template, user_input=user_input
        )
        return result.intent
    except Exception:
        # Fallback to simple keyword matching if LLM fails
        user_lower = user_input.lower()
        if any(
            word in user_lower
            for word in ["y", "yes", "approve", "good", "perfect", "ok"]
        ):
            return "approve"
        elif any(
            word in user_lower for word in ["cancel", "exit", "test", "load", "stop"]
        ):
            return "exit"
        else:
            return "continue"
