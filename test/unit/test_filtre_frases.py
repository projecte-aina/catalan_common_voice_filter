from argparse import Namespace
from pathlib import Path

import pytest
import spacy

from catalan_common_voice_filter.filtre_frases import (
    add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true,
    are_excluded_characters_in_line,
    are_numbers_in_line,
    are_time_expressions_in_line,
    are_words_repeated,
    create_output_directory_path,
    is_correct_number_of_tokens,
    is_name,
    is_token_a_verb,
    is_valid_single_letter_token,
    line_ends_with_punctuation,
    line_starts_with_lowercase_letter,
    remove_unnecessary_characters,
    replace_abbreviations,
    sentence_ends_incorrectly,
    store_and_print_selected_options,
    token_starts_with_lowercase_letter_and_is_not_a_pronoun,
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


@pytest.fixture
def spacy_tokenizer():
    return spacy.load(
        "ca_core_news_sm", exclude=["parser", "attribute_ruler", "lemmatizer", "ner"]
    )


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


@pytest.mark.parametrize(
    "text,exclusion_list,expected",
    [
        ("Test line", [], ["Test line"]),
        (
            "Test line",
            ["Existing phrase 1", "Existing phrase 2"],
            ["Existing phrase 1", "Existing phrase 2", "Test line"],
        ),
    ],
)
def test_add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
    text, exclusion_list, expected
):
    exclude_phrase = False
    (
        exclusion_list,
        exclude_phrase,
    ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
        text, exclusion_list, exclude_phrase
    )

    assert len(exclusion_list) == len(expected)
    assert "Test line" in expected
    assert exclude_phrase == True


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
    "text,expected",
    [
        (
            "els catalans coneixem Mark Twain",
            True,
        ),
        ("Els catalans coneixem Mark Twain", False),
    ],
)
def test_line_starts_with_lowercase_letter(text, expected):
    result = line_starts_with_lowercase_letter(text)

    assert result == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Parla amb la Marta de Lopez", False),
        ("Parla amb la Marta de Lopez.", True),
        ("Parla amb la Marta de Lopez!", True),
        ("Parla amb la Marta de Lopez?", True),
        ("'Parla amb la Marta de Lopez'", True),
        ('"Parla amb la Marta de Lopez?"', True),
    ],
)
def test_line_ends_with_punctuation(text, expected):
    result = line_ends_with_punctuation(text)

    assert result == expected


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
        ("Not a name", ["Bibi", "Gines", "de Santos"], False),
    ],
)
def test_is_name(text, surnames, expected):
    result = is_name(text, surnames)

    assert result == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        ("T|e$t Phr@s#", True),
        (".test", True),
        ("Test:", True),
        ("Test - Line", True),
        ("Test line", False),
    ],
)
def test_are_excluded_characters_in_line(line, expected):
    result = are_excluded_characters_in_line(line)

    assert result == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("The meeting will be at 11:30 am tomorrow", True),
        ("The meeting will be at 15:00 tomorrow", True),
        ("The meeting will be at 15.30 tomorrow", True),
        ("The meeting will be tomorrow morning", False),
    ],
)
def test_are_time_expressions_in_line(text, expected):
    result = are_time_expressions_in_line(text)

    assert result == expected


@pytest.mark.parametrize(
    "text,expected",
    [("T3st Phr4S3", True), ("Test Phrase 3405942", True), ("Test phrase", False)],
)
def test_are_numbers_in_line(text, expected):
    result = are_numbers_in_line(text)

    assert result == expected


@pytest.mark.parametrize(
    "tokens,expected",
    [
        (["Bon", "dia"], False),
        (["Bon", "dia", "tingui"], False),
        (
            [
                "Els",
                "catalans",
                "coneixem",
                "Mark",
                "Twain",
                "sobretot",
                "gràcies",
                "a",
                "Les",
                "aventures",
                "de",
                "Tom",
                "Sawyer",
                "i",
                "Les",
                "aventures",
                "de",
                "Huckleberry",
                "Finn",
                "novel·les",
            ],
            False,
        ),
        (["Els", "catalans", "coneixem", "Mark", "Twain"], True),
    ],
)
def test_is_correct_number_of_tokens(tokens, expected):
    result = is_correct_number_of_tokens(tokens)

    assert result == expected


@pytest.mark.parametrize(
    "tokens,expected",
    [
        (["Els", "catalans", "coneixem", "amb"], True),
        (["La", "Maria", "Marieta", "canta", "i", "balla", "al" "matí"], False),
    ],
)
def test_sentence_ends_incorrectly(tokens, expected):
    result = sentence_ends_incorrectly(tokens)

    assert result == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        ("agrada", True),
        ("ha", True),
        ("alemany", False),
    ],
)
def test_is_token_a_verb(line, expected, spacy_tokenizer):
    tokens = spacy_tokenizer(line)
    for token in tokens:
        result = is_token_a_verb(token)

        assert result == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("DNI", "document nacional d'identitat"),
        ("sra", "senyora"),
        ("Bon dia tingui, dra Maria.", "Bon dia tingui, doctora Maria."),
        ("Bon dia tingui, Sr. Felip.", "Bon dia tingui, senyor Felip."),
        (
            "M'agrada mirar-te als ulls, m'hi ofegaria.",
            "M'agrada mirar-te als ulls, m'hi ofegaria.",
        ),
    ],
)
def test_replace_abbreviations(text, expected, spacy_tokenizer):
    tokens = spacy_tokenizer(text)
    for token in tokens:
        text = replace_abbreviations(token, text)

    assert text == expected


@pytest.mark.parametrize("text,expected", [("a", True), ("i", True), ("s", False)])
def test_is_valid_single_letter_token(text, expected, spacy_tokenizer):
    tokens = spacy_tokenizer(text)
    for token in tokens:
        result = is_valid_single_letter_token(token)

    assert result == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("test", True),
        ("ls", False),
        ("Test", False),
    ],
)
def test_token_starts_with_lowercase_letter_and_is_not_a_pronoun(
    text, expected, spacy_tokenizer
):
    tokens = spacy_tokenizer(text)
    for token in tokens:
        result = token_starts_with_lowercase_letter_and_is_not_a_pronoun(token)

    assert result == expected
