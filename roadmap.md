Overview: multi-profile + layered summarization (Phase 1)

This prompt/plan file contains the TODO checklist and clarifying notes for delivering the multi-profile and layered summarization feature. Use this as the single source of truth while refining the roadmap and adding implementation details.

---

1) Objectives
- Build multi-profile summarization that returns a stack of summaries per profile
- Provide persona adapters to adapt language/tone/terminology for different audiences
- Add CLI entry (`summarize-multi`) and unit tests for programmatic and human usage
- Ensure budget compliance using `UI_UX.compute_budget`

---

2) Deliverables (Phase 1)
- Modules:
  - `vision_ui/profiles.py` — profiles management (default + user JSON profiles; parse + save helpers)
  - `vision_ui/summarize.py` — layered_summarize(), multi_profile_summarize(), persona adapters, formatting
  - `vision_ui/cli.py` — `summarize-multi` subcommand handling formats + persona + layers
- Tests:
  - `vision_ui/tests/test_profiles_ui.py` — validate default and JSON loading
  - `vision_ui/tests/test_summarize_ui.py` — layer behaviors, persona integration, char budgets
  - `vision_ui/tests/test_cli_summarize_multi_ui.py` — CLI integration tests
- Documentation:
  - `vision_ui/README.md` / `USAGE.md` with usage examples and persona guidance
- Packaging:
  - `pyproject.toml` updated with entry point `vision-ui` (done), and `packages` include `vision_ui`
- Examples:
  - Add `learning_data/` examples for long text, PRs, logs, README.md etc.

---

3) Implementation checklist — code & APIs
- profiles.py
  - dataclass `Profile(name, width_px, height_px, font_size_px=14, editor_ruler_columns=80, buffer=0.9)`
  - builtin `DEFAULT_PROFILES` with names: laptop, phone, slides, tweet
  - `load_profile(name_or_path)` supports builtin name + JSON file
  - `list_profiles()` returns builtin + user profiles
  - `parse_profiles_from_cli(string)` to return profiles for CLI
- summarize.py
  - LayerConfig dataclass: name, budget_multiplier, max_sentences, include_hash
  - DEFAULT_LAYERS: headline, one_screen, deep (10% / 80% / 100%)
  - `Persona` dataclass & BUILTIN_PERSONAS (developer, designer, manager, musician, scientist, chef, student)
    - `apply(text)`: transform vocabulary, prepend examples/context
    - NOTE: persona examples can dominate short summaries – sequence must consider budget offsets
  - `layered_summarize(text, char_budget, layers, persona=None, summarizer=None)`
  - `multi_profile_summarize(text, profiles, layers, persona)` uses compute_budget to get target_chars
  - `format_multi_profile_output(summaries, format_type='stacked')` — stacked/json/compact
- cli.py
  - Add `summarize-multi` subparser: `--profiles`, `--layers`, `--persona`, `--format`
  - Use `parse_profiles_from_cli` and `multi_profile_summarize()`; handle JSON/stacked output

---

4) Tests & edge cases
- Unit tests
  - Profile loading, missing/invalid JSON file errors
  - Budget constraints: `len(summary) <= target_chars` for `one_screen`
  - Layered summarization: headline is short & below headline budget
  - Persona injection: persona examples and context prefixes appear as expected
- CLI tests
  - CLI end-to-end with `--format json` and `compact` validation
- Input sanitation and errors
  - Missing profiles raise a user-friendly error with suggestions
  - Layers unknown -> explicit message
- Integration
  - Ensure `UI_UX.budget` relative import works to allow `vision_ui.cli` to import on repo root
- Manual review tests
  - Human review on sampled PR/issue/logs for quality judgment (A/B)

---

5) Security / Ethics / Privacy
- Save only local JSON profiles; avoid transmitting sensitive content to external APIs
- For images/screenshots (Phase 2+), add redaction & consent checks
- Persona content must be non-sensitive and optional; do not expose PII in persona examples

---

6) Phase 2 & Phase 3 expansion plan (short)
- Phase 2: screenshot-aware summarization
  - integrate OCR (pytesseract) and layout-aware image occupation slots
  - budget-aware image slotting and cropping helpers
- Phase 3: triage board & personas at scale
  - simple web UI for triage (Flask/Streamlit) with multi-profile stack cards
  - attention & saliency research (foveation, gaze alignment)

---

7) Tests, metrics, and CI
- Test scenarios
  - Short inputs (small summaries), long inputs (deep), and PR/issue examples
- Metrics
  - Budget fidelity: fraction of profiles where char_count <= target_chars
  - Human utility: average score across human reviewers (1–5 scale)
  - Persona alignment: does persona produce domain-specific terms (precision/recall heuristics)
- CI tasks
  - Run `pytest` including `vision_ui/tests` & `UI_UX` tests
  - Build wheel: `python -m build` for distribution sanity
  - Optionally: `pip install dist/*.whl` and run CLI smoke tests

---

8) Packaging & publishing
- Decide package layout: top-level vs `src/` layout; update `pyproject` accordingly
- Maintain `vision-ui` entrypoint
- Add `README` and usage examples before publishing
- Publish release process:
  - tag release, build package, upload to PyPI or GitHub Packages

---

9) Data artifacts & sample dataset
- Create `learning_data/` subfolder with:
  - `samples/pr_example.txt` - long PR body
  - `samples/incident_log.txt` - incident timeline
  - `samples/long_blog.md` - long blog post
  - `screenshots/` (Phase 2) - sample dashboard screenshots and annotations

---

10) Acceptance criteria & DONE checklist
- [ ] `vision_ui` package has `profiles.py`, `summarize.py`, `cli.py` with working `summarize-multi`
- [ ] Unit tests exist & pass (set `PYTHONPATH` for local runs) and example CLI tested
- [ ] Documentation `vision_ui/README.md` with example commands and persona guidance
- [ ] Profiling & metrics: simple gauge for `budget fidelity` and CLI output shape
- [ ] Security/privacy checklist (safeguards for images, persona only local & opt-in)

---

What I need from you (actionable items)
- Confirm the target canonical profiles and adjust defaults (phone/laptop/slides/tweet) if needed
- Decide whether to use top-level packages vs `src/` layout for publishing
- Provide sample texts (PRs / issues / logs / blog posts) to enrich `learning_data/`
- Decide release and distribution preferences (upload to PyPI? GitHub Packages?)

---

Timeline estimate
- Phase 1: 2–3 weeks to complete with tests and docs
- Phase 2: + 2–4 weeks with OCR & image-aware budgets & additional tests
- Phase 3: + 4–8 weeks for triage board UI, persona enrichment, and attention research

---

Notes & open questions
- Persona budget interaction: Should we subtract persona example length from headline budget, or include persona info after the headline? (To avoid examples dominating short headlined outputs)
- What are the high-priority persona categories you'd like included initially? (developer/designer/manager seem relevant; others can follow)
- How will language & tone mapping be evaluated? Should it be manual or automated with sample checks?w


---

Use this file as the starting point for the project's Phase 1 delivery. Rename or copy to your repo `README` or `ROADMAP.md` as needed.
