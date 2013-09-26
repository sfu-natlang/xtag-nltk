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

def dep_init(dg):
    """
    dep_init(DependencyGrammar) -> NonprojectiveDependencyParser

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

def dep_parse_sentence(parser,sent):
    """
    dep_parse_sentence(NonprojectiveDependencyParser,str) -> list

    This function accepts a string sentence and a parser object as input,
    and returns the result of parsing as output. The sentence will be transformed
    into a list, which is the only input type that parse() method can accept,
    using the built-in split() function of class str. Please take care of the
    correctness of the sentence itself.

    If parsing fails (either because of the format or meaning) then a False
    will be returned. Please check the value first before using.
    """
    return parser.parse(sent.split())

def dep_parse_list(parser,sent):
    """
    dep_parse_list(NonprojectiveDependencyParser,list) -> list

    This is almost the same as dep_parse_sentence, except that the 2nd argumemt
    is a list contaning each token of a sentence, instead of a string. The
    return value is also the same.
    """
    return parser.parse(sent)

def check_dep_return_value(ret):
    """
    check_dep_return_value(list/bool) -> None

    Check the retuen value in case that a False is encountered.
    """
    if ret == False:
        raise ValueError('The return value of the dependency parse is False.')
    else:
        return

def get_dep_tree(ds,index):
    """
    get_dep_tree(dict,integer) -> list

    This function is recursively called, with the first argument ds being the
    dictionary returned by a non-projective dependency parser, and the second
    argument index being the index that we would like to use as the root.

    This function will return a tree (i.e. a list) rooted at ds[index]. The
    whole tree can be got by calling with index = 0.

    The structure of the tree is expliained below: Each node is repersented
    as a list, the first element is the word, i.e. the token; the second element
    is some additional information, which can be determined by the user, and
    this function will not add anything to this item, just leave a None there;
    the third element is also a list, which contains all the leaves of this node.
    This structure is recursively defined, which is exactly what a tree looks like.
    """
    # Just the same as indexing
    d = ds.get_by_address(index)
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

def get_all_dep_trees(trees):
    """
    get_all_dep_trees(list) -> list

    Given the result of a non-projective dependency parser, which is a list,
    this function will return a list of trees.
    """
    check_dep_return_value(trees)
    new_trees = []
    for i in trees:
        new_trees.append(get_dep_tree(i,0))
        
    return new_trees

#########################################
# Grammar Training ######################
#########################################

def insert_dep_entry(grm,head,modes):
    """
    insert_dep_entry(list,str,list) -> None

    This function will insert a rule into the grammar. The rule is made of a head
    and a mode (or modes). The head is actually the left hand side and the mode
    is the right hand side. modes is a list containing all modes of a particular
    head. This function will change the grammar in-place.

    For example:

    insert_dep_entry(grammar,'shot',['I','elephant','in'])

    will insert a grammar rule 'shot' -> 'I' | 'elephant' | 'in' into the list.
    """
    grm.append((head,modes,))
    return

def dep_add_qutation_mark(s):
    return "'" + s + "'"

def convert_dep_into_str(grm):
    """
    convert_dep_into_str(grm) -> str

    Return the string representation of the dependency grammar. Used for training
    using parse_dependency_grammar()
    """
    s = ""
    for i in grm:
        lhs = dep_add_qutation_mark(i[0])
        rhs = dep_add_qutation_mark(i[1][0])
        for j in i[1][1:]:
            rhs += ' | ' + dep_add_qutation_mark(j)
        s += ('\n' + lhs + ' -> ' + rhs)
    return s
    
dg = parse_dependency_grammar("""
'shot' -> 'I' | 'elephant' | 'in'
'elephant' -> 'an' | 'in'
'in' -> 'pajamas'
'pajamas' -> 'my'
""")
psr = dep_init(dg)
help(dg)

def debug_convert_dep_into_str():
    grm = []
    insert_dep_entry(grm,'shot',['I','elephant','in'])
    insert_dep_entry(grm,'in',['pajamas'])
    insert_dep_entry(grm,'elephant',['an','in'])
    insert_dep_entry(grm,'pajamas',['my'])
    print parse_dependency_grammar(convert_dep_into_str(grm))

def debug_get_dep_tree():
    trees = dep_parse_sentence(psr,'I shot an elephant in my pajamas')
    print get_all_dep_trees(trees)

if __name__ == '__main__':
    debug_get_dep_tree()
