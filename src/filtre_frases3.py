#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 9 setembre 2022
edició maig 2023:
- elimina les frases amb xifres
- comprova que els noms propis no excedeixin 1/3 del total dels tokens
edició gener 2024:
- afegida opció d'excloure noms
- afegits arreglaments apòstrofs
- canviada estratègia reemplaços
- torna a calcular num tokens després reemplaços números

@author: carme
"""
from optparse import OptionParser
from sentence_splitter import SentenceSplitter
import os, sys
#sys.path.append('/home/carme/Desktop/tasques/commonvoice/filtres/')
import llegeix_nums_v2 as nums
import re
import hunspell
import unidecode
from datetime import datetime
import spacy
#nlp = spacy.load("en_core_web_sm", enable=["tok2vec", "tagger"])
nlp = spacy.load("ca_core_news_sm", exclude=["parser", "attribute_ruler", "lemmatizer", "ner"])

cognoms_tots = open("word_lists/cognoms_list.txt", "r").read().splitlines()
cognoms = []
for cognom in cognoms_tots:
    if len(cognom) >= 3:
        cognoms.append(cognom)

def main(argv=None):
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="file",  action="store", help="fitxer que es vol filtrar", default ="/tmp/un_fitxer.txt")    
    parser.add_option("-l", "--list", dest="list",  action="store", help="llista de paraules que es volen eliminar", default ="")
    parser.add_option("-d", "--dir", dest="dir",  action="store", help="directori on es desaran els resultats", default ="")
    parser.add_option("-x", "--num", dest="num",  action="store_true", help="no es transcriuen els números", default =False)
    parser.add_option("-v", "--verb", dest="verb",  action="store_true", help="només frases amb verbs", default =False)
    parser.add_option("-p", "--punt", dest="punt",  action="store_true", help="només frases amb marques de finals", default =False)
    parser.add_option("-m", "--cap", dest="cap",  action="store_true", help="només frases que comencen amb majúscules", default =False)
    parser.add_option("-n", "--pnom", dest="pnom",  action="store_true", help="exclou frases amb possibles noms propis", default =False)
    
    (options, args) = parser.parse_args(argv)


    dic = hunspell.HunSpell('/usr/share/hunspell/ca.dic', '/usr/share/hunspell/ca.aff')
        
    file = options.file
    nom = file.split("/")[-1][:-4]  

    opcions_seleccionades = ["* File: " + nom + "\n" ,"* Opcions seleccionades:"]

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
    
    
    if options.dir != "":
        if options.dir[-1] == "/":
            path = options.dir
        else:
            path = options.dir + "/"
    else:
        if "/" in file:
            oldPath = file[:file.rfind("/")] + "/"
        else:
            oldPath = ""
        path = oldPath + "resulats_filtre_" + nom + "_" + datetime.now().strftime("%Y%m%d_%H%M") + "/"  
    
    if options.list != "":
        paraules_excloses =  open(options.list, "r").read().splitlines() # si es volen filtrar algunes paraules
    else:
        paraules_excloses = []

    lines = open(file, "r").readlines()

    possibles_noms = re.compile(r"[A-Z][a-ü]+ ([Dd][\'e](l)?)? ?[A-Z][a-ü]*")
    def troba_noms(line):
        busca_noms = re.search(possibles_noms, line)                                                           
        if  busca_noms != None:
            possible_nom = busca_noms.group(0)
            possible_cognom = possible_nom[possible_nom.index(" ")+1:]
            if unidecode.unidecode(possible_cognom) in cognoms:
                if busca_noms.span()[0] == 0 and len(busca_noms.group(0).split(" ")[0]) <= 2:
                    return False
                else:
                    return True
            else:
                return False
        else:
            return False

        
    splitter = SentenceSplitter(language='ca')
    sentences = []
    countl = 0
    for l in lines:
        countl += 1
        frases = splitter.split(l)
        for frase in frases:
            parts = frase.split(":")
    #    print(frases)
            sentences.append(parts[-1])
            
    puntuacio = ["|", "[", "]", "(", ")", "@", "#", "$", "&", "*", "+", "{", "}", "/", "=", "®", ">", "<", "≤", "–", "©"] # caràcters que no volem a les frases
    nombres = [str(i) for i in range(10)]   # xifres
    ultim = [".", "!", "?", "\"", "\'"]   # caràcters que indiquen final de frase
    emojis = re.compile(r'[\u263a-\U0001f645]') # emojis
    paraula_repetida = re.compile(r"\b(\w+)\b\s+(\1)\b")
    hores = re.compile(r'[0-2]?[0-9](:|\.)[0-5][0-9](?![0-9])') # hores
    mal_final = ["els", "el", "la", "les", "a", "en", "de", "que", "què", "mitjançant", "del", "dels", "al", "als", "es", "per", "i", "amb", "hem", "ha", "he", "has", "heu", "qual", "han", "són", "com"]   # paraules que no haurien d'acabar una frase
    reemplacos = {"’": "'",    # aquests reemplaços es fan al principi 
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
                "c.": " carrer", # càrrec
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
                "ptes.": " pessetes", # aptes
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
                "iban" : "Iban",
                "ibex" : "Ibex",
                "eeuu" : "Estats Units",
                "eua" : "Estats Units",
                "eu" : "Unió Europea",
                "ue" : "Unió Europea",
                "nie" : "Nie",
                "erc" : "Esquerra Republicana de Catalunya",
                "ciu" : "Convergiència i Unió",
                "psoe" : "Partit Socialista Espanyol",
                "pp" : "Partit Popular",
                "cup" : "Cup",
                "psc" : "Partit Socialista de Catalunya",
                "ccoo" : "Comissions Obreres",
                "ampa" : "associació de mares i pares d'alumnes",
                "ampas" : "associacions de mares i pares d'alumnes",
                "ampes" : "associacions de mares i pares d'alumnes",
                "afas" : "associacions de famílies d'alumnes",
                "afes" : "associacions de famílies d'alumnes",
                "afa" : "associació de famílies d'alumnes",
                "tc" : "Tribunal Constitucional",
                "tsjc" : "Tribunal Superior de Justícia de Catalunya",
                "pimes" : "Pime",
                "pime" : "Pime",
                "led" : "led",
                "unesco" : "Unesco",
                "unicef" : "Unicef",
                "sepa" : "Sepa",
                "erto" : "Erto",
                "dni" : "document nacional d'identitat",
                "termcat" : "Termcat"
                }
            
# aquí hi ha les llistes on es van desant les frases segons si es descarten o no
    tokens_descartats = []
    frases_seleccionades = []
    frases_seleccionades_orig = []
    frases_seleccionades_repetides = []
    excloses_caracter = []
    excloses_ortografia = []
    excloses_proporcio = []
    excloses_mida = []
    excloses_sigles = []
    excloses_paraula = []
    excloses_paraula_repetida = []
    excloses_nom = []
    error_num = []
    excloses_abreviatura = []
    excloses_hora = []
    possibles_trencades = []
    estudi_cas = []
    estudi_cas_ortografia = []
    excloses_min = []
    excloses_num = []
    excloses_verb = []

    def create_file(myfile, mylist):
        os.makedirs(path, exist_ok=True)
        newfile = open(path + nom + "_" + myfile, "w")
        mylist.sort()
        for frase in mylist:
            newfile.writelines(frase+"\n")
        newfile.close()
        
    def tokenizer(line):
        new_line = re.sub(r'([^A-Za-zÀ-ÿ0-9\.\,·\-])', ' \\1 ', line)
        new_line = re.sub(r'([sdmtlnSDMTLN]) \'', '\\1\' ', new_line)
        new_line = re.sub(r'\' ([smtlnSMTLN])', '\'\\1', new_line)
        new_line = re.sub(r'([^0-9])(\.|,)', '\\1 \\2 ', new_line)
        new_line = re.sub(r'([0-9])(\.|,)(\D|\Z)', '\\1 \\2 \\3 ', new_line)
        new_line = re.sub(r'[ ]+', ' ', new_line)
        trossos = new_line.split(" ")
        if trossos[0] == '':
            trossos = trossos[1:]
        if trossos[-1] == '':
            trossos = trossos[:-1]
        return trossos
    
    def treu_puntuacio(list):
        items = [".", ",", "!", ":", "?"]
        for item in items:
            while item in list:
                list.remove(item)
        return list

    cometes = ["‘", "’", "“", "\"", "”", "«", "»"]
    def arregla_cometes(text):
        text = re.sub(r"([nldNLD])’(h?[aeiouAEIOUàèéíòóúÀÈÉÍÒÓÚ])", r"\1'\2", text)  # arregla apòstrofs
        text = re.sub(r"([aeiouAEIOUàèéíòóú])’([nldNLD])", r"\1'\2", text)  # arregla apòstrofs
        text = re.sub(r"([aeiouAEIOUàèéíòóúnldNLD])' (h?[aeiouAEIOUàèéíòóúnldNLD])", r"\1'\2", text)  # arregla apòstrofs    
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
        

    for line in sentences:
        count = 0
        exclou_frase = False
        abreviatura = False
        frase_orig = line
        if len(line) > 4:
            if line[0] not in cometes:
                while not line[0].isalpha() and len(line) > 4:                      # netegem les brossetes a princpi de frase
                    line = line[1:]    

            if line[0].islower() and options.cap == True:                           # revisem si comença amb majúscula                 
                excloses_min.append(frase_orig)  
                exclou_frase = True
            else:                                                                                                                                                       
                if line[-1] not in ultim and options.punt == True:                  # comprovem que té puntuació de final
                    possibles_trencades.append(frase_orig)
                    exclou_frase = True
                else:      
                    if re.search(paraula_repetida, line) == None:
                        if options.pnom == True and troba_noms(line):
                            exclou_frase = True
                            excloses_nom.append(frase_orig)
                        else:
                            line = re.sub(r" \([A-Úa-ú0-9 -\.\,]*\)", "", line)             # netegem el que hi ha entre parèntesis
                            if any(element in line for element in puntuacio) == False and re.search(r'\.[a-zA-Z]', line) == None and re.search(emojis, line) == None and line[-1] != ":" and " - " not in line:
                                                                                            # comprovem que no hi hagi signes de puntuació pel mig, emojis o acabades en :
                                if re.search(hores, line) == None:                          # comprovem que no hi hagi expressions horàries
                                            
                                    if options.num == True and any(element in line for element in nombres):
                                                                                            # comprovem si hi ha nombres
                                        excloses_num.append(frase_orig)
                                        exclou_frase = True
                                    else:                          
                                        trossos = line.split(" ")                           # fem una primera tokenització simple
                                        if len(trossos) >= 4 and len(trossos) <= 18:        # comptem el número de tokens
                                            if trossos[-1] not in mal_final:           # comprovem que no acaba malament
                                                # aquí acaba el primer procés de selecció
                                                tokens = nlp(line)                          # tokenitzem amb l'spacy
                                                te_verb = False
            
                                                for token in tokens:
                                                    if token.pos_ == "VERB" or token.pos_ == "AUX":
                                                        te_verb = True
                                                    if token.text.lower() in reemplacos.keys():  # desenvolupem algunes abreviatures
                                                        line=line.replace(token.text, reemplacos[token.text.lower()])
                                                
                                                    else:
                                                        if token.text.isalpha():
                                                            if len(token) == 1:
                                                                if token.text.lower() in ["a", "e", "i", "o", "u", "l", "d", "p"]:
                                                                    pass
                                                                else:                        # si és una consonant sola, excloem la frase
                                                                    exclou_frase = True
                                                                    excloses_ortografia.append(frase_orig)
                                                                    estudi_cas_ortografia.append([frase_orig, token.text])
                                                                    break
                                                            elif token.text.isupper():       # si és tota majúscula
                                                                exclou_frase = True
                                                                excloses_sigles.append(frase_orig)
                                                                break
                                                            elif token.text in paraules_excloses:   # si està a la llista de paraules prohibiles, exclou la frase
                                                                exclou_frase = True
                                                                excloses_paraula.append(frase_orig)
                                                                estudi_cas.append([frase_orig, token.text])
                                                                break
                                                    
                                                            elif not dic.spell(token.text):
                                                                if token.text[0].islower() and token.text != "ls": # si no comença amb majúsucula ni està al diccionari, excloem la frase
                                                                    exclou_frase = True
                                                                    excloses_ortografia.append(frase_orig)
                                                                    estudi_cas_ortografia.append([frase_orig, token.text])
                                                                    tokens_descartats.append(token.text)
                                                                    break
                                                                elif token.text[0].isupper():
                                                                    count += 1
                                                                                                                        
                                                        if any(element in token.text for element in nombres):     # si hi ha alguna xifra 
                                                            try:                              # intentem transcriure-la (si no es volia transcriure, ja s'ha descartat abans)    
                                                                transcrip = nums.llegeix_nums(token.text)
                                                                line = line.replace(token.text, transcrip, 1) 
                                                            except:                           # si no podem
                                                                if token.text[-1] == "h":     # mirem si acaba en h i ho tornem a provar
                                                                    try:                      
                                                                        transcrip = nums.llegeix_nums(token.text[:-1]) + " hores"
                                                                        line = line.replace(token.text, transcrip, 1) 
                                                                        
                                                                    except:                   # si no podem, la descartem
                                                                        error_num.append(frase_orig)
                                                                        exclou_frase = True
                                                                        break
                                                                else:                         # si no podem, la maquem com a error
                                                                    error_num.append(frase_orig)
                                                                    exclou_frase = True
                                                                    break
                                                            if exclou_frase == False and len(line.split(" ")) >= 18: # comprovem que la frase no s'hagi fet massa llarga.
                                                                excloses_mida.append(frase_orig)
                                                                exclou_frase = True
                                                if count >= len(trossos)/3:
                                                    exclou_frase = True
                                                    excloses_proporcio.append(frase_orig)    
                                                else:
                                                    if te_verb == False and options.verb == True and exclou_frase == False:   # si no té verb i ho hem posat com a requisit i la frase no ha estat eliminada abans, elimina la frase
                                                        exclou_frase = True
                                                        excloses_verb.append(frase_orig)
                                            else:
                                                exclou_frase = True
                                                possibles_trencades.append(frase_orig)
                                        else:
                                            exclou_frase = True
                                            excloses_mida.append(frase_orig)
                                else:
                                    exclou_frase = True
                                    excloses_hora.append(frase_orig)
                            else:
                                exclou_frase = True
                                excloses_caracter.append(frase_orig)
                    else:
                        exclou_frase = True
                        excloses_paraula_repetida.append(frase_orig)
        else:
            exclou_frase = True
            excloses_mida.append(frase_orig)
        
        if exclou_frase == False:                                
            if "." in line[:-2]:                                    # mirem que no hagi quedat cap punt dins la frase
                if ".." in line:
                    line = re.sub('\.(\.)+', "...", line)
                else:
                    abreviatura = True
                    excloses_abreviatura.append(frase_orig)
            else:                                                   # un cop seleccionades les frases, fem els arreglets
                line = arregla_cometes(line)
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
    
            

            
    # estadistiques
    total = len(sentences)

    def descriu(descriptor, llista):
        text = descriptor + " " + str(len(llista)) + " (" + str(round(len(llista)*100/total, 2)) + "%)"
        return text

    estadistiques = ["línies inici: " + str(countl),
            "frases inici: " + str(total),
            descriu("excloses mida:", excloses_mida),
            descriu("excloses caracter:", excloses_caracter),
            descriu("excloses sigles:", excloses_sigles),
            descriu("excloses paraules:", excloses_paraula),
            descriu("excloses ortografia:", excloses_ortografia),
            descriu("excloses proporció:", excloses_proporcio),
            descriu("excloses hores:", excloses_hora),
            descriu("excloses paraules repetides:", excloses_paraula_repetida),
            descriu("excloses noms:", excloses_nom),
            descriu("seleccionades repetides:", frases_seleccionades_repetides),
            descriu("seleccionades:", frases_seleccionades),
            descriu("abreviatures:", excloses_abreviatura),
            descriu("possibles trencades:", possibles_trencades),
            descriu("comença amb min:", excloses_min),
            descriu("conté una xifra:", excloses_num),
            descriu("excloses verb:", excloses_verb),
            
            descriu("error num:", error_num)]
    for r in estadistiques:
        print(r)
        
    create_file("estadistiques_filtre.txt", opcions_seleccionades + ["---------"] + estadistiques)
    create_file("frases_seleccionades.txt", frases_seleccionades)
    create_file("excloses_mida.txt", excloses_mida)
    create_file("excloses_caracter.txt", excloses_caracter)
    create_file("excloses_sigles.txt", excloses_sigles)
    create_file("excloses_paraula.txt", excloses_paraula)
    create_file("excloses_ortografia.txt", excloses_ortografia)
    create_file("excloses_proporcio.txt", excloses_proporcio)
    create_file("excloses_hores.txt", excloses_hora)
    create_file("excloses_paraules_repetides.txt", excloses_paraula_repetida)
    create_file("excloses_nom.txt", excloses_nom)
    create_file("frases_seleccionades_repetides.txt", frases_seleccionades_repetides)
    create_file("error_num.txt", error_num)
    create_file("possibles_trencades.txt", possibles_trencades)
    create_file("excloses_abreviatura.txt", excloses_abreviatura)
    create_file("excloses_minuscula.txt", excloses_min)
    create_file("excloses_num.txt", excloses_num)
    create_file("excloses_verb.txt", excloses_verb)
    create_file("frases_seleccionades_originals.txt", frases_seleccionades_orig)

        

    newfile = open(path + nom + "_" + "estudi_cas_filtre.tsv", "w")
    for frase in estudi_cas:
        newfile.writelines(frase[1]+"\t"+frase[0]+"\n")
    newfile.close()    


    newfile = open(path + nom + "_" + "estudi_cas_ortografia.tsv", "w")
    for frase in estudi_cas_ortografia:
        newfile.writelines(frase[1]+"\t"+frase[0]+"\n")
    newfile.close()    

if __name__ == "__main__":
    sys.exit(main())
