import re
from pathlib import Path

from script_helpers import ScriptedChat, make

from dcs_orchestrator.interface import ScriptOrchestrator

SRC = Path(__file__).resolve().parents[1] / "src" / "dcs_orchestrator"


def test_only_the_langgraph_adapter_imports_langgraph():
    pattern = re.compile(r"^\s*(from|import)\s+langgraph", re.M)
    offenders = [
        p.relative_to(SRC).as_posix()
        for p in SRC.rglob("*.py")
        if pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == ["adapters/langgraph_script.py"]


def test_adapter_satisfies_protocol():
    assert isinstance(make(ScriptedChat([]), ScriptedChat([])), ScriptOrchestrator)
