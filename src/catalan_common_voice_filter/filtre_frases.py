import logging
import os
import re
import subprocess
from argparse import ArgumentParser, Namespace
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Match, Tuple, Union

import hunspell
import lingua_franca
import spacy
import unidecode
from lingua_franca.format import pronounce_number
from sentence_splitter import SentenceSplitter
from spacy.tokens import Doc
from spacy.tokens.token import Token

from catalan_common_voice_filter.constants import (
    EMOJIS,
    HOURS,
    INCORRECT_SENTENCE_END_WORDS,
    NUMBERS,
    PUNCTUATION_TO_EXCLUDE,
    QUOTATION_MARKS,
    REPEATED_WORDS,
    REPLACEMENT_WORDS,
    SENTENCE_END_CHARS,
)

logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)


def add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
    line: str, exclusion_list: List[str], exclude_phrase: bool
) -> Tuple[List[str], bool]:
    exclusion_list.append(line)
    exclude_phrase = True
    return exclusion_list, exclude_phrase


def get_surname_list() -> List[str]:
    with open(Path("data/cognoms_list.txt"), "r") as f:
        all_surnames = f.read().splitlines()

    surnames = [surname for surname in all_surnames if len(surname) >= 3]
    return surnames


def describe(descriptor: str, exclusion_list: List[str], total: int) -> str:
    text = (
        descriptor
        + " "
        + str(len(exclusion_list))
        + " ("
        + str(round(len(exclusion_list) * 100 / total, 2))
        + "%)"
    )
    return text


def create_file(
    output_dir: Path,
    filter_file_name: str,
    statistics_file_name: str,
    exclusion_list: List[str],
) -> None:
    exclusion_list.sort()

    os.makedirs(output_dir, exist_ok=True)
    new_file = output_dir / f"{filter_file_name}_{statistics_file_name}"
    with open(new_file, "w") as f:
        for frase in exclusion_list:
            f.writelines(frase + "\n")


def fix_apostrophes(line: str) -> str:
    line = re.sub(r"([nldNLD])’(h?[aeiouAEIOUàèéíòóúÀÈÉÍÒÓÚ])", r"\1'\2", line)
    line = re.sub(r"([aeiouAEIOUàèéíòóú])’([nldNLD])", r"\1'\2", line)
    line = re.sub(
        r"([aeiouAEIOUàèéíòóúnldNLD])' (h?[aeiouAEIOUàèéíòóúnldNLD])", r"\1'\2", line
    )
    return line


def fix_quotation_marks(line: str) -> str:
    character_counts = Counter(line)
    quotation_mark_character_counts = {
        char: character_counts[char]
        for char in QUOTATION_MARKS
        if char in character_counts.keys()
    }
    quotation_mark_count_sum = sum(quotation_mark_character_counts.values())

    if quotation_mark_count_sum % 2 != 0:
        for char in quotation_mark_character_counts.keys():
            line = line.replace(char, "")

    return line


def store_and_print_selected_options(
    args: Namespace, filter_file_name: str
) -> List[str]:
    selected_options = [
        "* File: " + filter_file_name + "\n",
        "* Opcions seleccionades:",
    ]
    print(*selected_options)

    if args.punctuation:
        text = "- Només frases amb marques de finals"
        print(text)
        selected_options.append(text)
    if args.numbers:
        text = "- S'eliminen les frases amb xifres"
        print(text)
        selected_options.append(text)
    if args.verb:
        text = "- Només frases amb verbs"
        print(text)
        selected_options.append(text)
    if args.capitals:
        text = "- Només frases que comencen amb majúscula"
        print(text)
        selected_options.append(text)
    if args.proper_nouns:
        text = "- Exclou frases amb possibles noms"
        print(text)
        selected_options.append(text)

    return selected_options


def create_output_directory_path(
    output_dir: Union[str, None], file_to_filter: Path
) -> Path:
    if output_dir:
        return Path(output_dir)

    now = datetime.now().strftime("%Y%m%d_%H%M")
    return file_to_filter.parent / f"resulats_filtre_{file_to_filter.stem}_{now}"


def create_excluded_words_list(excluded_words_list_file: Union[str, None]) -> List[str]:
    words_to_exclude = []
    if excluded_words_list_file:
        excluded_words_list_path = Path(excluded_words_list_file)
        with open(excluded_words_list_path, "r") as f:
            words_to_exclude = f.read().splitlines()

    return words_to_exclude


def split_filter_file_into_sentences(file_to_filter: Path) -> Tuple[List[str], int]:
    splitter = SentenceSplitter(language="ca")

    with open(file_to_filter, "r") as f:
        file_lines = f.readlines()

    sentences = []
    total_lines = 0
    for line in file_lines:
        total_lines += 1
        phrases = splitter.split(line)
        for phrase in phrases:
            parts = phrase.split(":")
            sentences.append(parts[-1])

    return sentences, total_lines


def is_line_length_correct(line: str) -> bool:
    return len(line) > 4


def remove_unnecessary_characters(line: str) -> str:
    first_char = line[0]
    if first_char not in QUOTATION_MARKS:
        while is_line_length_correct(line) and not line[0].isalpha():
            line = line[1:]

    return line


def line_starts_with_lowercase_letter(
    line: str,
) -> bool:
    if line[0].islower():
        return True

    return False


def line_ends_with_punctuation(
    line: str,
) -> bool:
    if line[-1] in SENTENCE_END_CHARS:
        return True

    return False


def are_words_repeated(line: str) -> bool:
    if not re.search(REPEATED_WORDS, line.lower()):
        return False

    return True


def _is_word_too_short_to_be_name(name_search: Match[str]) -> bool:
    return name_search.span()[0] == 0 and len(name_search.group(0).split(" ")[0]) <= 2


def is_name(line: str, surnames: List[str]) -> bool:
    possible_names = re.compile(r"[A-Z][a-ü]+ ([Dd][\'e](l)?)? ?[A-Z][a-ü]*")
    name_search = re.search(possible_names, line)

    if name_search:
        possible_name = name_search.group(0)
        possible_surname = possible_name[possible_name.index(" ") + 1 :]

        if unidecode.unidecode(possible_surname) in surnames:
            if _is_word_too_short_to_be_name(name_search):
                return False

            return True

    return False


def clean_up_characters_in_parentheses(line: str) -> str:
    line = re.sub(r" \([A-Úa-ú0-9 -\.\,]*\)", "", line)
    return line


def are_excluded_characters_in_line(line: str) -> bool:
    if (
        any(char in PUNCTUATION_TO_EXCLUDE for char in line)
        or re.search(r"\.[a-zA-Z]", line)
        or re.search(EMOJIS, line)
        or line[-1] == ":"
        or " - " in line
    ):
        return True

    return False


def are_time_expressions_in_line(line: str) -> bool:
    if re.search(HOURS, line):
        return True

    return False


def are_numbers_in_line(line: str) -> bool:
    return any(char in NUMBERS for char in line)


def is_correct_number_of_tokens(tokens: List[str]) -> bool:
    return len(tokens) > 3 and len(tokens) < 19


def sentence_ends_incorrectly(tokens: List[str]) -> bool:
    return tokens[-1] in INCORRECT_SENTENCE_END_WORDS


def is_token_a_verb(token: Token) -> bool:
    if token.pos_ == "VERB" or token.pos_ == "AUX":
        return True

    return False


def replace_abbreviations(token: Token, line: str) -> str:
    if token.text.lower() in REPLACEMENT_WORDS.keys():
        line = line.replace(
            token.text,
            REPLACEMENT_WORDS[token.text.lower()],
        )

    return line


def is_valid_single_letter_token(token: Token) -> bool:
    return token.text.lower() in ["a", "e", "i", "o", "u", "l", "d", "p"]


def token_starts_with_lowercase_letter_and_is_not_a_pronoun(token: Token) -> bool:
    if token.text[0].islower() and token.text != "ls":
        return True

    return False


def token_contains_numbers(token: Token) -> bool:
    return any(char in token.text for char in NUMBERS)


def _is_token_depicting_an_hour(token: Token) -> bool:
    if token.text[-1] == "h":
        return True

    return False


def _replace_hour_abbreviation_with_full_word(
    token: Token, line: str, number: str, number_in_catalan: str
) -> str:
    line = line.replace(token.text, token.text[:-1])
    line = re.sub(number, number_in_catalan + " hores", line)
    return line


def transcribe_number(token: Token, line: str) -> str:
    numbers = re.findall(r" \d+ |\d+(?=\D|$)", token.text)
    for number in numbers:
        try:
            number_as_word = pronounce_number(int(number), "en")
            number_in_catalan = translate_to_catalan(number_as_word)
            if _is_token_depicting_an_hour(token):
                line = _replace_hour_abbreviation_with_full_word(
                    token, line, number, number_in_catalan
                )
            else:
                line = re.sub(number, number_in_catalan, line)
        except IOError as err:
            raise IOError(err)

    return line


def translate_to_catalan(number_in_english: str) -> str:
    command = f'echo "{number_in_english}" | apertium eng-cat'
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output, error = process.communicate()

    if error:
        raise IOError(error)
    else:
        return output.strip()


def line_does_not_contain_verb_and_verbs_required(
    verb_token_present: bool, verb_required: bool, exclude_phrase: bool
) -> bool:
    return not verb_token_present and verb_required and not exclude_phrase


def is_token_a_proper_noun(token: Token) -> bool:
    if token.text[0].isupper():
        return True

    return False


def is_proper_noun_ratio_correct(proper_noun_count: int, tokens: Doc) -> bool:
    return proper_noun_count < len(tokens) / 3


def clean_up_sentence_end(line: str) -> str:
    if line[-1] == ",":
        line = line[:-1]
    line = line + "."
    return line


def clean_up_sentence_beginning(line: str) -> str:
    if line[0] == " ":
        line = line[1:]
    if line[0].islower():
        line = line[0].upper() + line[1:]
    return line


def replace_multiple_punctuation_marks_with_single_punctuation_mark(line: str) -> str:
    line = re.sub(r"([\?\!])\.", "\\1", line)
    line = re.sub(r"\!+", "!", line)
    line = re.sub(r"\?+", "?", line)
    return line


def is_multiple_periods_in_sentence(line: str) -> bool:
    return "." in line[:-2]


def correctly_format_elipses(line: str) -> str:
    line = re.sub(r"\.(\.)+", "...", line)
    return line


def create_output_dir_if_not_exists(output_dir: Path) -> None:
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        print("Hem creat el directori", output_dir)
    else:
        print("El directori", output_dir, "ja existeix")


def create_case_studies_file(output_file: Path, case_studies: List[List[str]]) -> None:
    with open(output_file, "w") as f:
        for phrase in case_studies:
            f.writelines(phrase[1] + "\t" + phrase[0] + "\n")


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--file",
        "-f",
        dest="file_to_filter",
        action="store",
        help="fitxer que es vol filtrar",
        required=True,
    )
    parser.add_argument(
        "--list",
        "-l",
        dest="list",
        action="store",
        help="llista de paraules que es volen eliminar",
    )
    parser.add_argument(
        "--dir",
        "-d",
        dest="dir",
        action="store",
        help="directori on es desaran els resultats",
    )
    parser.add_argument(
        "--num",
        "-n",
        dest="numbers",
        action="store_true",
        help="no es transcriuen els números",
        default=False,
    )
    parser.add_argument(
        "--verb",
        "-v",
        dest="verb",
        action="store_true",
        help="només frases amb verbs",
        default=False,
    )
    parser.add_argument(
        "--punt",
        "-p",
        dest="punctuation",
        action="store_true",
        help="només frases amb marques de finals",
        default=False,
    )
    parser.add_argument(
        "--cap",
        "-c",
        dest="capitals",
        action="store_true",
        help="només frases que comencen amb majúscules",
        default=False,
    )
    parser.add_argument(
        "--noms-propis",
        "-np",
        dest="proper_nouns",
        action="store_true",
        help="exclou frases amb possibles noms propis",
        default=False,
    )
    args = parser.parse_args()

    lingua_franca.load_language("en")
    dic = hunspell.HunSpell("data/ca.dic", "data/ca.aff")
    spacy_tokenizer = spacy.load(
        "ca_core_news_sm", exclude=["parser", "attribute_ruler", "lemmatizer", "ner"]
    )
    surnames = get_surname_list()

    file_to_filter = Path(args.file_to_filter)
    filter_file_name = file_to_filter.stem

    selected_options = store_and_print_selected_options(args, filter_file_name)
    output_dir = create_output_directory_path(args.dir, file_to_filter)
    words_to_exclude = create_excluded_words_list(args.list)
    sentences, total_lines = split_filter_file_into_sentences(file_to_filter)

    # here are the lists where the sentences are saved depending on whether they are discarded or not
    discarded_tokens: List[str] = []
    selected_phrases: List[str] = []
    selected_phrases_orig: List[str] = []
    selected_phrases_repeated: List[str] = []
    excluded_characters: List[str] = []
    excluded_spellings: List[str] = []
    excluded_ratios: List[str] = []
    excluded_sentences_improper_length: List[str] = []
    excluded_acronyms: List[str] = []
    excluded_words: List[str] = []
    excluded_repeated_words: List[str] = []
    excluded_names: List[str] = []
    error_num: List[str] = []
    excluded_abbreviations: List[str] = []
    excluded_hours: List[str] = []
    possible_breaks: List[str] = []
    case_studies: List[List[str]] = []
    spelling_case_studies: List[List[str]] = []
    excluded_lowercase: List[str] = []
    excluded_nums: List[str] = []
    excluded_verbs: List[str] = []

    for line in sentences:
        proper_noun_count = 0
        exclude_phrase = False
        original_phrase = line

        if not is_line_length_correct(line):
            (
                excluded_sentences_improper_length,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_sentences_improper_length, exclude_phrase
            )
            continue

        line = remove_unnecessary_characters(line)

        if args.capitals and line_starts_with_lowercase_letter(line):
            (
                excluded_lowercase,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_lowercase, exclude_phrase
            )

        if args.punctuation and not line_ends_with_punctuation(line):
            (
                possible_breaks,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, possible_breaks, exclude_phrase
            )

        if are_words_repeated(line):
            (
                excluded_repeated_words,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_repeated_words, exclude_phrase
            )
            continue

        if args.proper_nouns and is_name(line, surnames):
            (
                excluded_names,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_names, exclude_phrase
            )

        line = clean_up_characters_in_parentheses(line)
        if are_excluded_characters_in_line(line):
            (
                excluded_characters,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_characters, exclude_phrase
            )
            continue

        if are_time_expressions_in_line(line):
            (
                excluded_hours,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_hours, exclude_phrase
            )
            continue

        if args.numbers and are_numbers_in_line(line):
            (
                excluded_nums,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_nums, exclude_phrase
            )
            continue

        simple_tokens = line.split(" ")  # we do a simple first tokenization
        if not is_correct_number_of_tokens(simple_tokens):
            (
                excluded_sentences_improper_length,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_sentences_improper_length, exclude_phrase
            )
            continue

        if sentence_ends_incorrectly(simple_tokens):
            (
                possible_breaks,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, possible_breaks, exclude_phrase
            )
            continue

        tokens = spacy_tokenizer(line)
        verb_token_present = False
        for token in tokens:
            if is_token_a_verb(token):
                verb_token_present = True

            line = replace_abbreviations(token, line)

            if token.text.isalpha():
                if len(token) == 1 and not is_valid_single_letter_token(token):
                    (
                        excluded_spellings,
                        exclude_phrase,
                    ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                        original_phrase, excluded_spellings, exclude_phrase
                    )
                    spelling_case_studies.append(
                        [
                            original_phrase,
                            token.text,
                        ]
                    )
                    break

                if token.text.isupper():
                    (
                        excluded_acronyms,
                        exclude_phrase,
                    ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                        original_phrase, excluded_acronyms, exclude_phrase
                    )
                    break

                if token.text in words_to_exclude:
                    (
                        excluded_words,
                        exclude_phrase,
                    ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                        original_phrase, excluded_words, exclude_phrase
                    )
                    case_studies.append(
                        [
                            original_phrase,
                            token.text,
                        ]
                    )
                    break

                if not dic.spell(token.text):
                    if token_starts_with_lowercase_letter_and_is_not_a_pronoun(token):
                        (
                            excluded_spellings,
                            exclude_phrase,
                        ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                            original_phrase, excluded_spellings, exclude_phrase
                        )
                        spelling_case_studies.append(
                            [
                                original_phrase,
                                token.text,
                            ]
                        )
                        (
                            discarded_tokens,
                            exclude_phrase,
                        ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                            token.text, discarded_tokens, exclude_phrase
                        )
                        break

                    if is_token_a_proper_noun(token):
                        proper_noun_count += 1

            if token_contains_numbers(token):
                try:
                    line = transcribe_number(token, line)
                except IOError as err:
                    logging.error(err)
                    (
                        error_num,
                        exclude_phrase,
                    ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                        original_phrase, error_num, exclude_phrase
                    )
                    break
                if not exclude_phrase and not is_correct_number_of_tokens(
                    line.split(" ")
                ):
                    (
                        excluded_sentences_improper_length,
                        exclude_phrase,
                    ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                        original_phrase,
                        excluded_sentences_improper_length,
                        exclude_phrase,
                    )

        if not is_proper_noun_ratio_correct(proper_noun_count, tokens):
            (
                excluded_ratios,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_ratios, exclude_phrase
            )
        elif line_does_not_contain_verb_and_verbs_required(
            verb_token_present, args.verb, exclude_phrase
        ):
            (
                excluded_verbs,
                exclude_phrase,
            ) = add_line_to_exclusion_list_and_set_exclude_phrase_bool_to_true(
                original_phrase, excluded_verbs, exclude_phrase
            )

        if not exclude_phrase:
            if is_multiple_periods_in_sentence(line):
                if ".." in line:
                    line = correctly_format_elipses(line)
                else:
                    excluded_abbreviations.append(original_phrase)
            else:
                line = fix_apostrophes(line)
                line = fix_quotation_marks(line)
                if not line_ends_with_punctuation(line):
                    line = clean_up_sentence_end(line)
                line = replace_multiple_punctuation_marks_with_single_punctuation_mark(
                    line
                )
                line = clean_up_sentence_beginning(line)
                if line not in selected_phrases:
                    selected_phrases.append(line)
                    selected_phrases_orig.append(original_phrase)
                else:
                    selected_phrases_repeated.append(line)

    create_output_dir_if_not_exists(output_dir)

    total = len(sentences)
    statistics = [
        "línies inici: " + str(total_lines),
        "frases inici: " + str(total),
        describe("excloses mida:", excluded_sentences_improper_length, total),
        describe("excloses caracter:", excluded_characters, total),
        describe("excloses sigles:", excluded_acronyms, total),
        describe("excloses paraules:", excluded_words, total),
        describe("excloses ortografia:", excluded_spellings, total),
        describe("excloses proporció:", excluded_ratios, total),
        describe("excloses hores:", excluded_hours, total),
        describe("excloses paraules repetides:", excluded_repeated_words, total),
        describe("excloses noms:", excluded_names, total),
        describe("seleccionades repetides:", selected_phrases_repeated, total),
        describe("seleccionades:", selected_phrases, total),
        describe("abreviatures:", excluded_abbreviations, total),
        describe("possibles trencades:", possible_breaks, total),
        describe("comença amb min:", excluded_lowercase, total),
        describe("conté una xifra:", excluded_nums, total),
        describe("excloses verb:", excluded_verbs, total),
        describe("error num:", error_num, total),
    ]
    for line in statistics:
        print(line)

    all_exclusion_lists = [
        selected_options + ["---------"] + statistics,
        selected_phrases,
        excluded_sentences_improper_length,
        excluded_characters,
        excluded_acronyms,
        excluded_words,
        excluded_spellings,
        excluded_ratios,
        excluded_hours,
        excluded_repeated_words,
        excluded_names,
        selected_phrases_repeated,
        error_num,
        possible_breaks,
        excluded_abbreviations,
        excluded_lowercase,
        excluded_nums,
        excluded_verbs,
        selected_phrases_orig,
    ]
    all_exclusion_list_files = [
        "estadistiques_filtre.txt",
        "frases_seleccionades.txt",
        "excloses_mida.txt",
        "excloses_caracter.txt",
        "excloses_sigles.txt",
        "excloses_paraula.txt",
        "excloses_ortografia.txt",
        "excloses_proporcio.txt",
        "excloses_hores.txt",
        "excloses_paraules_repetides.txt",
        "excloses_nom.txt",
        "frases_seleccionades_repetides.txt",
        "error_num.txt",
        "possibles_trencades.txt",
        "excloses_abreviatura.txt",
        "excloses_minuscula.txt",
        "excloses_num.txt",
        "excloses_verb.txt",
        "frases_seleccionades_originals.txt",
    ]
    for exclusion_list, file in zip(all_exclusion_lists, all_exclusion_list_files):
        create_file(output_dir, filter_file_name, file, exclusion_list)

    case_studies_files = [
        output_dir / f"{filter_file_name}_estudi_cas_filtre.tsv",
        output_dir / f"{filter_file_name}_estudi_cas_ortografia.tsv",
    ]
    all_case_studies = [case_studies, spelling_case_studies]

    for case_studies_file, case_study in zip(case_studies_files, all_case_studies):
        create_case_studies_file(case_studies_file, case_study)


if __name__ == "__main__":
    main()
