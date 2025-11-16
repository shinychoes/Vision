from vision_ui.summarize import multi_profile_summarize, layered_summarize
from vision_ui.profiles import parse_profiles_from_cli


def test_layered_summarize_basic():
    text = "This is a test. We have several sentences. This is the final sentence."
    summary = layered_summarize(text, char_budget=200, layers=["headline", "one_screen"], persona=None)
    assert "headline" in summary
    assert "one_screen" in summary
    assert len(summary["headline"]) <= 200


def test_multi_profile_returns_expected_structure():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 8
    profiles = parse_profiles_from_cli("phone,laptop")
    summaries = multi_profile_summarize(text=text, profiles=profiles, layers=["headline","one_screen"], persona="developer")
    assert set(summaries.keys()) == {"phone", "laptop"}
    for p in summaries.values():
        assert "headline" in p
        assert len(p["one_screen"]) <= 10000
