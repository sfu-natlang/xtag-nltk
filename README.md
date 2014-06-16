# XTAG Grammars in NLTK

This package provides an NLTK interface to the XTAG grammar files
for multiple languages. For now the code implements a viewer for
the XTAG grammar format. It has been tested with the XTAG English
grammar and the XTAG Korean grammar.

Github repository: `https://github.com/sfu-natlang/xtag-nltk.git`

## Setup

1) Get the repository:

         git clone https://github.com/sfu-natlang/xtag-nltk.git

2) Clean up from previous installs (if any):

         rm -f ~/nltk_data/xtag_grammar

3) Get the grammars which are in their own github repositories and install the english and korean grammars into `~/nltk_data/xtag_grammar`.

         cd xtag-nltk
         sh install-xtag-grammars.sh

4) To view the grammars:

* XTAG English grammar: `python draw.py english`
* XTAG Korean grammar: `python draw.py korean`

## Authors

* Ziqi Wang
* Haotian Zhang
* Anoop Sarkar

[SFU Natural Language Lab](http://natlang.cs.sfu.ca/)


Future plans include a parser and grammar generator.

Original XTAG interface and [XTAG project web page](http://www.cis.upenn.edu/~xtag/)

