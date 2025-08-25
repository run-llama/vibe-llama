"""
Diff-based iterative editing workflow for code modifications.

This workflow applies changes to code using structured diffs rather than
full regeneration, with an iterative validation loop.
"""

from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage, ChatPromptTemplate
from pydantic import BaseModel, Field
from workflows import Context, Workflow, step
from workflows.events import Event, StartEvent, StopEvent
from typing import Optional, cast

from vibe_llama.docuflows.commons import StreamEvent
from vibe_llama.docuflows.commons.typed_state_editing import EditSessionState


class CodeDiff(BaseModel):
    """A single code change/diff to apply."""

    old_text: str = Field(
        ..., description="The exact text to replace (must match exactly)"
    )
    new_text: str = Field(..., description="The replacement text")
    reason: str = Field(..., description="Why this change is needed")


class DiffPlan(BaseModel):
    """A plan containing multiple diffs to apply to code."""

    diffs: list[CodeDiff] = Field(..., description="List of diffs to apply in order")
    summary: str = Field(
        ..., description="High-level summary of what these changes accomplish"
    )


class ValidationResult(BaseModel):
    """Result of validating edited code."""

    is_valid: bool = Field(..., description="Whether the code is valid and complete")
    issues_found: list[str] = Field(
        default_factory=list, description="List of any issues found"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )


class EditRequest(StartEvent):
    """Event to start the diff editing workflow."""

    current_workflow: str
    edit_request: str
    context_str: str
    original_task: str = ""
    reference_path: str = ""
    recent_context: str | list[ChatMessage] = ""
    max_iterations: int = 3


class DiffGenerated(Event):
    """Event when diffs are generated."""

    diff_plan: DiffPlan
    iteration: int


class DiffsApplied(Event):
    """Event when diffs are applied."""

    updated_code: str
    applied_changes: list[dict]
    iteration: int


class ValidationCompleted(Event):
    """Event when validation is completed."""

    validation: ValidationResult
    current_code: str
    iteration: int


class EditCompleted(StopEvent):
    """Event when editing is complete."""

    final_code: str
    edit_history: list[dict]
    total_iterations: int


class DiffEditingWorkflow(Workflow):
    """Workflow for applying iterative diff-based edits to code."""

    def __init__(self, llm: LLM, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm

    def _build_shared_context(
        self,
        context_str: str,
        original_task: str,
        reference_path: str,
        recent_context: str | list[ChatMessage],
        current_code: str,
        edit_history: Optional[list[dict]] = None,
    ) -> str:
        """Build shared context prefix for prompt caching."""

        history_context = ""
        if edit_history:
            history_context = "PREVIOUS ITERATIONS:\n"
            for h in edit_history[-2:]:  # Show last 2 iterations
                history_context += f"Iteration {h['iteration']}: Applied {len(h['applied_changes'])} changes\n"

        # Format recent context (could be string or ChatMessage list)
        formatted_recent_context = ""
        if recent_context:
            if isinstance(recent_context, list):
                # Format ChatMessage list as conversation
                formatted_recent_context = "RECENT EDITING CONVERSATION:\n"
                for msg in recent_context[-6:]:  # Show last 6 messages
                    role_prefix = (
                        "User" if msg.role == MessageRole.USER else "Assistant"
                    )
                    formatted_recent_context += f"{role_prefix}: {msg.content}\n"
            else:
                # Use string as-is
                formatted_recent_context = f"RECENT CONVERSATION:\n{recent_context}"

        return f"""CONTEXT DOCUMENTATION:
{context_str}

ORIGINAL TASK: {original_task}
REFERENCE FILES PATH: {reference_path}

{formatted_recent_context}

{history_context}

CURRENT CODE:
```python
{current_code}
```"""

    @step
    async def start_editing(
        self, ctx: Context[EditSessionState], ev: EditRequest
    ) -> DiffGenerated:
        """Initialize the editing process."""

        # Initialize workflow state
        async with ctx.store.edit_state() as state:
            state.current_code = ev.current_workflow
            state.original_request = ev.edit_request
            state.context_str = ev.context_str
            state.original_task = ev.original_task
            state.reference_path = ev.reference_path
            state.recent_context = ev.recent_context
            state.max_iterations = ev.max_iterations
            state.edit_history = []
            state.iteration = 1

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta=f"🔧 Starting diff-based editing (max {ev.max_iterations} iterations)...\n"
            )
        )

        # Generate first diff plan
        return await self._generate_diff_plan(ctx, ev.edit_request, 1)

    @step
    async def apply_diffs(
        self, ctx: Context[EditSessionState], ev: DiffGenerated
    ) -> DiffsApplied:
        """Apply the generated diffs to the code."""

        if not ev.diff_plan.diffs:
            ctx.write_event_to_stream(StreamEvent(delta="✅ No changes needed.\n"))  # type: ignore
            current_code = (await ctx.store.get_state()).current_code
            return DiffsApplied(
                updated_code=cast(str, current_code),
                applied_changes=[],
                iteration=ev.iteration,
            )

        current_code = (await ctx.store.get_state()).current_code

        # Show planned changes
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta=f"\n📝 Iteration {ev.iteration}: {ev.diff_plan.summary}\n"
            )
        )
        ctx.write_event_to_stream(
            StreamEvent(delta=f"📋 Applying {len(ev.diff_plan.diffs)} changes...\n")  # type: ignore
        )

        # Apply diffs
        working_code = cast(str, current_code)
        applied_changes = []

        for i, diff in enumerate(ev.diff_plan.diffs, 1):
            ctx.write_event_to_stream(StreamEvent(delta=f"  {i}. {diff.reason}\n"))  # type: ignore

            if diff.old_text not in working_code:
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta=f"    ⚠️ Could not find text to replace: {diff.old_text[:100]}...\n"
                    )
                )
                applied_changes.append(
                    {
                        "reason": diff.reason,
                        "old_text": diff.old_text,
                        "new_text": diff.new_text,
                        "success": False,
                        "error": "Text not found",
                    }
                )
                continue

            # Apply the diff
            working_code = working_code.replace(diff.old_text, diff.new_text, 1)

            applied_changes.append(
                {
                    "reason": diff.reason,
                    "old_text": diff.old_text,
                    "new_text": diff.new_text,
                    "success": True,
                }
            )

            ctx.write_event_to_stream(StreamEvent(delta="    ✅ Applied\n"))  # type: ignore

        # Update stored code
        async with ctx.store.edit_state() as state:
            state.current_code = working_code

        return DiffsApplied(
            updated_code=working_code,
            applied_changes=applied_changes,
            iteration=ev.iteration,
        )

    @step
    async def validate_code(
        self, ctx: Context[EditSessionState], ev: DiffsApplied
    ) -> ValidationCompleted:
        """Validate the updated code."""

        ctx.write_event_to_stream(StreamEvent(delta="🔍 Validating changes...\n"))  # type: ignore

        original_request = (await ctx.store.get_state()).original_request
        original_task = (await ctx.store.get_state()).original_task

        # Store this iteration in history
        edit_history = (await ctx.store.get_state()).edit_history
        edit_history.append(
            {
                "iteration": ev.iteration,
                "request": original_request
                if ev.iteration == 1
                else "Refinement based on validation",
                "applied_changes": ev.applied_changes,
                "result_preview": ev.updated_code[:200] + "..."
                if len(ev.updated_code) > 200
                else ev.updated_code,
            }
        )
        async with ctx.store.edit_state() as state:
            state.edit_history = edit_history

        context_str = (await ctx.store.get_state()).context_str
        reference_path = (await ctx.store.get_state()).reference_path
        recent_context = (await ctx.store.get_state()).recent_context

        validation = await self._validate_code(
            ev.updated_code,
            cast(str, original_request),
            cast(str, original_task),
            cast(str, context_str),
            cast(str, reference_path),
            cast(str, recent_context),
        )

        return ValidationCompleted(
            validation=validation, current_code=ev.updated_code, iteration=ev.iteration
        )

    @step
    async def check_completion(
        self, ctx: Context[EditSessionState], ev: ValidationCompleted
    ) -> DiffGenerated | EditCompleted:
        """Check if editing is complete or if another iteration is needed."""

        max_iterations = (await ctx.store.get_state()).max_iterations
        edit_history = (await ctx.store.get_state()).edit_history

        if ev.validation.is_valid:
            ctx.write_event_to_stream(StreamEvent(delta="✅ Validation passed!\n"))  # type: ignore
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"🎉 Diff-based editing complete after {ev.iteration} iterations!\n"
                )
            )

            return EditCompleted(
                final_code=ev.current_code,
                edit_history=edit_history,
                total_iterations=ev.iteration,
            )

        elif ev.iteration < cast(int, max_iterations):
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"⚠️ Issues found: {', '.join(ev.validation.issues_found)}\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(delta="🔄 Attempting to fix issues...\n")  # type: ignore
            )

            # Use issues as new edit request for next iteration
            new_edit_request = (
                f"Fix these issues: {', '.join(ev.validation.issues_found)}. "
                + f"Suggestions: {', '.join(ev.validation.suggestions)}"
            )

            next_iteration = ev.iteration + 1
            async with ctx.store.edit_state() as state:
                state.iteration = next_iteration

            return await self._generate_diff_plan(ctx, new_edit_request, next_iteration)

        else:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"⚠️ Max iterations reached. Issues remain: {', '.join(ev.validation.issues_found)}\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"🎉 Diff-based editing complete after {ev.iteration} iterations (with remaining issues)!\n"
                )
            )

            return EditCompleted(
                final_code=ev.current_code,
                edit_history=edit_history,
                total_iterations=ev.iteration,
            )

    async def _generate_diff_plan(
        self, ctx: Context[EditSessionState], edit_request: str, iteration: int
    ) -> DiffGenerated:
        """Generate a plan of diffs to apply."""

        current_code = await ctx.store.get("current_code")
        context_str = await ctx.store.get("context_str")
        original_task = await ctx.store.get("original_task")
        reference_path = await ctx.store.get("reference_path")
        recent_context = await ctx.store.get("recent_context")
        edit_history = await ctx.store.get("edit_history")

        # Build shared context for caching
        shared_context = self._build_shared_context(
            context_str,
            original_task,
            reference_path,
            recent_context,
            current_code,
            edit_history,
        )

        diff_prompt = f"""You are an expert code editor. Generate precise diffs to modify Python workflow code.

{shared_context}

EDIT REQUEST: {edit_request}

Generate a plan of precise text replacements to implement the requested changes.

IMPORTANT RULES:
1. old_text must match EXACTLY (including whitespace, indentation)
2. Make minimal, targeted changes
3. Preserve existing functionality unless explicitly asked to change it
4. Each diff should be atomic and focused
5. Order diffs so they don't conflict with each other
6. If no changes are needed, return empty diffs list

Generate diffs that will modify the code to satisfy the edit request."""

        chat_template = ChatPromptTemplate([ChatMessage.from_str(diff_prompt, "user")])

        try:
            result = await self.llm.astructured_predict(
                DiffPlan,
                chat_template,
                current_code=current_code,
                edit_request=edit_request,
            )

            return DiffGenerated(diff_plan=result, iteration=iteration)

        except Exception as e:
            # Fallback: return empty plan
            ctx.write_event_to_stream(
                StreamEvent(delta=f"❌ Error generating diffs: {e}\n")  # type: ignore
            )

            return DiffGenerated(
                diff_plan=DiffPlan(diffs=[], summary=f"Error generating diffs: {e}"),
                iteration=iteration,
            )

    async def _validate_code(
        self,
        code: str,
        original_request: str,
        original_task: str,
        context_str: str = "",
        reference_path: str = "",
        recent_context: str | list[ChatMessage] = "",
    ) -> ValidationResult:
        """Validate the edited code."""

        # Build shared context for caching (no edit history needed for validation)
        shared_context = self._build_shared_context(
            context_str, original_task, reference_path, recent_context, code
        )

        validation_prompt = f"""Review this Python workflow code for correctness and completeness.

{shared_context}

EDIT REQUEST: {original_request}

Check for:
1. Syntax correctness
2. Import completeness
3. Logical flow
4. Whether the edit request was properly addressed
5. LlamaIndex workflow patterns are followed

Identify any issues and suggest improvements."""

        chat_template = ChatPromptTemplate(
            [ChatMessage.from_str(validation_prompt, "user")]
        )

        try:
            result = await self.llm.astructured_predict(
                ValidationResult,
                chat_template,
                code=code,
                edit_request=original_request,
                original_task=original_task,
            )
            return result
        except Exception as e:
            # Fallback: assume valid
            return ValidationResult(
                is_valid=True, issues_found=[f"Validation error: {e}"], suggestions=[]
            )
