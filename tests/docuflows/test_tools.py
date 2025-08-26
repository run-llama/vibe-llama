from llama_index.core.tools import FunctionTool

from src.vibe_llama.docuflows.tools import create_agent_tools


def test_create_agent_tools() -> None:
    tools = create_agent_tools()
    assert isinstance(tools, list)
    assert all(isinstance(tool, FunctionTool) for tool in tools)  # type: ignore
    assert [
        "generate_workflow",
        "edit_workflow",
        "test_workflow",
        "answer_question",
        "show_config",
        "reconfigure",
        "load_workflow",
    ] == [tool.metadata.get_name() for tool in tools]
