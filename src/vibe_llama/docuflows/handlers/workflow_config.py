from workflows import Context
from workflows.events import InputRequiredEvent
from typing import cast

from vibe_llama.docuflows.agent.utils import (
    AgentConfig,
)
from vibe_llama.docuflows.commons import (
    StreamEvent,
    validate_uuid,
)
from vibe_llama.docuflows.commons.typed_state import WorkflowState


async def handle_configuration(
    ctx: Context[WorkflowState], user_input: str
) -> InputRequiredEvent | None:
    """Handle configuration setup"""
    config = cast(AgentConfig, (await ctx.store.get_state()).config)

    if not config.project_id:
        if not validate_uuid(user_input):
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Invalid project ID format. Please provide a valid UUID.\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(delta="Example: 12345678-1234-1234-1234-123456789abc\n")  # type: ignore
            )
            return InputRequiredEvent(
                prefix="Please provide your LlamaCloud project ID: "  # type: ignore
            )

        config.project_id = user_input
        config.save_to_file()
        async with ctx.store.edit_state() as state:
            state.config = config
        return InputRequiredEvent(
            prefix="Great! Now please provide your organization ID: "  # type: ignore
        )

    if config.project_id and not config.organization_id:
        if not validate_uuid(user_input):
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Invalid organization ID format. Please provide a valid UUID.\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(delta="Example: 12345678-1234-1234-1234-123456789abc\n")  # type: ignore
            )
            return InputRequiredEvent(prefix="Please provide your organization ID: ")  # type: ignore

        config.organization_id = user_input
        config.save_to_file()
        async with ctx.store.edit_state() as state:
            state.config = config
            state.app_state = "ready"
        ctx.write_event_to_stream(StreamEvent(delta="✅ Configuration saved!\n"))  # type: ignore
        return InputRequiredEvent(
            prefix="Perfect! Now, what would you like to do?\n"  # type: ignore
            "(Examples: 'generate a workflow', 'edit workflow', 'help'): "
        )


async def handle_show_config(ctx: Context[WorkflowState]) -> InputRequiredEvent:
    """Show current configuration"""
    config = cast(AgentConfig, (await ctx.store.get_state()).config)
    config_text = f"""
Current Configuration:
- Project ID: {config.project_id}
- Organization ID: {config.organization_id}
- Default Reference Files: {config.default_reference_files_path or "Not set"}
- Output Directory: {config.output_directory}
    """
    ctx.write_event_to_stream(StreamEvent(delta=config_text))  # type: ignore
    # Set status message for chat history
    async with ctx.store.edit_state() as state:
        state.handler_status_message = "Displayed current configuration settings."

    return InputRequiredEvent(prefix="\nWhat would you like to do next? ")  # type: ignore


async def handle_reconfigure(ctx: Context[WorkflowState]) -> InputRequiredEvent:
    """Handle reconfiguration of credentials"""

    # Reset configuration state
    config = AgentConfig()
    async with ctx.store.edit_state() as state:
        state.config = config
        state.app_state = "configuring"

    ctx.write_event_to_stream(StreamEvent(delta="🔄 Reconfiguring credentials...\n"))  # type: ignore
    # Set status message for chat history
    async with ctx.store.edit_state() as state:
        state.handler_status_message = (
            "Reset configuration and started reconfiguration process."
        )

    return InputRequiredEvent(prefix="Please provide your LlamaCloud project ID: ")  # type: ignore
