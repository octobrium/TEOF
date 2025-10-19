from tools.autonomy import scan_trigger


def test_should_trigger_when_watched_prefix_matches():
    changed = ["_plans/new-plan.plan.json", "README.md"]
    assert scan_trigger._should_trigger(changed, ("_plans/", "_report/")) is True


def test_should_not_trigger_when_no_prefix_matches():
    changed = ["docs/notes.md", "scripts/run.sh"]
    assert scan_trigger._should_trigger(changed, ("_plans/", "_report/")) is False
