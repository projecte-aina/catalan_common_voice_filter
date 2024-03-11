import os
import re
import sys
from datetime import datetime
from optparse import OptionParser

import hunspell
import spacy
import unidecode
from sentence_splitter import SentenceSplitter


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


def create_file(path, nom, myfile, mylist):
    os.makedirs(path, exist_ok=True)
    newfile = open(path + nom + "_" + myfile, "w")
    mylist.sort()
    for frase in mylist:
        newfile.writelines(frase + "\n")
    newfile.close()


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


def fix_quotation_marks(text, cometes):
    text = re.sub(
        r"([nldNLD])’(h?[aeiouAEIOUàèéíòóúÀÈÉÍÒÓÚ])", r"\1'\2", text
    )  # fix apostrophes
    text = re.sub(
        r"([aeiouAEIOUàèéíòóú])’([nldNLD])", r"\1'\2", text
    )  # fix apostrophes
    text = re.sub(
        r"([aeiouAEIOUàèéíòóúnldNLD])' (h?[aeiouAEIOUàèéíòóúnldNLD])", r"\1'\2", text
    )  # fix apostrophes
    if text[0] in cometes:
        if any(cometa in text[1:] for cometa in cometes):
            pass
        else:
            text = text[1:]
    elif any(cometa in text[1:] for cometa in cometes):
        countc = 0
        for c in text[1:]:
            if c in cometes:
                countc += 1
        if countc % 2 != 0:
            for c in text[1:]:
                if c in cometes:
                    text = text.replace(c, "")
    return text


def main(argv=None):
    parser = OptionParser()
    parser.add_option(
        "-f", "--file", dest="file", action="store", help="fitxer que es vol filtrar"
    )
    parser.add_option(
        "-l",
        "--list",
        dest="list",
        action="store",
        help="llista de paraules que es volen eliminar",
    )
    parser.add_option(
        "-d",
        "--dir",
        dest="dir",
        action="store",
        help="directori on es desaran els resultats",
    )
    parser.add_option(
        "-x",
        "--num",
        dest="num",
        action="store_true",
        help="no es transcriuen els números",
        default=False,
    )
    parser.add_option(
        "-v",
        "--verb",
        dest="verb",
        action="store_true",
        help="només frases amb verbs",
        default=False,
    )
    parser.add_option(
        "-p",
        "--punt",
        dest="punt",
        action="store_true",
        help="només frases amb marques de finals",
        default=False,
    )
    parser.add_option(
        "-m",
        "--cap",
        dest="cap",
        action="store_true",
        help="només frases que comencen amb majúscules",
        default=False,
    )
    parser.add_option(
        "-n",
        "--pnom",
        dest="pnom",
        action="store_true",
        help="exclou frases amb possibles noms propis",
        default=False,
    )

    (options, _) = parser.parse_args(argv)

    dic = hunspell.HunSpell("data/ca.dic", "data/ca.aff")

    file = options.file
    nom = file.split("/")[-1][:-4]

    opcions_seleccionades = ["* File: " + nom + "\n", "* Opcions seleccionades:"]

    if options.punt == True:
        text = "- Només frases amb marques de finals"
        print(text)
        opcions_seleccionades.append(text)
    if options.num == True:
        text = "- S'eliminen les frases amb xifres"
        print(text)
        opcions_seleccionades.append(text)
    if options.verb == True:
        text = "- Només frases amb verbs"
        print(text)
        opcions_seleccionades.append(text)
    if options.cap == True:
        text = "- Només frases que comencen amb majúscula"
        print(text)
        opcions_seleccionades.append(text)
    if options.pnom == True:
        text = "- Exclou frases amb possibles noms"
        print(text)
        opcions_seleccionades.append(text)

    if options.dir:
        if options.dir[-1] == "/":
            path = options.dir
        else:
            path = options.dir + "/"
    else:
        if "/" in file:
            oldPath = file[: file.rfind("/")] + "/"
        else:
            oldPath = ""
        path = (
            oldPath
            + "resulats_filtre_"
            + nom
            + "_"
            + datetime.now().strftime("%Y%m%d_%H%M")
            + "/"
        )

    if options.list:
        paraules_excluded = (
            open(options.list, "r").read().splitlines()
        )  # used if the user wishes to filter some words out
    else:
        paraules_excluded = []

    lines = open(file, "r").readlines()

    splitter = SentenceSplitter(language="ca")
    sentences = []
    countl = 0
    for l in lines:
        countl += 1
        frases = splitter.split(l)
        for frase in frases:
            parts = frase.split(":")
            sentences.append(parts[-1])

    puntuacio = [
        "|",
        "[",
        "]",
        "(",
        ")",
        "@",
        "#",
        "$",
        "&",
        "*",
        "+",
        "{",
        "}",
        "/",
        "=",
        "®",
        ">",
        "<",
        "≤",
        "–",
        "©",
    ]  # characters to exclude from sentences
    nombres = [str(i) for i in range(10)]  # numbers
    ultim = [".", "!", "?", '"', "'"]  # characters that indicate the end of a sentence
    emojis = re.compile(r"[\u263a-\U0001f645]")  # emojis
    repeated_words = re.compile(r"\b(\w+)\b\s+(\1)\b")
    hores = re.compile(r"[0-2]?[0-9](:|\.)[0-5][0-9](?![0-9])")  # hours
    mal_final = [
        "els",
        "el",
        "la",
        "les",
        "a",
        "en",
        "de",
        "que",
        "què",
        "mitjançant",
        "del",
        "dels",
        "al",
        "als",
        "es",
        "per",
        "i",
        "amb",
        "hem",
        "ha",
        "he",
        "has",
        "heu",
        "qual",
        "han",
        "són",
        "com",
    ]  # words that should not end a sentence
    reemplacos = {
        "’": "'",  # these replacements are done at the beginning
        "%": "per cent",
        "€": "euros",
        "sr.": "senyor",
        "dr.": "doctor",
        "sra.": "senyora",
        "dra.": "doctora",
        "st.": "Sant",
        "sta.": "Santa",
        "num.": "número ",
        "núm ": "número ",
        "núm.": "número",
        "vol.": "Volum ",
        "km.": "quilòmetres",
        "c.": " carrer",  # càrrec
        "c/": "carrer",
        "pl.": "plaça ",
        "Pl.": "Plaça ",
        "pag.": "pàgina",
        "pàg.": "pàgina",
        "p.": " pàgina",
        "ed.": "editorial",
        "h.": "hores",
        "av.": "avinguda",
        "hable.": "Honorable",
        "hble.": "honorable",
        "etc.": "etcètera",
        "pral.": "principal",
        "jr.": "júnior",
        "ptes.": " pessetes",  # aptes
        "covid-19": "Covid dinou",
        "ha.": "hectàrees",
        "veg.": "vegeu",
        "sr": "senyor",
        "dr": "doctor",
        "sra": "senyora",
        "dra": "doctora",
        "st": "Sant",
        "sta": "Santa",
        "num ": "número ",
        "núm": "número ",
        "km": "quilòmetres",
        "kv": "quilovolts",
        "kw": "quilowatts",
        "pag": "pàgina",
        "pàg": "pàgina",
        "av": "avinguda",
        "hable": "Honorable",
        "hble": "honorable",
        "ptes": "pessetes",
        "1r": "primer",
        "1a": "primera",
        "2n": "segon",
        "2a": "segona",
        "3r": "tercera",
        "4t": "quart",
        "4a": "quarta",
        "5è": "cinquè",
        "5ena": "cinquena",
        "iban": "Iban",
        "ibex": "Ibex",
        "eeuu": "Estats Units",
        "eua": "Estats Units",
        "eu": "Unió Europea",
        "ue": "Unió Europea",
        "nie": "Nie",
        "erc": "Esquerra Republicana de Catalunya",
        "ciu": "Convergiència i Unió",
        "psoe": "Partit Socialista Espanyol",
        "pp": "Partit Popular",
        "cup": "Cup",
        "psc": "Partit Socialista de Catalunya",
        "ccoo": "Comissions Obreres",
        "ampa": "associació de mares i pares d'alumnes",
        "ampas": "associacions de mares i pares d'alumnes",
        "ampes": "associacions de mares i pares d'alumnes",
        "afas": "associacions de famílies d'alumnes",
        "afes": "associacions de famílies d'alumnes",
        "afa": "associació de famílies d'alumnes",
        "tc": "Tribunal Constitucional",
        "tsjc": "Tribunal Superior de Justícia de Catalunya",
        "pimes": "Pime",
        "pime": "Pime",
        "led": "led",
        "unesco": "Unesco",
        "unicef": "Unicef",
        "sepa": "Sepa",
        "erto": "Erto",
        "dni": "document nacional d'identitat",
        "termcat": "Termcat",
    }

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

    cometes = ["‘", "’", "“", '"', "”", "«", "»"]

    for line in sentences:
        count = 0
        exclou_frase = False
        frase_orig = line
        if len(line) > 4:
            if line[0] not in cometes:
                while (
                    not line[0].isalpha() and len(line) > 4
                ):  # clean up the rubbish at the beginning of the sentence
                    line = line[1:]

            if (
                line[0].islower() and options.cap == True
            ):  # check if line starts with a capital letter
                excluded_min.append(frase_orig)
                exclou_frase = True
            else:
                if (
                    line[-1] not in ultim and options.punt == True
                ):  # check that line has a final score
                    possibles_trencades.append(frase_orig)
                    exclou_frase = True
                else:
                    if re.search(repeated_words, line) == None:
                        if options.pnom == True and find_names(line):
                            exclou_frase = True
                            excluded_nom.append(frase_orig)
                        else:
                            line = re.sub(
                                r" \([A-Úa-ú0-9 -\.\,]*\)", "", line
                            )  # clean up what's in parentheses
                            if (
                                any(element in line for element in puntuacio) == False
                                and re.search(r"\.[a-zA-Z]", line) == None
                                and re.search(emojis, line) == None
                                and line[-1] != ":"
                                and " - " not in line
                            ):
                                # check that there are no punctuation marks in the middle, emojis or endings in:
                                if (
                                    re.search(hores, line) == None
                                ):  # we check that there are no time expressions
                                    if options.num == True and any(
                                        element in line for element in nombres
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
                                                trossos[-1] not in mal_final
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
                                                        in reemplacos.keys()
                                                    ):  # develop some abbreviations
                                                        line = line.replace(
                                                            token.text,
                                                            reemplacos[
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
                                                                in paraules_excluded
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
                                                            for element in nombres
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
                                                        and options.verb == True
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
                line = fix_quotation_marks(line, cometes)
                if line[-1] not in ultim:
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

    if not os.path.exists(path):
        os.mkdir(path)
        print("Hem creat el directori", path)
    else:
        print("El directori", path, "ja existeix")

    # stats
    total = len(sentences)
    statistics = [
        "línies inici: " + str(countl),
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
        path,
        nom,
        "estadistiques_filtre.txt",
        opcions_seleccionades + ["---------"] + statistics,
    )
    create_file(path, nom, "frases_seleccionades.txt", frases_seleccionades)
    create_file(path, nom, "excloses_mida.txt", excluded_mida)
    create_file(path, nom, "excloses_caracter.txt", excluded_caracter)
    create_file(path, nom, "excloses_sigles.txt", excluded_sigles)
    create_file(path, nom, "excloses_paraula.txt", excluded_paraula)
    create_file(path, nom, "excloses_ortografia.txt", excluded_ortografia)
    create_file(path, nom, "excloses_proporcio.txt", excluded_proporcio)
    create_file(path, nom, "excloses_hores.txt", excluded_hora)
    create_file(path, nom, "excloses_paraules_repetides.txt", excluded_repeated_words)
    create_file(path, nom, "excloses_nom.txt", excluded_nom)
    create_file(
        path, nom, "frases_seleccionades_repetides.txt", frases_seleccionades_repetides
    )
    create_file(path, nom, "error_num.txt", error_num)
    create_file(path, nom, "possibles_trencades.txt", possibles_trencades)
    create_file(path, nom, "excloses_abreviatura.txt", excluded_abreviatura)
    create_file(path, nom, "excloses_minuscula.txt", excluded_min)
    create_file(path, nom, "excloses_num.txt", excluded_num)
    create_file(path, nom, "excloses_verb.txt", excluded_verb)
    create_file(
        path, nom, "frases_seleccionades_originals.txt", frases_seleccionades_orig
    )

    newfile = open(path + nom + "_" + "estudi_cas_filtre.tsv", "w")
    for frase in estudi_cas:
        newfile.writelines(frase[1] + "\t" + frase[0] + "\n")
    newfile.close()

    newfile = open(path + nom + "_" + "estudi_cas_ortografia.tsv", "w")
    for frase in estudi_cas_ortografia:
        newfile.writelines(frase[1] + "\t" + frase[0] + "\n")
    newfile.close()


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
