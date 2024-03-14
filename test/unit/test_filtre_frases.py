from argparse import Namespace
from pathlib import Path

import pytest

from catalan_common_voice_filter.filtre_frases import (
    check_if_line_starts_with_lowercase_letter,
    create_output_directory_path,
    remove_unnecessary_characters,
    store_and_print_selected_options,
)


@pytest.fixture
def all_args():
    selected_args = dict(
        punctuation=True,
        numbers=True,
        verb=True,
        capitals=True,
        proper_nouns=True,
    )
    args = Namespace(**selected_args)
    return args


@pytest.fixture
def some_args():
    selected_args = dict(
        punctuation=False,
        numbers=True,
        verb=True,
        capitals=False,
        proper_nouns=False,
    )
    args = Namespace(**selected_args)
    return args


def test_store_and_print_selected_options_with_all_options(all_args):
    file_name = "test_file"
    selected_options = store_and_print_selected_options(all_args, file_name)
    assert len(selected_options) == 7

    assert "- Només frases amb marques de finals" in selected_options
    assert "- S'eliminen les frases amb xifres" in selected_options
    assert "- Només frases amb verbs" in selected_options
    assert "- Només frases que comencen amb majúscula" in selected_options
    assert "- Exclou frases amb possibles noms" in selected_options
    assert file_name in selected_options[0]


def test_store_and_print_selected_options_with_some_options(some_args):
    file_name = "test_file"
    selected_options = store_and_print_selected_options(some_args, file_name)
    assert len(selected_options) == 4

    assert "- S'eliminen les frases amb xifres" in selected_options
    assert "- Només frases amb verbs" in selected_options
    assert file_name in selected_options[0]

    assert "- Només frases amb marques de finals" not in selected_options
    assert "- Només frases que comencen amb majúscula" not in selected_options
    assert "- Exclou frases amb possibles noms" not in selected_options


def test_create_output_directory_path_with_specified_directory():
    results_dir = "path/to/results"
    file_to_filter = Path("test_filter_file.txt")

    output_dir = create_output_directory_path(results_dir, file_to_filter)
    assert str(output_dir) == results_dir


def test_create_output_directory_path_without_specified_directory():
    file_to_filter = Path("path/to/test_filter_file.txt")

    output_dir = create_output_directory_path(None, file_to_filter)
    assert output_dir.parent == file_to_filter.parent
    assert file_to_filter.stem in str(output_dir)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("%$/>&!!Els catalans coneixem Mark Twain", "Els catalans coneixem Mark Twain"),
        ("Els catalans coneixem Mark Twain", "Els catalans coneixem Mark Twain"),
        ("«Els catalans coneixem Mark Twain»", "«Els catalans coneixem Mark Twain»"),
        ("/>@#$", ">@#$"),
    ],
)
def test_remove_unnecessary_characters(text, expected):
    line = remove_unnecessary_characters(text)

    assert line == expected


@pytest.mark.parametrize(
    "text,only_allow_capitalized_sentences,expected",
    [
        (
            "els catalans coneixem Mark Twain",
            True,
            (["els catalans coneixem Mark Twain"], True),
        ),
        ("els catalans coneixem Mark Twain", False, ([], False)),
        ("Els catalans coneixem Mark Twain", True, ([], False)),
        ("Els catalans coneixem Mark Twain", False, ([], False)),
    ],
)
def test_check_if_line_starts_with_lowercase_letter(
    text, only_allow_capitalized_sentences, expected
):
    excluded_min = []
    excluded_min, exclude_phrase = check_if_line_starts_with_lowercase_letter(
        text, text, only_allow_capitalized_sentences, excluded_min
    )

    assert excluded_min == expected[0]
    assert exclude_phrase == expected[1]
