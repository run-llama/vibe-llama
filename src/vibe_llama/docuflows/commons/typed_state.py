from pydantic import BaseModel, Field
from typing import Optional, List, Any


class WorkflowState(BaseModel):
    """
    Pydantic model representing all the state properties stored in ctx.store
    """

    # Configuration and basic state
    config: Optional[Any] = Field(None, description="Application configuration object")
    app_state: str = Field("initializing", description="Current application state")
    current_model: Optional[str] = Field(None, description="Currently selected model")

    # Chat and conversation history
    chat_history: List[Any] = Field(
        default_factory=list, description="Chat conversation history"
    )
    edit_conversation_history: List[Any] = Field(
        default_factory=list, description="Edit conversation history"
    )

    # Workflow management
    current_workflow: Optional[Any] = Field(None, description="Current active workflow")
    current_workflow_path: Optional[str] = Field(
        None, description="Path to current workflow file"
    )
    pending_workflow_edit: Optional[Any] = Field(
        None, description="Workflow being edited"
    )

    # Runbook management
    current_runbook: Optional[str] = Field(None, description="Current runbook content")
    current_runbook_path: Optional[str] = Field(
        None, description="Path to current runbook file"
    )
    pending_runbook_edit: Optional[Any] = Field(
        None, description="Runbook being edited"
    )

    # Edit session management
    edit_session_history: Optional[Any] = Field(
        None, description="History of edit sessions"
    )

    # Status and messaging
    handler_status_message: Optional[str] = Field(
        None, description="Current handler status message"
    )

    class Config:
        # Allow arbitrary types for flexibility with different object types
        arbitrary_types_allowed = True
        # Use enum values for serialization
        use_enum_values = True
