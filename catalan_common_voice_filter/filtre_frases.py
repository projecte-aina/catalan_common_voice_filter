import os
import re
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Union

import hunspell
import spacy
import unidecode
from sentence_splitter import SentenceSplitter

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


def descriu(descriptor, llista, total):
    text = (
        descriptor
        + " "
        + str(len(llista))
        + " ("
        + str(round(len(llista) * 100 / total, 2))
        + "%)"
    )
    return text


def create_file(output_dir, filter_file_name, myfile, mylist):
    mylist.sort()

    os.makedirs(output_dir, exist_ok=True)
    new_file = output_dir / f"{filter_file_name}_{myfile}"
    with open(new_file, "w") as f:
        for frase in mylist:
            f.writelines(frase + "\n")


def find_names(line):
    possibles_noms = re.compile(r"[A-Z][a-ü]+ ([Dd][\'e](l)?)? ?[A-Z][a-ü]*")
    busca_noms = re.search(possibles_noms, line)

    if busca_noms != None:
        possible_nom = busca_noms.group(0)
        possible_cognom = possible_nom[possible_nom.index(" ") + 1 :]
        if unidecode.unidecode(possible_cognom) in cognoms:
            if (
                busca_noms.span()[0] == 0
                and len(busca_noms.group(0).split(" ")[0]) <= 2
            ):
                return False
            else:
                return True
        else:
            return False
    else:
        return False


def fix_quotation_marks(text):
    text = re.sub(
        r"([nldNLD])’(h?[aeiouAEIOUàèéíòóúÀÈÉÍÒÓÚ])", r"\1'\2", text
    )  # fix apostrophes
    text = re.sub(
        r"([aeiouAEIOUàèéíòóú])’([nldNLD])", r"\1'\2", text
    )  # fix apostrophes
    text = re.sub(
        r"([aeiouAEIOUàèéíòóúnldNLD])' (h?[aeiouAEIOUàèéíòóúnldNLD])", r"\1'\2", text
    )  # fix apostrophes
    if text[0] in QUOTATION_MARKS:
        if any(quotation_mark in text[1:] for quotation_mark in QUOTATION_MARKS):
            pass
        else:
            text = text[1:]
    elif any(quotation_mark in text[1:] for quotation_mark in QUOTATION_MARKS):
        countc = 0
        for c in text[1:]:
            if c in QUOTATION_MARKS:
                countc += 1
        if countc % 2 != 0:
            for c in text[1:]:
                if c in QUOTATION_MARKS:
                    text = text.replace(c, "")
    return text


def store_and_print_selected_options(
    args: Namespace, filter_file_name: str
) -> List[str]:
    selected_options = [
        "* File: " + filter_file_name + "\n",
        "* Opcions seleccionades:",
    ]
    print(*selected_options)

    if args.punctuation == True:
        text = "- Només frases amb marques de finals"
        print(text)
        selected_options.append(text)
    if args.numbers == True:
        text = "- S'eliminen les frases amb xifres"
        print(text)
        selected_options.append(text)
    if args.verb == True:
        text = "- Només frases amb verbs"
        print(text)
        selected_options.append(text)
    if args.capitals == True:
        text = "- Només frases que comencen amb majúscula"
        print(text)
        selected_options.append(text)
    if args.proper_nouns == True:
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
        excluded_words_list_file = Path(excluded_words_list_file)
        with open(excluded_words_list_file, "r") as f:
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


def check_if_line_starts_with_lowercase_letter(
    line: str,
    original_phrase: str,
    only_allow_capitalized_sentences: bool,
    excluded_min: List[str],
    exclude_phrase: bool,
) -> Tuple[List[str], bool]:
    if line[0].islower() and only_allow_capitalized_sentences:
        excluded_min.append(original_phrase)
        exclude_phrase = True

    return excluded_min, exclude_phrase


def check_if_line_ends_with_punctuation(
    line: str,
    original_phrase: str,
    only_allow_punctuation: bool,
    possible_breaks: List[str],
    exclude_phrase: bool,
) -> Tuple[List[str], bool]:
    if line[-1] not in SENTENCE_END_CHARS and only_allow_punctuation == True:
        possible_breaks.append(original_phrase)
        exclude_phrase = True

    return possible_breaks, exclude_phrase


def are_words_repeated(line: str):
    if not re.search(REPEATED_WORDS, line.lower()):
        return False

    return True


def main():
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

    dic = hunspell.HunSpell("data/ca.dic", "data/ca.aff")

    file_to_filter = Path(args.file_to_filter)
    filter_file_name = file_to_filter.stem

    selected_options = store_and_print_selected_options(args, filter_file_name)
    output_dir = create_output_directory_path(args.dir, file_to_filter)
    words_to_exclude = create_excluded_words_list(args.list)
    sentences, total_lines = split_filter_file_into_sentences(file_to_filter)

    # here are the lists where the sentences are saved depending on whether they are discarded or not
    discarded_tokens = []
    selected_phrases = []
    selected_phrases_orig = []
    selected_phrases_repeated = []
    excluded_characters = []
    excluded_spellings = []
    excluded_ratios = []
    excluded_sentences_improper_length = []
    excluded_acronyms = []
    excluded_words = []
    excluded_repeated_words = []
    excluded_names = []
    error_num = []
    excluded_abbreviations = []
    excluded_hours = []
    possible_breaks = []
    case_studies = []
    spelling_case_studies = []
    excluded_min = []
    excluded_num = []
    excluded_verbs = []

    for line in sentences:
        count = 0
        exclude_phrase = False
        original_phrase = line
        if is_line_length_correct(line):
            line = remove_unnecessary_characters(line)
            excluded_min, exclude_phrase = check_if_line_starts_with_lowercase_letter(
                line, original_phrase, args.capitals, excluded_min, exclude_phrase
            )
            possible_breaks, exclude_phrase = check_if_line_ends_with_punctuation(
                line, original_phrase, args.punctuation, possible_breaks, exclude_phrase
            )
            if are_words_repeated(line):
                exclude_phrase = True
                excluded_repeated_words.append(original_phrase)
                continue

            if args.proper_nouns == True and find_names(line):
                exclude_phrase = True
                excluded_names.append(original_phrase)
            else:
                line = re.sub(
                    r" \([A-Úa-ú0-9 -\.\,]*\)", "", line
                )  # clean up what's in parentheses
                if (
                    any(element in line for element in PUNCTUATION_TO_EXCLUDE) == False
                    and re.search(r"\.[a-zA-Z]", line) == None
                    and re.search(EMOJIS, line) == None
                    and line[-1] != ":"
                    and " - " not in line
                ):
                    # check that there are no punctuation marks in the middle, emojis or endings in:
                    if (
                        re.search(HOURS, line) == None
                    ):  # we check that there are no time expressions
                        if args.numbers == True and any(
                            element in line for element in NUMBERS
                        ):
                            # check if there are numbers
                            excluded_num.append(original_phrase)
                            exclude_phrase = True
                        else:
                            trossos = line.split(
                                " "
                            )  # we do a simple first tokenization
                            if (
                                len(trossos) >= 4 and len(trossos) <= 18
                            ):  # count the number of tokens
                                if (
                                    trossos[-1] not in INCORRECT_SENTENCE_END_WORDS
                                ):  # make sure line doesn't end badly
                                    # first selection process ends here
                                    tokens = nlp(line)  # tokenize with spacy
                                    te_verb = False

                                    for token in tokens:
                                        if token.pos_ == "VERB" or token.pos_ == "AUX":
                                            te_verb = True
                                        if (
                                            token.text.lower()
                                            in REPLACEMENT_WORDS.keys()
                                        ):  # develop some abbreviations
                                            line = line.replace(
                                                token.text,
                                                REPLACEMENT_WORDS[token.text.lower()],
                                            )

                                        else:
                                            if token.text.isalpha():
                                                if len(token) == 1:
                                                    if token.text.lower() in [
                                                        "a",
                                                        "e",
                                                        "i",
                                                        "o",
                                                        "u",
                                                        "l",
                                                        "d",
                                                        "p",
                                                    ]:
                                                        pass
                                                    else:  # if it is a single consonant, exclude the sentence
                                                        exclude_phrase = True
                                                        excluded_spellings.append(
                                                            original_phrase
                                                        )
                                                        spelling_case_studies.append(
                                                            [
                                                                original_phrase,
                                                                token.text,
                                                            ]
                                                        )
                                                        break
                                                elif token.text.isupper():
                                                    exclude_phrase = True
                                                    excluded_acronyms.append(
                                                        original_phrase
                                                    )
                                                    break
                                                elif (
                                                    token.text in words_to_exclude
                                                ):  # if it's on the list of forbidden words, exclude the phrase
                                                    exclude_phrase = True
                                                    excluded_words.append(
                                                        original_phrase
                                                    )
                                                    case_studies.append(
                                                        [
                                                            original_phrase,
                                                            token.text,
                                                        ]
                                                    )
                                                    break

                                                elif not dic.spell(token.text):
                                                    if (
                                                        token.text[0].islower()
                                                        and token.text != "ls"
                                                    ):  # if it doesn't start with a capital letter and isn't in the dictionary, we exclude the phrase
                                                        exclude_phrase = True
                                                        excluded_spellings.append(
                                                            original_phrase
                                                        )
                                                        spelling_case_studies.append(
                                                            [
                                                                original_phrase,
                                                                token.text,
                                                            ]
                                                        )
                                                        discarded_tokens.append(
                                                            token.text
                                                        )
                                                        break
                                                    elif token.text[0].isupper():
                                                        count += 1

                                            if any(
                                                element in token.text
                                                for element in NUMBERS
                                            ):  # if there is any figure
                                                try:  # try to transcribe it
                                                    transcrip = nums.llegeix_nums(
                                                        token.text
                                                    )
                                                    line = line.replace(
                                                        token.text,
                                                        transcrip,
                                                        1,
                                                    )
                                                except:  # if we can't
                                                    if (
                                                        token.text[-1] == "h"
                                                    ):  # see if word ends in 'h' and try again
                                                        try:
                                                            transcrip = (
                                                                nums.llegeix_nums(
                                                                    token.text[:-1]
                                                                )
                                                                + " hores"
                                                            )
                                                            line = line.replace(
                                                                token.text,
                                                                transcrip,
                                                                1,
                                                            )

                                                        except:  # if it can't be transcribed, discard it
                                                            error_num.append(
                                                                original_phrase
                                                            )
                                                            exclude_phrase = True
                                                            break
                                                    else:  # mark as an error
                                                        error_num.append(
                                                            original_phrase
                                                        )
                                                        exclude_phrase = True
                                                        break
                                                if (
                                                    exclude_phrase == False
                                                    and len(line.split(" ")) >= 18
                                                ):  # check sentence has not become too long
                                                    excluded_sentences_improper_length.append(
                                                        original_phrase
                                                    )
                                                    exclude_phrase = True
                                    if count >= len(trossos) / 3:
                                        exclude_phrase = True
                                        excluded_ratios.append(original_phrase)
                                    else:
                                        if (
                                            te_verb == False
                                            and args.verb == True
                                            and exclude_phrase == False
                                        ):  # if it doesn't have a verb and we've made it a requirement and the sentence hasn't been deleted before, delete the sentence
                                            exclude_phrase = True
                                            excluded_verbs.append(original_phrase)
                                else:
                                    exclude_phrase = True
                                    possible_breaks.append(original_phrase)
                            else:
                                exclude_phrase = True
                                excluded_sentences_improper_length.append(
                                    original_phrase
                                )
                    else:
                        exclude_phrase = True
                        excluded_hours.append(original_phrase)
                else:
                    exclude_phrase = True
                    excluded_characters.append(original_phrase)
        else:
            exclude_phrase = True
            excluded_sentences_improper_length.append(original_phrase)

        if exclude_phrase == False:
            if "." in line[:-2]:  # check that there is no period left in the sentence
                if ".." in line:
                    line = re.sub("\.(\.)+", "...", line)
                else:
                    excluded_abbreviations.append(original_phrase)
            else:  # once the sentences have been selected, make the arrangements
                line = fix_quotation_marks(line)
                if line[-1] not in SENTENCE_END_CHARS:
                    if line[-1] == ",":
                        line = line[:-1]
                    line = line + "."
                line = re.sub(r"([\?\!])\.", "\\1", line)
                line = re.sub(r"\!+", "!", line)
                line = re.sub(r"\?+", "?", line)
                if line[0] == " ":
                    line = line[1:]
                if line[0].islower():
                    line = line[0].upper() + line[1:]
                if line not in selected_phrases:
                    selected_phrases.append(line)
                    selected_phrases_orig.append(original_phrase)
                else:
                    selected_phrases_repeated.append(line)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        print("Hem creat el directori", output_dir)
    else:
        print("El directori", output_dir, "ja existeix")

    # stats
    total = len(sentences)
    statistics = [
        "línies inici: " + str(total_lines),
        "frases inici: " + str(total),
        descriu("excloses mida:", excluded_sentences_improper_length, total),
        descriu("excloses caracter:", excluded_characters, total),
        descriu("excloses sigles:", excluded_acronyms, total),
        descriu("excloses paraules:", excluded_words, total),
        descriu("excloses ortografia:", excluded_spellings, total),
        descriu("excloses proporció:", excluded_ratios, total),
        descriu("excloses hores:", excluded_hours, total),
        descriu("excloses paraules repetides:", excluded_repeated_words, total),
        descriu("excloses noms:", excluded_names, total),
        descriu("seleccionades repetides:", selected_phrases_repeated, total),
        descriu("seleccionades:", selected_phrases, total),
        descriu("abreviatures:", excluded_abbreviations, total),
        descriu("possibles trencades:", possible_breaks, total),
        descriu("comença amb min:", excluded_min, total),
        descriu("conté una xifra:", excluded_num, total),
        descriu("excloses verb:", excluded_verbs, total),
        descriu("error num:", error_num, total),
    ]
    for line in statistics:
        print(line)

    create_file(
        output_dir,
        filter_file_name,
        "estadistiques_filtre.txt",
        selected_options + ["---------"] + statistics,
    )
    create_file(
        output_dir, filter_file_name, "frases_seleccionades.txt", selected_phrases
    )
    create_file(
        output_dir,
        filter_file_name,
        "excloses_mida.txt",
        excluded_sentences_improper_length,
    )
    create_file(
        output_dir, filter_file_name, "excloses_caracter.txt", excluded_characters
    )
    create_file(output_dir, filter_file_name, "excloses_sigles.txt", excluded_acronyms)
    create_file(output_dir, filter_file_name, "excloses_paraula.txt", excluded_words)
    create_file(
        output_dir, filter_file_name, "excloses_ortografia.txt", excluded_spellings
    )
    create_file(output_dir, filter_file_name, "excloses_proporcio.txt", excluded_ratios)
    create_file(output_dir, filter_file_name, "excloses_hores.txt", excluded_hours)
    create_file(
        output_dir,
        filter_file_name,
        "excloses_paraules_repetides.txt",
        excluded_repeated_words,
    )
    create_file(output_dir, filter_file_name, "excloses_nom.txt", excluded_names)
    create_file(
        output_dir,
        filter_file_name,
        "frases_seleccionades_repetides.txt",
        selected_phrases_repeated,
    )
    create_file(output_dir, filter_file_name, "error_num.txt", error_num)
    create_file(
        output_dir, filter_file_name, "possibles_trencades.txt", possible_breaks
    )
    create_file(
        output_dir, filter_file_name, "excloses_abreviatura.txt", excluded_abbreviations
    )
    create_file(output_dir, filter_file_name, "excloses_minuscula.txt", excluded_min)
    create_file(output_dir, filter_file_name, "excloses_num.txt", excluded_num)
    create_file(output_dir, filter_file_name, "excloses_verb.txt", excluded_verbs)
    create_file(
        output_dir,
        filter_file_name,
        "frases_seleccionades_originals.txt",
        selected_phrases_orig,
    )

    new_file = output_dir / f"{filter_file_name}_estudi_cas_filtre.tsv"
    with open(new_file, "w") as f:
        for frase in case_studies:
            f.writelines(frase[1] + "\t" + frase[0] + "\n")

    new_file = output_dir / f"{filter_file_name}_estudi_cas_ortografia.tsv"
    with open(new_file, "w") as f:
        for frase in spelling_case_studies:
            f.writelines(frase[1] + "\t" + frase[0] + "\n")


if __name__ == "__main__":
    nlp = spacy.load(
        "ca_core_news_sm", exclude=["parser", "attribute_ruler", "lemmatizer", "ner"]
    )

    cognoms_tots = open("data/cognoms_list.txt", "r").read().splitlines()
    cognoms = []
    for cognom in cognoms_tots:
        if len(cognom) >= 3:
            cognoms.append(cognom)
    sys.exit(main())
