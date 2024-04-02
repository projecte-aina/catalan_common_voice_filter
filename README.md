![Tests](https://github.com/projecte-aina/catalan_common_voice_filter/actions/workflows/tests.yml/badge.svg)

This work has been promoted and financed by the Generalitat de Catalunya through the [Aina project](https://projecteaina.cat/).

# Common Voice Script
This script was designed to filter text for the [Common Voice Catalan Corpus](https://commonvoice.mozilla.org/ca).

This project is developed to run with Python 3.10 on Linux Ubuntu 22.04 or later.

## Configuration and Setup Needed to Run the Script
```
$ sudo apt-get install -y libhunspell-dev

$ curl -sS https://apertium.projectjj.com/apt/install-release.sh | sudo bash
$ sudo apt-get -f install -y apertium apertium-eng-cat

$ python3 -m venv env                
$ source env/bin/activate             
$ pip install -r requirements.txt     
$ pip install hunspell

$ python -m spacy download ca_core_news_sm
$ pip install -e .
```

## Additional Configuration Needed for Development/Running the Tests
```
$ pip install -r requirements_dev.txt      
$ pre-commit install

$ pytest
```

## Filter Phrases
The `filter_phrases.py` script filters sentences from a text document and classifies them according to whether they are useful for the Common Voice corpus or not.

If they are not, it classifies them according to the reason.

The script creates a folder with statistics and the obtained results.

To run the script, run the following commands:

```
$ cd src/catalan_common_voice_filter
$ python filter_phrases.py -f FILE [OPTIONS]
```

### Filter Options

#### --file (-f) [REQUIRED]
Path to the file to be filtered

#### --list (-l)
The `--list` option allows you to pass a file with a list of words that could cause problematic misunderstandings. Sentences containing these words will be excluded.

```
$ cd src/catalan_common_voice_filter
$ python filter_phrases.py -f path/to/file-to-filter.txt -l path/to/words-to-exclude.txt
``` 

#### --dir (-d)
Directory where you want to save the results.

If this option is not set, the `filter_phrases.py` script will create a results directory in the parent folder of the file passed in 
to be filtered.

#### --num (-n)
Remove sentences that contain numbers.

If this option is not set, the script will attempt to transcribe the numbers in the text.

#### --cap (-c)
Remove sentences that do not start with a capital letter.

If this option is not set, the script will capitalize the first letter of the sentence.

#### --punt (-p)
Remove sentences that don't end in ".", "?" or "!".

If this option is not set, the script puts a period at the end of these sentences.

#### --verb (-v)
Eliminate sentences that do not contain a verb.

#### --proper-nouns (-pn)
Eliminate sentences that contain possible personal names.

### Filtering Criteria
Sentences that meet any of the following criteria (in this order) are removed:
* do not reach a minimum of five characters
* contain numbers that could be expressing hours
* contain certain characters ($, &, emojis, etc.)
* contain less than 4 words or more than 18.
* contain a word written in all capital letters (possible acronyms)
* contain a word from the list of excluded words
* contain some word that does not start with a capital letter and is not found in the Hundspell dictionary
* contain numbers that cannot be transcribed

### Modifications of Sentences
Some sentences are modified slightly to be used by the corpus:
* strings containing more than one '!' and/or '?' are replaced with a single character
* quotes and apostrophes will be modified if necessary
* certain characters at the beginning of the line are removed (*, §, –, numbers, etc.)
* numbers will be transcribed
* some common acronyms and abbreviations will be replaced with the full word/phrase
* strings of more than three dots are replaced by an elipsis ("...")
* a period is added to sentences that are not closed by any punctuation marks
* the first character of a sentence is capitalized
* sentences containing a ":" are split and the first part is removed

### Resultats
`filter_phrases.py` creates a folder `filter_results_FILE_DATETIME` in the same directory as the file that has been filtered (unless an 
output directory has been specified with the `--dir` flag), with the statistics and the results obtained:

* FILE_number_transcription_errors.txt (sentences with figures that could not be transcribed)
* FILE_filter_statistics.txt (statistics)
* FILE_filter_case_study.tsv (sentences where a word appears in the list of excluded words, with the word at the beginning)
* FILE_spelling_case_study.tsv (sentences with a word that is not in the dictionary, with the word at the beginning)
* FILE_excluded_abbreviations.txt
* FILE_excluded_characters.txt
* FILE_excluded_hours.txt
* FILE_excluded_improper_length.txt
* FILE_excluded_lowercase.txt
* FILE_excluded_names.txt
* FILE_excluded_numbers.txt
* FILE_excluded_spelling.txt
* FILE_excluded_words.txt
* FILE_excluded_repeated_words.txt
* FILE_excluded_proportion_of_proper_nouns.txt (more than a third of the words are proper nouns)
* FILE_excluded_acronyms.txt
* FILE_excluded_verbs.txt
* FILE_selected_original_phrases.txt (original sentences)
* FILE_selected_repeated_phrases.txt
* FILE_selected_phrases.txt
* FILE_excluded_possible_breaks.txt (sentences that do not have any ending punctuation)


## Links of interest:
* [cv-dataset](https://github.com/common-voice/cv-dataset/tree/main/datasets)
* [Common Voice Dataset Analyzer](https://cv-dataset-analyzer.netlify.app/)
* [Common Voice Metadata Viewer](https://cv-metadata-viewer.netlify.app/)
