"""filters.py — composable look chains."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import filters  # noqa: E402


def test_chain_single_look():
    assert filters.chain("cinematic")  # non-empty ffmpeg filter string


def test_chain_composes_with_commas():
    ch = filters.chain("warm", "grain")
    assert "," in ch  # two filters joined


def test_chain_empty_is_empty():
    assert filters.chain() == ""


def test_resolve_alias():
    # aliases resolve to a real look key
    for alias in filters.ALIASES:
        assert filters.resolve(alias) in filters.LOOKS


def test_unknown_look_raises():
    with pytest.raises(KeyError):
        filters.resolve("definitely_not_a_look")


def test_all_looks_are_valid_strings():
    for name in filters.LOOKS:
        assert isinstance(filters.chain(name), str) and filters.chain(name)
