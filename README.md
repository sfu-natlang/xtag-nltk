NLTK interface to the XTAG grammar files in multiple languages.

Authors:

* Ziqi Wang
* Haotian Zhang
* Anoop Sarkar

[SFU Natural Language Lab](http://natlang.cs.sfu.ca/)

For now the code implements a viewer for the XTAG grammar format.
It has been tested with the XTAG English grammar and the XTAG Korean
grammar.

Future plans include a parser and grammar generator.

Original XTAG interface and [XTAG project web page](http://www.cis.upenn.edu/~xtag/)

Installation
------------

0. Remove any previous data in `~/nltk_data/xtag_grammar` if previously installed.
1. Run `sh install.sh`. This will install the english and korean grammars into `~/nltk_data/xtag_grammar`.
2. Run `python draw.py english` to view the XTAG English grammar.
3. Run `python draw.py korean` to view the XTAG Korean grammar.

