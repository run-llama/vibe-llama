import json
from llama_index.core.tools import BaseTool, FunctionTool


def create_agent_tools() -> list[BaseTool]:
    """Create tools that the agent can use"""

    def generate_workflow_tool(task: str, reference_files_path: str) -> str:
        """Generate a workflow based on a task description and reference files directory"""
        return json.dumps(
            {
                "action": "generate_workflow",
                "task": task,
                "reference_files_path": reference_files_path,
            }
        )

    def edit_workflow_tool(edit_request: str) -> str:
        """Edit the current workflow based on user request"""
        return json.dumps({"action": "edit_workflow", "edit_request": edit_request})

    def test_workflow_tool(test_file_path: str = "") -> str:
        """Test the current workflow on sample data. Only provide test_file_path if user specified a specific file path."""
        return json.dumps({"action": "test_workflow", "test_file_path": test_file_path})

    def answer_question_tool(question: str) -> str:
        """Answer questions about the current workflow"""
        return json.dumps({"action": "answer_question", "question": question})

    def show_config_tool() -> str:
        """Show current configuration"""
        return json.dumps({"action": "show_config"})

    def reconfigure_tool() -> str:
        """Reconfigure credentials (project_id and organization_id)"""
        return json.dumps({"action": "reconfigure"})

    def load_workflow_tool(workflow_path: str) -> str:
        """Load an existing workflow from a file"""
        return json.dumps({"action": "load_workflow", "workflow_path": workflow_path})

    return [
        FunctionTool.from_defaults(
            fn=generate_workflow_tool,
            name="generate_workflow",
            description="Generate a NEW workflow from scratch based on task description and reference files directory path. ONLY use when user wants to CREATE a new workflow. DO NOT use for testing existing workflows - use test_workflow instead.",
        ),
        FunctionTool.from_defaults(
            fn=edit_workflow_tool,
            name="edit_workflow",
            description="Edit the current workflow based on user feedback or requirements",
        ),
        FunctionTool.from_defaults(
            fn=test_workflow_tool,
            name="test_workflow",
            description="Test the current/existing workflow on sample data or a specific file. ALWAYS use this tool for ANY testing request including: 'test', 'test it', 'test on sample data', 'run it on a file', 'try it out', or similar. DO NOT use generate_workflow for testing.",
        ),
        FunctionTool.from_defaults(
            fn=answer_question_tool,
            name="answer_question",
            description="Answer questions about the current workflow's functionality or structure",
        ),
        FunctionTool.from_defaults(
            fn=show_config_tool,
            name="show_config",
            description="Show the current configuration settings",
        ),
        FunctionTool.from_defaults(
            fn=reconfigure_tool,
            name="reconfigure",
            description="Reconfigure credentials (useful when project_id or organization_id are invalid)",
        ),
        FunctionTool.from_defaults(
            fn=load_workflow_tool,
            name="load_workflow",
            description="Load an existing workflow from a Python file. ONLY use when user explicitly wants to 'load', 'open', or 'switch to' a different workflow file. Do NOT use if user wants to work with the current workflow.",
        ),
    ]
