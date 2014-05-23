NLTK interface to the XTAG grammar files in multiple languages.

Github repository: https://github.com/sfu-natlang/xtag-nltk.git

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

0. git clone https://github.com/sfu-natlang/xtag-nltk.git
1. cd xtag-nltk
2. Remove any previous data in `~/nltk_data/xtag_grammar` if previously installed.
3. Run `sh install-xtag-grammars.sh`. This will install the english and korean grammars into `~/nltk_data/xtag_grammar`.
4. Run `python draw.py english` to view the XTAG English grammar.
5. Run `python draw.py korean` to view the XTAG Korean grammar.

