import pytest

from catalan_common_voice_filter.filtre_frases import \
    create_excluded_words_list


@pytest.fixture
def file_of_words_to_filter_out():
    return "test/data/paraules_per_filtrar_literatura.txt"


def test_create_excluded_words_list_with_file(file_of_words_to_filter_out):
    excluded_words = create_excluded_words_list(file_of_words_to_filter_out)
    assert len(excluded_words) > 0


def test_create_excluded_words_list_no_file():
    excluded_words = create_excluded_words_list(None)
    assert len(excluded_words) == 0
