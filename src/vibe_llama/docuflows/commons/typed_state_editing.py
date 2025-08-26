from pydantic import BaseModel, Field
from typing import Optional, List, Any


class EditSessionState(BaseModel):
    # Current working code/workflow
    current_code: Optional[str] = Field(
        None, description="Current code/workflow being edited"
    )

    # Original request and task information
    original_request: Optional[str] = Field(
        None, description="Original edit request from user"
    )
    original_task: Optional[str] = Field(None, description="Original task description")

    # Context information
    context_str: Optional[str] = Field(
        None, description="Context string for the edit session"
    )
    recent_context: Optional[Any] = Field(
        None, description="Recent context information"
    )

    # Reference and path information
    reference_path: Optional[str] = Field(
        None, description="Path to reference files or resources"
    )

    # Edit session configuration
    max_iterations: Optional[int] = Field(
        None, description="Maximum number of edit iterations allowed"
    )

    # Edit session tracking
    edit_history: List[Any] = Field(
        default_factory=list, description="History of edits made during session"
    )
    iteration: int = Field(
        1, description="Current iteration number in the edit session"
    )

    class Config:
        # Allow arbitrary types for flexibility with different object types
        arbitrary_types_allowed = True
        # Use enum values for serialization
        use_enum_values = True
