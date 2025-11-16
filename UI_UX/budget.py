"""
budget.py

Utilities to compute a "one-screen" budget based on screen/window size and editor settings.
All code is pure Python; no JavaScript.
"""

from typing import Union
import textwrap
from typing import Dict
from .token_utils import estimate_avg_chars_per_token, chars_to_tokens


def compute_budget(width_px: int, height_px: int,
                   font_size_px: int = 14,
                   avg_char_width_px: Union[float, None] = None,
                   line_height_px: Union[float, None] = None,
                   editor_ruler_columns: Union[int, None] = 80,
                   buffer: float = 0.9) -> Dict[str, Union[int, float]]:
    """
    Compute a character budget based on pixel dimensions and font metrics.

    Args:
      width_px, height_px: window dimensions in px
      font_size_px: font point size in px
      avg_char_width_px: average char width in px. If None, we use font_size_px*0.55
      line_height_px: line height in px. If None, we use font_size_px * 1.25
      editor_ruler_columns: optional max columns (e.g., 80)
      buffer: keep some fraction of the total to avoid overflow (default 0.9)

    Returns a dict with `columns`, `lines`, `effective_columns`, `char_budget`, and `target_chars`.
    """
    if avg_char_width_px is None:
        avg_char_width_px = max(4.0, font_size_px * 0.55)
    if line_height_px is None:
        line_height_px = max(12.0, font_size_px * 1.25)

    columns = max(1, int(width_px // avg_char_width_px))
    lines = max(1, int(height_px // line_height_px))

    effective_columns = columns if editor_ruler_columns is None else min(columns, editor_ruler_columns)
    char_budget = effective_columns * lines
    target_chars = int(char_budget * buffer)

    return {
        "width_px": width_px,
        "height_px": height_px,
        "columns": columns,
        "lines": lines,
        "effective_columns": effective_columns,
        "char_budget": char_budget,
        "target_chars": target_chars,
        "font_size_px": font_size_px,
        "avg_char_width_px": avg_char_width_px,
        "line_height_px": line_height_px,
    }


def progress_bar(chars_used: int, char_budget: int, width: int = 28) -> str:
    """Return a simple ASCII progress bar with fill based on chars_used / char_budget."""
    if char_budget <= 0:
        return "[no budget]"
    ratio = min(1.0, max(0.0, chars_used / char_budget))
    fill = int(ratio * width)
    return "[" + "#" * fill + "-" * (width - fill) + "] " + f"{int(ratio*100)}%"


def naive_summarize(text: str, char_limit: int) -> str:
    """Naive summarizer: keep useful sentences until char_limit.

    This is intentionally simple; for production use a sentence-ranker or transformer-based summarizer.
    """
    if not text:
        return ""

    # Respect the requested char_limit while avoiding absurdly small values.
    # Lower bound of 10 ensures truncation still produces a meaningful short string.
    max_chars = max(10, int(char_limit))
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    summary = []
    for sentence in sentences:
        candidate = ('. '.join(summary + [sentence]) + '.')
        if len(candidate) <= max_chars:
            summary.append(sentence)
        else:
            break

    if not summary:
        # fallback to truncation
        return (textwrap.shorten(text, width=max_chars, placeholder='...'))

    return '. '.join(summary) + '.'


# Small helper to pretty-print a budget
def pretty_budget(b: Dict[str, int]) -> str:
    return (f"{b['columns']} cols x {b['lines']} lines  (effective={b['effective_columns']}) -> "
            f"budget={b['char_budget']} target={b['target_chars']}")


def token_aware_budget(budget: Dict[str, int], samples: list[str] | None = None, tokenizer=None, model_name: str = "gpt2") -> Dict[str, int]:
    """Return a token-aware extension of `budget`.

    This function estimates an average chars/token ratio using `token_utils.estimate_avg_chars_per_token` and
    returns a budget augmented with `chars_per_token`, `token_budget_est`, and `token_target_est`.
    If a tokenizer is not available, a fallback of 4 chars/token is used.
    """
    chars_ratio = estimate_avg_chars_per_token(samples=samples or [], tokenizer=tokenizer, model_name=model_name)
    token_budget = chars_to_tokens(budget["char_budget"], chars_ratio)
    token_target = chars_to_tokens(budget["target_chars"], chars_ratio)
    return {
        **budget,
        "chars_per_token": chars_ratio,
        "token_budget_est": token_budget,
        "token_target_est": token_target,
    }
