from __future__ import annotations

import sys
from pathlib import Path
import os

from langchain_core.messages import AIMessage
from langgraph.types import Command

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("GROQ_API_KEY", "dummy-key-for-smoke-tests")

import agent_runtime


def fake_message(content: str, tool_calls: list[dict]) -> AIMessage:
    return AIMessage(content=content, tool_calls=tool_calls)


def main() -> None:
    original_call_model = agent_runtime._call_model
    try:
        # 1) Recommendation tool parsing
        recommendation_queue = [
            fake_message(
                "I recommend a complete office outfit.",
                [
                    {
                        "name": "show_recommendations",
                        "args": {
                            "product_ids": ["silver-slate", "printed-tie-combo", "mens-belt"],
                            "title": "Office outfit bundle",
                            "reason": "A clean, complete office combination.",
                            "cross_sells": ["white shirt"],
                        },
                        "id": "tool-rec-1",
                    }
                ],
            )
        ]

        def recommendation_stub(*_args, **_kwargs):
            return recommendation_queue.pop(0)

        agent_runtime._call_model = recommendation_stub
        graph = agent_runtime.build_agent_graph()
        config = {"configurable": {"thread_id": "manual-smoke-1"}}
        result = graph.invoke({"session_id": "manual-smoke-1", "messages": [{"role": "user", "content": "Show me an office outfit"}]}, config)
        assert any(action["type"] == "show_recommendations" for action in result["actions"]), result

        # 2) Validation fallback on repeated question
        validation_state = {
            "messages": [{"role": "user", "content": "I need a wedding suit"}],
            "response": "What is the occasion?",
            "actions": [{"type": "present_options", "title": "Choose occasion", "options": ["Wedding", "Office"]}],
            "retry_count": 0,
        }
        validation_result = agent_runtime._validate_output(validation_state)
        assert validation_result["validation_failed"] is True, validation_result

        # 3) Confirmation interrupt and resume
        confirmation_queue = [
            fake_message(
                "I can add this to your bag.",
                [{"name": "add_to_bag", "args": {}, "id": "tool-add-1"}],
            )
        ]

        def confirmation_stub(*_args, **_kwargs):
            return confirmation_queue.pop(0)

        agent_runtime._call_model = confirmation_stub
        graph = agent_runtime.build_agent_graph()
        config = {"configurable": {"thread_id": "manual-smoke-2"}}
        interrupted = graph.invoke({"session_id": "manual-smoke-2", "messages": [{"role": "user", "content": "Add it to my bag"}]}, config)
        assert "__interrupt__" in interrupted, interrupted

        resumed = graph.invoke(Command(resume="confirm"), config)
        assert any(action["type"] == "add_to_bag" for action in resumed["actions"]), resumed

        # 4) Checkpointer persistence across a fresh graph instance
        fresh_graph = agent_runtime.build_agent_graph()
        snapshot = fresh_graph.get_state(config)
        assert snapshot.interrupts == (), snapshot

        print("manual_upgrade_smoke: ok")
    finally:
        agent_runtime._call_model = original_call_model


if __name__ == "__main__":
    main()
