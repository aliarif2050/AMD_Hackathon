"""Conservative zero-token solvers for obvious tasks.

These solvers are intentionally precision-first. Returning ``None`` is the
normal safe outcome when a prompt does not match a narrow, deterministic shape.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re

_NUMBER = r"-?\d+(?:\.\d+)?"

_POSITIVE_CUES = {
    "amazing",
    "awesome",
    "excellent",
    "fantastic",
    "good",
    "great",
    "happy",
    "love",
    "loved",
    "perfect",
    "pleased",
    "positive",
    "recommend",
    "satisfied",
    "wonderful",
}
_NEGATIVE_CUES = {
    "awful",
    "bad",
    "broken",
    "disappointed",
    "disappointing",
    "hate",
    "hated",
    "negative",
    "poor",
    "scratches",
    "slow",
    "terrible",
    "unhappy",
    "worst",
}
_CONTRASTS = {"but", "however", "although", "though", "yet", "nevertheless"}
_NEGATIONS = {"not", "never", "no", "none", "hardly", "barely", "without"}


def try_solve(task_type: str, prompt: str) -> str | None:
    """Return a deterministic answer for obvious prompts, else ``None``."""
    if task_type == "math":
        return _try_math(prompt)
    if task_type == "sentiment":
        return _try_sentiment(prompt)
    return None


def _try_math(prompt: str) -> str | None:
    text = _normalize_math_text(prompt)
    return (
        _try_percentage_remaining(text)
        or _try_sum(text)
        or _try_average(text)
        or _try_product(text)
        or _try_binary_arithmetic(text)
    )


def _normalize_math_text(prompt: str) -> str:
    return (
        prompt.lower()
        .replace("\u00d7", "*")
        .replace("\u2715", "*")
        .replace("\u00f7", "/")
        .replace(",", "")
    )


def _try_percentage_remaining(text: str) -> str | None:
    if "remain" not in text and "left" not in text:
        return None
    if len(re.findall(rf"{_NUMBER}\s*%", text)) != 1:
        return None

    initial = re.search(
        rf"\b(?:has|have|starts with|started with|there are|with)\s+({_NUMBER})\s+([a-z]+)\b",
        text,
    )
    pct = re.search(
        rf"\b(?:sells|sold|uses|used|loses|lost|spends|spent|removes|removed)\s+({_NUMBER})\s*%",
        text,
    )
    fixed = re.search(
        rf"\b(?:and\s+)?({_NUMBER})\s+more\b",
        text,
    )
    if not (initial and pct and fixed):
        return None

    try:
        start = Decimal(initial.group(1))
        percent = Decimal(pct.group(1))
        extra = Decimal(fixed.group(1))
    except InvalidOperation:
        return None
    if start < 0 or percent < 0 or percent > 100 or extra < 0:
        return None

    answer = start - (start * percent / Decimal("100")) - extra
    if answer < 0:
        return None
    return _format_decimal(answer)


def _try_sum(text: str) -> str | None:
    match = re.search(rf"\b(?:sum|total)\s+(?:of\s+)?((?:{_NUMBER}(?:\s*(?:and|plus|\+)?\s*))+)", text)
    if not match:
        return None
    values = _numbers(match.group(1))
    if len(values) < 2:
        return None
    return _format_decimal(sum(values, Decimal("0")))


def _try_average(text: str) -> str | None:
    match = re.search(rf"\baverage\s+(?:of\s+)?((?:{_NUMBER}(?:\s*(?:and|plus|\+)?\s*))+)", text)
    if not match:
        return None
    values = _numbers(match.group(1))
    if len(values) < 2:
        return None
    return _format_decimal(sum(values, Decimal("0")) / Decimal(len(values)))


def _try_product(text: str) -> str | None:
    match = re.search(rf"\bproduct\s+of\s+({_NUMBER})\s+(?:and|times|\*)\s+({_NUMBER})\b", text)
    if not match:
        return None
    return _format_decimal(Decimal(match.group(1)) * Decimal(match.group(2)))


def _try_binary_arithmetic(text: str) -> str | None:
    op_words = {
        "+": "+",
        "plus": "+",
        "add": "+",
        "-": "-",
        "minus": "-",
        "less": "-",
        "*": "*",
        "x": "*",
        "times": "*",
        "multiply": "*",
        "multiplied by": "*",
        "/": "/",
        "divided by": "/",
        "divide": "/",
    }
    if not re.search(r"\b(?:what is|calculate|compute)\b", text):
        return None

    op_pattern = "|".join(re.escape(op) for op in sorted(op_words, key=len, reverse=True))
    match = re.search(rf"\b({_NUMBER})\s*({op_pattern})\s*({_NUMBER})\b", text)
    if not match:
        return None

    left = Decimal(match.group(1))
    op = op_words[match.group(2)]
    right = Decimal(match.group(3))
    if op == "+":
        return _format_decimal(left + right)
    if op == "-":
        return _format_decimal(left - right)
    if op == "*":
        return _format_decimal(left * right)
    if right == 0:
        return None
    return _format_decimal(left / right)


def _try_sentiment(prompt: str) -> str | None:
    text = prompt.lower()
    tokens = set(re.findall(r"[a-z']+", text))
    if tokens & _CONTRASTS or tokens & _NEGATIONS:
        return None

    # Prefer the review body after the instruction when present.
    if ":" in text:
        text = text.split(":", 1)[1]
        tokens = set(re.findall(r"[a-z']+", text))

    positive = tokens & _POSITIVE_CUES
    negative = tokens & _NEGATIVE_CUES
    if positive and not negative:
        return "positive"
    if negative and not positive:
        return "negative"
    return None


def _numbers(text: str) -> list[Decimal]:
    try:
        return [Decimal(value) for value in re.findall(_NUMBER, text)]
    except InvalidOperation:
        return []


def _format_decimal(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".")
