from types import SimpleNamespace

from teof.commands import foreman


def test_choose_action_matches_keywords():
    assert foreman._choose_action("run the alignment scan for me", foreman._ACTIONS).name == "scan"
    assert foreman._choose_action("show me the status snapshot", foreman._ACTIONS).name == "status"
    assert foreman._choose_action("list the tasks please", foreman._ACTIONS).name == "tasks"
    assert foreman._choose_action("rebuild the brief artifacts", foreman._ACTIONS).name == "brief"
    assert foreman._choose_action("run my daily routine", foreman._ACTIONS).name == "daily"


def test_choose_action_handles_unknown_request():
    assert foreman._choose_action("schedule a meeting", foreman._ACTIONS) is None


def test_spoken_from_args_prefers_flag_value():
    args = SimpleNamespace(say="  run scan ", phrase=["ignored"])
    assert foreman._spoken_from_args(args) == "run scan"


def test_spoken_from_args_joins_positional_phrase():
    args = SimpleNamespace(say=None, phrase=["run", "the", "alignment", "scan"])
    assert foreman._spoken_from_args(args) == "run the alignment scan"
