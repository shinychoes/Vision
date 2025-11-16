# Vision / UI-UX — one-screen budget (Python)

This folder contains a Python-native implementation of the "one-screen" screen-ratio configuration and visual reference discovered during the chat log you provided.
It includes code and tooling for calculating a response budget for a standard "one-screen" reply and a small CLI demo to visualize the usage.

What this folder includes:
- `screen_ratio_schema.json` — JSON example describing a screen profile and the computed one-screen budget
- `budget.py` — Core functions to compute budgets, show progress bars, and naive summarization
- `token_utils.py` — Optional helpers for token-aware budgets and token/character estimates
- `demo_cli.py` — Terminal demo to compute budgets and print a one-screen formatted summary for sample screen sizes; no JavaScript required
- `test_budget.py` — pytest unit tests for the `compute_budget` and `naive_summarize` utilities
- `test_token_utils.py` — pytest unit tests for the token utilities
- `requirements.txt` — Development and test dependencies for this module

How to run the demo (Python only):

1. Create a virtual environment (recommended):

```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
```

2. Install dev/test dependencies (optional if you want to run tests):

```powershell
pip install -r requirements.txt
```

3. Run the demo (prints budgets for common device sizes and shows one-screen summaries):

```powershell
python demo_cli.py
```

4. Run the tests (uses pytest):

```powershell
pytest -q
```

Notes:
- The implementation is intentionally pure Python and does not require JavaScript.
- The Python-based demo writes a static `report.html` with prefilled values (no client-side JS). If you want to run a live server or add interactive components we can add Flask/streamlit later.

---

What we created (overview)
---------------------------
- `budget.py`: calculates the amount of text that can fit on a single screen given width/height, font metrics, and an editor ruler setting; provides `compute_budget`, `progress_bar`, and `naive_summarize`.
- `demo_cli.py`: a small, reproducible command-line demo that prints budgets for sample devices and outputs a static `report.html` with a textual progress bar and the one-screen summary.
- `screen_ratio_schema.json`: an example JSON schema that shows how to persist a one-screen budget profile for a device.
- `test_budget.py`: unit tests (pytest) to validate behavior and edge cases.

Motivation — why this module exists
----------------------------------
This project documents and implements a small, measurable policy for the output length of AI responses in a code editor / chat UI. The core idea from the chat log is: "Limit the AI's reply so it fits on a single screen (one-screen mode)." That constraint:

- Improves readability — avoids vertical scrolling and keeps the response readable within an `editor.rulers=80` context.
- Aligns AI responses with UI settings — uses actual screen size and editor preferences (like `editor.rulers`) to compute budgets.
- Enforces concise writing — forces the system to summarize and prioritize information in contexts where the user needs a fast, single-screen summary.

How this helps (practical benefits)
----------------------------------
- Faster comprehension — one-screen answers reduce the time it takes to read and act on AI suggestions.
- Safer suggestions — by limiting content length we can reduce the chance of long, ambiguous code changes being pasted into the editor automatically.
- Better UX control — developers can tune the budget by changing font-size or `editor.rulers` instead of tuning the AI itself.

Practical use cases
-------------------
1. Chat-assisted code review — When an AI gives a code change suggestion or a summary of a failing test, one-screen summaries highlight the main issue and recommended change without overwhelming the developer.

2. Quick debugging summary — Present stack traces or error summaries compressed into a single screen; detailed logs remain available via a "view full" toggle.

3. Teaching and documentation — When generating explanations or small tutorials, one-screen mode gives a step-by-step checklist suitable for quick on-screen learning.

4. CLI & Terminal integrations — The ASCII progress bar and static HTML output make this usable in text-only environments (SSH or headless CI).

5. Accessibility & compact modes — For narrow or high-contrast displays, the budget can be tuned to make AI replies more legible and accessible.

Implementation details (short)
-----------------------------
- Budget calculation uses screen width/height, an average character width (derived from font size), a line height, and optionally an editor ruler (e.g., 80 columns) to compute `charBudget` and `targetChars`.
- `targetChars` includes a buffer (default 10%) to avoid overflow when editors reserve space for line numbers, tabs, or toolbars.
- `naive_summarize` currently uses a simple sentence-based approach (keep sentences until the budget is reached), with a fallback truncation for very small budgets. It is intentionally simple; a token-aware transformer-based summarizer can be added later to improve quality.

Next steps (suggestions for extension)
------------------------------------
- Add a token-aware summarizer using a transformer model (Hugging Face) so we can reliably measure tokens→characters.
- Add a lightweight Python web UI (Streamlit or Flask) to allow users to interactively change the budget and preview summaries live.
- Add a configuration file format (YAML/JSON) for user presets and a command-line `vision-ui --profile` to switch between presets.

Contact
-------
If you want any of the suggested extensions, or you'd like the summarizer to use token-length instead of characters, tell me which direction you prefer and I'll implement it in a Python-first manner.
