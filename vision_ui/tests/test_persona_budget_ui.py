from vision_ui.summarize import layered_summarize, DEFAULT_LAYERS, Persona


def test_headline_omits_persona_examples_when_prepend():
    text = "This is a long explanatory text. " * 10
    char_budget = 200
    persona = Persona(
        name="tester",
        example_sentences=["Important note: keep this short."],
        context_prefix="As a persona:",
        examples_location="prepend",
    )

    out = layered_summarize(text, char_budget=char_budget, layers=["headline", "one_screen"], persona=persona)
    headline = out["headline"]
    one_screen = out["one_screen"]

    # Persona examples should NOT be present in the headline (we only apply vocabulary mapping there)
    assert "Example:" not in headline
    # Persona examples should appear in one_screen
    assert "Example:" in one_screen

    # Headline should be at most the budget for the headline layer
    expected_headline_budget = int(char_budget * DEFAULT_LAYERS["headline"].budget_multiplier)
    assert len(headline) <= expected_headline_budget


def test_persona_examples_appended_in_one_screen_when_append():
    text = "Detailed discussion on the implementation. " * 6
    char_budget = 120
    persona = Persona(
        name="tester2",
        example_sentences=["Try keeping the design simple."],
        examples_location="append",
    )

    out = layered_summarize(text, char_budget=char_budget, layers=["headline", "one_screen"], persona=persona)
    assert "Example:" not in out["headline"]
    assert "Example:" in out["one_screen"]
