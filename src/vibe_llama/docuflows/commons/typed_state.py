from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


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

    pending_workflow: Optional[str] = Field(
        default_factory=str, description="Pending workflow"
    )
    pending_runbook: Optional[str] = Field(
        default_factory=str, description="Pending runbook"
    )
    pending_task: Optional[str] = Field(default_factory=str, description="Pending task")

    # Runbook management
    current_runbook: Optional[str] = Field(None, description="Current runbook content")
    current_runbook_path: Optional[str] = Field(
        None, description="Path to current runbook file"
    )
    current_folder_path: str = Field(
        default_factory=str, description="Current folder path"
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

    generation_task: str = Field(default_factory=str, description="Generation task")

    generation_reference_path: str = Field(
        default_factory=str, description="Reference path for generation"
    )

    workflow_analysis_cache: Optional[Dict[str, Any]] = Field(
        default=None, description="Workflow analysis cache"
    )
    workflow_analysis_cache_path: Optional[str] = Field(
        default=None, description="Path for workflow analysis cache"
    )

    class Config:
        # Allow arbitrary types for flexibility with different object types
        arbitrary_types_allowed = True
        # Use enum values for serialization
        use_enum_values = True
