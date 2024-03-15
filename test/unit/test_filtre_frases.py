from argparse import Namespace
from pathlib import Path

import pytest

from catalan_common_voice_filter.filtre_frases import (
    are_words_repeated,
    check_if_line_ends_with_punctuation,
    check_if_line_is_a_name,
    check_if_line_starts_with_lowercase_letter,
    create_output_directory_path,
    is_name,
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
    exclude_phrase = False
    excluded_min, exclude_phrase = check_if_line_starts_with_lowercase_letter(
        text, text, only_allow_capitalized_sentences, excluded_min, exclude_phrase
    )

    assert excluded_min == expected[0]
    assert exclude_phrase == expected[1]


@pytest.mark.parametrize(
    "text,only_allow_punctuation,expected",
    [
        ("Parla amb la Marta de Lopez", True, (["Parla amb la Marta de Lopez"], True)),
        ("Parla amb la Marta de Lopez.", True, ([], False)),
        ("Parla amb la Marta de Lopez", False, ([], False)),
        ("Parla amb la Marta de Lopez.", False, ([], False)),
    ],
)
def test_check_if_line_ends_with_punctuation(text, only_allow_punctuation, expected):
    possible_breaks = []
    exclude_phrase = False
    possible_breaks, exclude_phrase = check_if_line_ends_with_punctuation(
        text, text, only_allow_punctuation, possible_breaks, exclude_phrase
    )

    assert possible_breaks == expected[0]
    assert exclude_phrase == expected[1]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Parla Parla", True),
        ("Parla parla", True),
        ("Parla amb amb la Marta de Lopez", True),
        ("Parla amb la Marta de Lopez", False),
    ],
)
def test_are_words_repeated(text, expected):
    result = are_words_repeated(text)

    assert result == expected


@pytest.mark.parametrize(
    "text,surnames,expected",
    [
        ("Raul de Santos", ["Bibi", "Company", "de Santos"], True),
        ("Marco Del Pino", ["Bibi", "Company", "de Santos"], False),
        ("Marco Del Pino", ["Bibi", "Del Pino", "de Santos"], True),
        ("P Zhu", ["Bibi", "Zhu", "de Santos"], False),
        ("Raul Gines", ["Bibi", "Gines", "de Santos"], True),
    ],
)
def test_is_name(text, surnames, expected):
    result = is_name(text, surnames)

    assert result == expected


@pytest.mark.parametrize(
    "text,surnames,exclude_proper_nouns,expected",
    [
        (
            "Raul de Santos",
            ["Bibi", "Company", "de Santos"],
            True,
            (["Raul de Santos"], True),
        ),
        ("Not a name", ["Bibi", "Company", "de Santos"], True, ([], False)),
        ("Raul de Santos", ["Bibi", "Company", "de Santos"], False, ([], False)),
        ("Not a name", ["Bibi", "Company", "de Santos"], False, ([], False)),
    ],
)
def test_check_if_line_is_a_name(text, surnames, exclude_proper_nouns, expected):
    excluded_names = []
    exclude_phrase = False

    excluded_names, exclude_phrase = check_if_line_is_a_name(
        text, text, exclude_proper_nouns, surnames, excluded_names, exclude_phrase
    )

    assert excluded_names == expected[0]
    assert exclude_phrase == expected[1]
