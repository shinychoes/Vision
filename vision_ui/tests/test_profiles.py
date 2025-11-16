from vision_ui.profiles import list_profiles, load_profile, parse_profiles_from_cli


def test_list_profiles_contains_defaults():
    names = list_profiles()
    # Basic expectations
    assert "laptop" in names
    assert "phone" in names
    assert "slides" in names


def test_load_profile_by_name():
    p = load_profile("phone")
    assert p.name == "phone"
    assert p.width_px > 0


def test_parse_profiles_from_cli_mixed():
    profiles = parse_profiles_from_cli("phone,laptop")
    assert len(profiles) == 2
    assert profiles[0].name == "phone"
    assert profiles[1].name == "laptop"
