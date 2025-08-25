from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage
from workflows import Context
from workflows.events import InputRequiredEvent

from vibe_llama.docuflows.commons import (
    StreamEvent,
)
from vibe_llama.docuflows.commons.typed_state import WorkflowState


async def handle_help(ctx: Context[WorkflowState]) -> InputRequiredEvent:
    """Show help information"""
    help_text = """
🤖 AI Agent CLI Help:

Available actions:
- **Generate workflow**: Create a new workflow from a task description
  Example: "Generate a workflow for extracting income statements from 10-K reports"

- **Load workflow**: Load an existing workflow from a file
  Example: "Load my previous workflow", "Open generated_workflow_maritime.py"

- **Edit workflow**: Modify the current workflow
  Example: "Edit the workflow to handle quarterly reports better"

- **Test workflow**: Test current workflow on sample data
  Example: "Test the workflow on my sample PDF file"

- **Ask questions**: Ask about the current workflow
  Example: "How does this workflow handle table extraction?"

- **Show config**: Display current configuration
- **Reconfigure**: Reset and reconfigure credentials (useful for fixing invalid project/org IDs)
- **Help**: Show this help message
- **Quit/exit**: Exit the CLI

For workflow generation, I'll need:
1. A clear description of what you want the workflow to do
2. Path to directory containing reference files
    """
    ctx.write_event_to_stream(StreamEvent(delta=help_text))  # type: ignore
    return InputRequiredEvent(prefix="\nWhat would you like to do? ")  # type: ignore


async def handle_answer_question(
    ctx: Context[WorkflowState], question: str, llm: LLM
) -> InputRequiredEvent:
    """Answer questions about the current workflow with full context"""
    current_workflow = (await ctx.store.get_state()).current_workflow

    if not current_workflow:
        ctx.write_event_to_stream(
            StreamEvent(delta="❌ No workflow loaded to ask questions about.\n")  # type: ignore
        )
        return InputRequiredEvent(prefix="What would you like to do? ")  # type: ignore

    if not question:
        return InputRequiredEvent(
            prefix="What would you like to know about the workflow? "  # type: ignore
        )

    try:
        # Use full workflow context (no truncation)
        qa_messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="You are an expert at explaining LlamaIndex workflow code. Answer the user's question about the workflow clearly and helpfully.",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"""Based on this workflow code, please answer the user's question:

Workflow Code:
```python
{current_workflow}
```

User Question: {question}

Please provide a helpful and detailed answer about the workflow, referencing specific parts of the code when relevant.""",
            ),
        ]

        ctx.write_event_to_stream(StreamEvent(delta=f"🤔 {question}\n\n🤖 "))  # type: ignore

        qa_response = await llm.astream_chat(qa_messages)
        async for r in qa_response:
            if r.delta:
                ctx.write_event_to_stream(StreamEvent(delta=r.delta))  # type: ignore

        # Set status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = (
                f"Answered question about the workflow: '{question}'"
            )

        return InputRequiredEvent(
            prefix="\n\nAny other questions? Or what would you like to do next? "  # type: ignore
        )

    except Exception as e:
        ctx.write_event_to_stream(
            StreamEvent(delta=f"❌ Error answering question: {str(e)}\n")  # type: ignore
        )
        # Set error status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = (
                f"Failed to answer question due to error: {str(e)}"
            )

        return InputRequiredEvent(
            prefix="Please try asking again. What would you like to do? "  # type: ignore
        )
