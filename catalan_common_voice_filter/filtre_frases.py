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
    excluded_words = []
    if excluded_words_list_file:
        excluded_words_list_file = Path(excluded_words_list_file)
        with open(excluded_words_list_file, "r") as f:
            excluded_words = f.read().splitlines()

    return excluded_words


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
    excluded_words = create_excluded_words_list(args.list)
    sentences, total_lines = split_filter_file_into_sentences(file_to_filter)

    # here are the lists where the sentences are saved depending on whether they are discarded or not
    tokens_descartats = []
    frases_seleccionades = []
    frases_seleccionades_orig = []
    frases_seleccionades_repetides = []
    excluded_caracter = []
    excluded_ortografia = []
    excluded_proporcio = []
    excluded_mida = []
    excluded_sigles = []
    excluded_paraula = []
    excluded_repeated_words = []
    excluded_nom = []
    error_num = []
    excluded_abreviatura = []
    excluded_hora = []
    possibles_trencades = []
    estudi_cas = []
    estudi_cas_ortografia = []
    excluded_min = []
    excluded_num = []
    excluded_verb = []

    for line in sentences:
        count = 0
        exclou_frase = False
        frase_orig = line
        if len(line) > 4:
            if line[0] not in QUOTATION_MARKS:
                while (
                    not line[0].isalpha() and len(line) > 4
                ):  # clean up the rubbish at the beginning of the sentence
                    line = line[1:]

            if (
                line[0].islower() and args.capitals == True
            ):  # check if line starts with a capital letter
                excluded_min.append(frase_orig)
                exclou_frase = True
            else:
                if (
                    line[-1] not in SENTENCE_END_CHARS and args.punctuation == True
                ):  # check that line has a final score
                    possibles_trencades.append(frase_orig)
                    exclou_frase = True
                else:
                    if re.search(REPEATED_WORDS, line) == None:
                        if args.proper_nouns == True and find_names(line):
                            exclou_frase = True
                            excluded_nom.append(frase_orig)
                        else:
                            line = re.sub(
                                r" \([A-Úa-ú0-9 -\.\,]*\)", "", line
                            )  # clean up what's in parentheses
                            if (
                                any(
                                    element in line
                                    for element in PUNCTUATION_TO_EXCLUDE
                                )
                                == False
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
                                        excluded_num.append(frase_orig)
                                        exclou_frase = True
                                    else:
                                        trossos = line.split(
                                            " "
                                        )  # we do a simple first tokenization
                                        if (
                                            len(trossos) >= 4 and len(trossos) <= 18
                                        ):  # count the number of tokens
                                            if (
                                                trossos[-1]
                                                not in INCORRECT_SENTENCE_END_WORDS
                                            ):  # make sure line doesn't end badly
                                                # first selection process ends here
                                                tokens = nlp(
                                                    line
                                                )  # tokenize with spacy
                                                te_verb = False

                                                for token in tokens:
                                                    if (
                                                        token.pos_ == "VERB"
                                                        or token.pos_ == "AUX"
                                                    ):
                                                        te_verb = True
                                                    if (
                                                        token.text.lower()
                                                        in REPLACEMENT_WORDS.keys()
                                                    ):  # develop some abbreviations
                                                        line = line.replace(
                                                            token.text,
                                                            REPLACEMENT_WORDS[
                                                                token.text.lower()
                                                            ],
                                                        )

                                                    else:
                                                        if token.text.isalpha():
                                                            if len(token) == 1:
                                                                if (
                                                                    token.text.lower()
                                                                    in [
                                                                        "a",
                                                                        "e",
                                                                        "i",
                                                                        "o",
                                                                        "u",
                                                                        "l",
                                                                        "d",
                                                                        "p",
                                                                    ]
                                                                ):
                                                                    pass
                                                                else:  # if it is a single consonant, exclude the sentence
                                                                    exclou_frase = True
                                                                    excluded_ortografia.append(
                                                                        frase_orig
                                                                    )
                                                                    estudi_cas_ortografia.append(
                                                                        [
                                                                            frase_orig,
                                                                            token.text,
                                                                        ]
                                                                    )
                                                                    break
                                                            elif token.text.isupper():
                                                                exclou_frase = True
                                                                excluded_sigles.append(
                                                                    frase_orig
                                                                )
                                                                break
                                                            elif (
                                                                token.text
                                                                in excluded_words
                                                            ):  # if it's on the list of forbidden words, exclude the phrase
                                                                exclou_frase = True
                                                                excluded_paraula.append(
                                                                    frase_orig
                                                                )
                                                                estudi_cas.append(
                                                                    [
                                                                        frase_orig,
                                                                        token.text,
                                                                    ]
                                                                )
                                                                break

                                                            elif not dic.spell(
                                                                token.text
                                                            ):
                                                                if (
                                                                    token.text[
                                                                        0
                                                                    ].islower()
                                                                    and token.text
                                                                    != "ls"
                                                                ):  # if it doesn't start with a capital letter and isn't in the dictionary, we exclude the phrase
                                                                    exclou_frase = True
                                                                    excluded_ortografia.append(
                                                                        frase_orig
                                                                    )
                                                                    estudi_cas_ortografia.append(
                                                                        [
                                                                            frase_orig,
                                                                            token.text,
                                                                        ]
                                                                    )
                                                                    tokens_descartats.append(
                                                                        token.text
                                                                    )
                                                                    break
                                                                elif token.text[
                                                                    0
                                                                ].isupper():
                                                                    count += 1

                                                        if any(
                                                            element in token.text
                                                            for element in NUMBERS
                                                        ):  # if there is any figure
                                                            try:  # try to transcribe it
                                                                transcrip = (
                                                                    nums.llegeix_nums(
                                                                        token.text
                                                                    )
                                                                )
                                                                line = line.replace(
                                                                    token.text,
                                                                    transcrip,
                                                                    1,
                                                                )
                                                            except:  # if we can't
                                                                if (
                                                                    token.text[-1]
                                                                    == "h"
                                                                ):  # see if word ends in 'h' and try again
                                                                    try:
                                                                        transcrip = (
                                                                            nums.llegeix_nums(
                                                                                token.text[
                                                                                    :-1
                                                                                ]
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
                                                                            frase_orig
                                                                        )
                                                                        exclou_frase = (
                                                                            True
                                                                        )
                                                                        break
                                                                else:  # mark as an error
                                                                    error_num.append(
                                                                        frase_orig
                                                                    )
                                                                    exclou_frase = True
                                                                    break
                                                            if (
                                                                exclou_frase == False
                                                                and len(line.split(" "))
                                                                >= 18
                                                            ):  # check sentence has not become too long
                                                                excluded_mida.append(
                                                                    frase_orig
                                                                )
                                                                exclou_frase = True
                                                if count >= len(trossos) / 3:
                                                    exclou_frase = True
                                                    excluded_proporcio.append(
                                                        frase_orig
                                                    )
                                                else:
                                                    if (
                                                        te_verb == False
                                                        and args.verb == True
                                                        and exclou_frase == False
                                                    ):  # if it doesn't have a verb and we've made it a requirement and the sentence hasn't been deleted before, delete the sentence
                                                        exclou_frase = True
                                                        excluded_verb.append(frase_orig)
                                            else:
                                                exclou_frase = True
                                                possibles_trencades.append(frase_orig)
                                        else:
                                            exclou_frase = True
                                            excluded_mida.append(frase_orig)
                                else:
                                    exclou_frase = True
                                    excluded_hora.append(frase_orig)
                            else:
                                exclou_frase = True
                                excluded_caracter.append(frase_orig)
                    else:
                        exclou_frase = True
                        excluded_repeated_words.append(frase_orig)
        else:
            exclou_frase = True
            excluded_mida.append(frase_orig)

        if exclou_frase == False:
            if "." in line[:-2]:  # check that there is no period left in the sentence
                if ".." in line:
                    line = re.sub("\.(\.)+", "...", line)
                else:
                    excluded_abreviatura.append(frase_orig)
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
                if line not in frases_seleccionades:
                    frases_seleccionades.append(line)
                    frases_seleccionades_orig.append(frase_orig)
                else:
                    frases_seleccionades_repetides.append(line)

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
        descriu("excloses mida:", excluded_mida, total),
        descriu("excloses caracter:", excluded_caracter, total),
        descriu("excloses sigles:", excluded_sigles, total),
        descriu("excloses paraules:", excluded_paraula, total),
        descriu("excloses ortografia:", excluded_ortografia, total),
        descriu("excloses proporció:", excluded_proporcio, total),
        descriu("excloses hores:", excluded_hora, total),
        descriu("excloses paraules repetides:", excluded_repeated_words, total),
        descriu("excloses noms:", excluded_nom, total),
        descriu("seleccionades repetides:", frases_seleccionades_repetides, total),
        descriu("seleccionades:", frases_seleccionades, total),
        descriu("abreviatures:", excluded_abreviatura, total),
        descriu("possibles trencades:", possibles_trencades, total),
        descriu("comença amb min:", excluded_min, total),
        descriu("conté una xifra:", excluded_num, total),
        descriu("excloses verb:", excluded_verb, total),
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
        output_dir, filter_file_name, "frases_seleccionades.txt", frases_seleccionades
    )
    create_file(output_dir, filter_file_name, "excloses_mida.txt", excluded_mida)
    create_file(
        output_dir, filter_file_name, "excloses_caracter.txt", excluded_caracter
    )
    create_file(output_dir, filter_file_name, "excloses_sigles.txt", excluded_sigles)
    create_file(output_dir, filter_file_name, "excloses_paraula.txt", excluded_paraula)
    create_file(
        output_dir, filter_file_name, "excloses_ortografia.txt", excluded_ortografia
    )
    create_file(
        output_dir, filter_file_name, "excloses_proporcio.txt", excluded_proporcio
    )
    create_file(output_dir, filter_file_name, "excloses_hores.txt", excluded_hora)
    create_file(
        output_dir,
        filter_file_name,
        "excloses_paraules_repetides.txt",
        excluded_repeated_words,
    )
    create_file(output_dir, filter_file_name, "excloses_nom.txt", excluded_nom)
    create_file(
        output_dir,
        filter_file_name,
        "frases_seleccionades_repetides.txt",
        frases_seleccionades_repetides,
    )
    create_file(output_dir, filter_file_name, "error_num.txt", error_num)
    create_file(
        output_dir, filter_file_name, "possibles_trencades.txt", possibles_trencades
    )
    create_file(
        output_dir, filter_file_name, "excloses_abreviatura.txt", excluded_abreviatura
    )
    create_file(output_dir, filter_file_name, "excloses_minuscula.txt", excluded_min)
    create_file(output_dir, filter_file_name, "excloses_num.txt", excluded_num)
    create_file(output_dir, filter_file_name, "excloses_verb.txt", excluded_verb)
    create_file(
        output_dir,
        filter_file_name,
        "frases_seleccionades_originals.txt",
        frases_seleccionades_orig,
    )

    new_file = output_dir / f"{filter_file_name}_estudi_cas_filtre.tsv"
    with open(new_file, "w") as f:
        for frase in estudi_cas:
            f.writelines(frase[1] + "\t" + frase[0] + "\n")

    new_file = output_dir / f"{filter_file_name}_estudi_cas_ortografia.tsv"
    with open(new_file, "w") as f:
        for frase in estudi_cas_ortografia:
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
