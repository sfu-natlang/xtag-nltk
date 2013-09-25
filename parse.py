# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

from nltk.parse.nonprojectivedependencyparser import NonprojectiveDependencyParser
from nltk import parse_dependency_grammar

def init(dg):
    """
    init(DependencyGrammar) -> NonprojectiveDependencyParser

    To initialize the non-projective dependency with dependency grammar. The
    grammar can be pre-trained data, or, can be generated using the function
    provided in this module. The initlization must be done before calling
    to any parsing function.

    Th return value is a trained parser object, when calling other functions it
    must be passed as an argument. Thus there can be more than 1 parsers in the
    environment with different grammars.
    """
    p = NonprojectiveDependencyParser(dg)
    return p

def parse_sentence(parser,sent):
    """
    parse_sentence(NonprojectiveDependencyParser,str) -> list

    This function accepts a string sentence and a parser object as input,
    and returns the result of parsing as output. The sentence will be transformed
    into a list, which is the only input type that parse() method can accept,
    using the built-in split() function of class str. Please take care of the
    correctness of the sentence itself.

    If parsing fails (either because of the format or meaning) then a False
    will be returned. Please check the value first before using.
    """
    return parser.parse(sent.split())

def parse_list(parser,sent):
    """
    parse_list(NonprojectiveDependencyParser,list) -> list

    This is almost the same as parse_sentence, except that the 2nd argumemt
    is a list contaning each token of a sentence, instead of a string. The
    return value is also the same.
    """
    return parser.parse(sent)

def get_dep_tree(ds,index):
    """
    get_dep_tree(dict,integer) -> list

    This function is recursively called, with the first argument ds being the
    dictionary returned by a non-projective dependency parser, and the second
    argument index being the index that we would like to use as the root.

    This function will return a tree (i.e. a list) rooted at ds[index]. The
    whole tree can be got by calling with index = 0.
    """
    d = ds[index]
    if d.has_key('tag') and d['tag'] == 'TOP':
        sub_trees = [d['deps']]
    else:
        sub_trees = d['deps']
    # We have met a leaf node, just return a single node with its word
    returned_sub_trees = []
    if len(sub_trees) == 0:
        return [d['word'],None,returned_sub_trees]
    else:
        for i in sub_trees:
            ret = get_dep_tree(ds,i)
            returned_sub_trees.append(ret)
        return [d['word'],None,returned_sub_trees]

dg = parse_dependency_grammar("""
'shot' -> 'I' | 'elephant' | 'in'
'elephant' -> 'an' | 'in'
'in' -> 'pajamas'
'pajamas' -> 'my'
""")
psr = init(dg)

def debug_get_dep_tree():
    trees = parse_sentence(psr,'I shot an elephant in my pajamas')
    print get_dep_tree(trees[0],0)

if __name__ == '__main__':
    debug_get_dep_tree()
