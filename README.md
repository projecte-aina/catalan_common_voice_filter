![Tests](https://github.com/projecte-aina/catalan_common_voice_filter/actions/workflows/tests.yml/badge.svg)

# common-voice-scripts
Scripts que faig servir per al corpus commonvoice

## Preparar el venv per executar l'script
```
sudo apt-get install -y libhunspell-dev

curl -sS https://apertium.projectjj.com/apt/install-release.sh | sudo bash
sudo apt-get -f install -y apertium apertium-eng-cat

python3 -m venv env                 # crea un venv que es diu env
source env/bin/activate             # activa el venv
pip install -r requirements.txt     # installa els requirements
pip install hunspell

python -m spacy download ca_core_news_sm
pip install -e .
```

## Configuració addicional si voleu desenvolupar i executar proves
```
pip install -r requirements_dev.txt      # installa dependències per al desenvolupament
pre-commit install

pytest
```

## Filtrar les frases
[filtre_frases.py](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/filtre_frases.py) filtra les frases d'un document en .txt i les classifica segons si són útils per al corpus commonvoice o no. 
En cas que no ho siguin, les classifica segons el motiu.

Crea una carpeta amb les estadístiques i els resultats obtinguts.

```
cd src/catalan_common_voice_filter
python filtre_frases.py -f FILE [OPTIONS]
```

L'script [llegeix_nums_v2.py](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/llegeix_nums_v2.py) transcriu alguns nombres. [filtre_frases.py](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/filtre_frases.py) el fa servir per evitar descartar tantes frases.

### Opcions del filtre

#### file (-f)
Nom del filtxer que es vol filtrar

#### list (-l)
L'opció -l permet passar un fitxer amb una llista de paraules que podrien causar malentensos problemàtics. S'exclouran les frases que continguin aquestes paraules.
```
cd src/catalan_common_voice_filter
python filtre_frases.py -f FILE.txt -l LLISTA.txt
``` 
Al directori [llistes_paraules](https://github.com/TeMU-BSC/common-voice-scripts/tree/main/llistes_paraules) hi ha llistes amb paraules que es poden fer servir.


#### dir (-d)
Directori on es vol desar els resultats.

Si no es posa aquesta opció, es crearà el directori "resultats_filtre_FILE".

#### numbers (-x)
Elimina les frases que continguin xifres. 

Si no es posa aquesta opció, s'intenten transcriure les xifres amb l'script [llegeix_nums_v2.py](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/llegeix_nums_v2.py).

#### capitals (-m)
Elimina les frases que no comencin amb majúscula.

Si no es posa aquesta opció, l'script posarà la primera lletra de la frase en majúscula.

#### puntuaction (-p)
Elimina les frases que no acabin en ".", "?" o "!".

Si no es posa aquesta opció, l'script posa un punt al final d'aquestes frases.

#### verb (-v)
Elimina les frases que no continguin un verb.

#### personal names (-n)
Elimina les frases que contenen possibles noms de persona.

### Criteris de filtratge
S'eliminien les frases que compleixen amb algun dels criteris següents (en aquest ordre):
* no arriben a un mínim de cinc caràcters
* Contenen nombres que podrien estar expressant hores
* contenten determinats caràcters ($, &,  emojis, etc.)
* Contenen menys de 4 paraules o més de 18.
* Contenen alguna paraula escrita amb majúscules (possibles sigles)
* Contenen alguna paraula de la llista de paraules excloses
* Contenen alguna paraula que no comença amb majúscula i no es troba al diccionari Hundspell
* Contenen xifres que l'script llegeix_nums_v2 no sap transcriure


### Modificacions de les frases
Algunes frases es modifiquen lleugerament per poder-les fer servir pel corpus:
* Se subsituteixen les cadenes de més d'un ! o ? per un sol caràcter
* s'intenten arreglar les cometes i apòstrofs
* S'eliminen determinats caràcters al principi de la línia (*, §, –, numeracions, etc.)
* S'intenten transcriure les xifres
* Es desenvolupen algunes sigles i abreviatures
* Se sustitueixen les cadenes de més de tres punts per "..."
* S'afegeix un punt a les frases que no estan tancades per cap signe de puntuació
* Es posa el primer caràcter en majúsucula, si no ho està
* Es parteixen les frases a partir de ":" i se n'elimina la primera part

### Resultats
[filtre_frases.py](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/filtre_frases.py) crea una carpeta *resultats_filtre_FILE_DATETIME* en el mateix directori on hi ha el fitxer que s'ha filtrat, amb les estadístiques i els resultats obtinguts:
* FILE_error_num.txt (frases amb xifres que no s'han pogut transcriure)
* FILE_estadistiques_filtre.txt (estadístiques)
* FILE_estudi_cas_filtre.tsv (frases on surt alguna paraula de la llista de paraules excloses, amb la paraula al principi)
* FILE_estudi_cas_ortografia.tsv (frases amb alguna paraula que no consta al diccionari, amb la paraula al principi)
* FILE_excloses_abreviatura.txt
* FILE_excloses_caracter.txt
* FILE_excloses_hores.txt
* FILE_excloses_mida.txt
* FILE_excloses_minúscula.txt
* FILE_excloses_nom.txt
* FILE_excloses_num.txt
* FILE_excloses_ortografia.txt
* FILE_excloses_paraula.txt
* FILE_excloses_paraules_repetides.txt
* FILE_excloses_proporcio.txt (més d'un terç de les paraules són noms propis)
* FILE_excloses_sigles.txt
* FILE_excloses_verb.txt
* FILE_frases_seleccionades_originals.txt (les frases abans de ser modificades)
* FILE_frases_seleccionades_repetides.txt
* FILE_frases_seleccionades.txt
* FILE_frases_possibles_trencades.txt (frases que no tenen un signe de finalització)


## Filtre ortogràfic
Per assegurar la qualitat lingüística de les frases, SoftCatalà ens ha compartir el seu filtre ortrogràfic

```
java -jar PATH/common-voice-scripts/filtercorpus-0.0.1-SNAPSHOT-jar-with-dependencies.jar --txt FITXER_AMB_FRASES.txt seleccionades.txt 2>&1 | tee errors.txt
```

Si es té temps i ganes, es poden repassar les frases d'erorrs.txt i intentar recuperar-les.

## Eliminar les frases amb noms de persona

Aquesta opció ha estat incorporada a filtre_frases3.py

L'script troba_noms.py busca les frases que contenen l'expressió regular "[A-Z][a-ü]* ([Dd][\'e])? ?[A-Z][a-ü]*" i mira si la segona part és a la llista de cognoms.

```
 python troba_noms.py -f FILE
``` 
Si es compeixen les dues condicions, desa la frase en fitxer *frases_amb_possibles_noms.txt, en el mateix directori on hi havia el fitxer original. <b>Cal revisar les frases a mà i deixar només les que tenen noms</b>.

Després, es poden eliminar de l'arxiu original amb la comanda:
```
grep -v -f LLISTA_DE_FRASES_A_ESBORRAR.txt LLISTA_DE_TOTES_LES_FRASES.txt > FRASES_SENSE_NOMS.txt
```

## Preparar una mostra per avaluar
Commonvoice demana que una mostra de les frases que es puja en cada PR hagi estat revisada per almenys dos parlants nadius.
El volum de la mostra es calcula amb aquesta eina [sample-size-calculator](https://www.surveymonkey.com/mp/sample-size-calculator/).
Cal posar la quantitat de frases que es tenen, el confidence level al 99% i el margin of error al 2%.

Llavors es pot fer servir [agafa_una_mostra.py](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/agafa_una_mostra.py):

    python agafa_una_mostra.py -f FILE -n NUM_DE_FRASES_QUE_ES_VOLEN

el resultat es guarda a */tmp/mostra.txt*

### Fulls de càlcul per als anotadors
Cal anar al [directori del drive](https://drive.google.com/drive/folders/1LgUu0P4zJ0-ewcRV-x1arBKh6wr_Kpne) i fer una còpia de *_template-Sentence_verification_process* i enganxar-hi les frases. 
I després fer-ne una còpia per l'altra anotadora. 
Posar el nom del fitxer original i an1 i an2.

## Comparar dues llistes de frases
```
python compara_llistes.py --file1 FILE1 --file2 FILE2
``` 

## Estadístiques
* [metadata_commonvoice.ipynb](https://github.com/TeMU-BSC/common-voice-scripts/blob/main/metadata_commonvoice.ipynb): notebook amb estadístiques sobre les últimes versions del corpus Common Voice
* [figs](https://github.com/TeMU-BSC/common-voice-scripts/tree/main/statistics): directori amb els gràfics de les estadístiques

Enllaços d'interès:
* [cv-dataset](https://github.com/common-voice/cv-dataset/tree/main/datasets)
* [Common Voice Dataset Analyzer](https://cv-dataset-analyzer.netlify.app/)
* [Common Voice Metadata Viewer](https://cv-metadata-viewer.netlify.app/)
