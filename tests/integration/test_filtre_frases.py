# mypy: ignore-errors
from pathlib import Path

import pytest

from catalan_common_voice_filter.filtre_frases import (
    create_excluded_words_list,
    split_filter_file_into_sentences,
)


@pytest.fixture
def file_of_words_to_filter_out():
    return Path("tests/data/paraules_per_filtrar_literatura.txt")


@pytest.fixture
def file_to_filter():
    return Path("tests/data/frases_prova.txt")


def test_create_excluded_words_list_with_file(file_of_words_to_filter_out):
    excluded_words = create_excluded_words_list(str(file_of_words_to_filter_out))
    assert len(excluded_words) > 0


def test_create_excluded_words_list_no_file():
    excluded_words = create_excluded_words_list(None)
    assert len(excluded_words) == 0


def test_split_filter_file_into_sentences(file_to_filter):
    sentences, total_lines = split_filter_file_into_sentences(file_to_filter)
    assert len(sentences) > 0
    assert total_lines == 25
