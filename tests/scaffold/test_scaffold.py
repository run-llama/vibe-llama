import pathlib
import shutil

from src.vibe_llama.scaffold import SCAFFOLD_DICT, create_scaffold


def test_scaffold_defaults() -> None:
    if pathlib.Path(".vibe-llama/scaffold/base_example").exists():
        shutil.rmtree(".vibe-llama/scaffold/base_example")
    ret = create_scaffold()
    assert ret.startswith("[bold green]")
    assert pathlib.Path(".vibe-llama/scaffold/base_example").is_dir()
    assert pathlib.Path(".vibe-llama/scaffold/base_example/workflow.py").is_file()
    assert pathlib.Path(".vibe-llama/scaffold/base_example/requirements.txt").is_file()
    with open(".vibe-llama/scaffold/base_example/workflow.py", "r") as f:
        code = f.read()
    with open(".vibe-llama/scaffold/base_example/requirements.txt") as f:
        reqs = f.read()
    assert code == SCAFFOLD_DICT["base_example"]["code"]
    assert reqs == SCAFFOLD_DICT["base_example"]["requirements"]


def test_scaffold_custom() -> None:
    if pathlib.Path("data/test/example/").exists():
        shutil.rmtree("data/test/example/")
    ret = create_scaffold(request="invoice_extractor", path="data/test/example/")
    assert ret.startswith("[bold green]")
    assert pathlib.Path("data/test/example/").is_dir()
    assert pathlib.Path("data/test/example/workflow.py").is_file()
    assert pathlib.Path("data/test/example/requirements.txt").is_file()
    with open("data/test/example/workflow.py", "r") as f:
        code = f.read()
    with open("data/test/example/requirements.txt") as f:
        reqs = f.read()
    assert code == SCAFFOLD_DICT["invoice_extractor"]["code"]
    assert reqs == SCAFFOLD_DICT["invoice_extractor"]["requirements"]
