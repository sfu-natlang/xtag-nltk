# -*- coding: utf-8 -*-
# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

from feature import *
from nltk.featstruct import *
import LL1

###########################################
# LL Parser for catalog file ##############
###########################################

# Do not call these functions from the outside! Only be used by the parser

def get_next_token(s,index,length=None):
    """
    To get the next token in english.gram. It is part of the LL parser.
    :param s: The source string
    :type s: str
    :param index: Current reading position.
    :type index: integer
    :param length: The length of s. Can be None. Just make it faster.
    :type length: integer

    :return: The token and current reading position
    :rtype: tuple(str,integer)
    """
    # This function is used by the LL parser to extract out tokens from the input
    # stream, which is not a general one, but is designed and simplified just
    # for use in the XTAG case. DO NOT USE IT AS A PUBLIC FUNCTION.
    # The return value is a tuple, the first element is the token itself, and
    # if we have reached the end of the string, this value should be a None
    # instead of some certain string. The second element of the tuple is the
    # next character index, after extracting the token, and if the first
    # element is None, the second element is the index that we passed in.
    # i.e. no change at all, this is designed to prevent repeated invalid call.
    #################
    # state = 0: outside anything
    # state = 1: inside ""
    # state = 2: inside identifier
    # state = 3: inside comment (not for sure)
    state = 0
    start = 0
    end = 0
    # length is the length of s, just for speed up if the length can be
    # calculated outside of this function and doesn't change
    if length == None:
        l = len(s)
    else:
        l = length
    while True:
        # If we have already reached the end of the string, index >= l (length)
        if state == 0 and index >= l:
            return (None,index)
        # Jump all space characters
        elif state == 0 and s[index].isspace():
            index += 1
        # Single '(' or ')' or ':' can itself form a token without any indicators
        elif state == 0 and (s[index] == '(' or s[index] == ')' or s[index] == ':'):
            return (s[index],index + 1)
        # If we have seen a '"' then enter a state that will accept anything
        # until another '"', this is used to extract out strings.
        elif state == 0 and s[index] == '"':
            start = index
            state = 1
            index += 1
        # See above.
        elif state == 1 and s[index] == '"':
            end = index
            state = 0
            return (s[start:end + 1],index + 1)
        # all numbers and characters as well as "'" without any space in the
        # middle will be treated in a whole.
        elif state == 0 and (s[index].isalnum() or s[index] == "'"):
            state = 2
            start = index
            index += 1
        # Any space, ')', '(' will terminate an identifier in state 2.
        elif state == 2 and (s[index].isspace() or s[index] == ')' or s[index] == '('):
            end = index - 1
            return (s[start:end + 1],index)
        # Skip all comments until the end of line (indicated by a '\n')
        elif state == 0 and (s[index] == ';' or s[index] == '#'):
            state = 3
            index += 1
        # See above
        elif state == 3 and s[index] == '\n':
            state = 0
            index += 1
        # NOTICE: this is not a exception, many branches above will rely on this
        # else statement, for it is the default processor for many other generic cases
        # not listed above.
        else:
            index += 1

catalog_name = {} # Global names defined by a "setf" statement

def add_new_name(s,index):
    """
    Extract a token from the string as a name, and add the name into the table.
    If there is a name clash then just raise an error
    
    :param s: The source string
    :type s: str
    :param index: Current reading position
    :type index: integer
    :return: The token and current reading position.
    :rtype: tuple(str,integer)
    """
    # This function will add a global name, i.e. those defined after 'setf'
    # into a global dictionary, called catalog_name, and will be retrieved by
    # generate_string later.
    global catalog_name
    token_1 = get_next_token(s,index)
    index = token_1[1]
    token_2 = get_next_token(s,index)
    index = token_2[1]
    if catalog_name.has_key(token_1[0]):
        raise TypeError("add_new_name: Name already exist")
    if token_2[0][0] != '"' or token_2[0][-1] != '"':
        raise TypeError('add_new_name: Value must be wrapped with "')
    else:
        catalog_name[token_1[0]] = token_2[0][1:-1]
    return (token_2[0][1:-1],index)

def generate_string(s,index):
    """
    Only "concatenate 'string" method is supported.

    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()
    :return: Evaluated string
    :rtype: Same as in get_next_token()
    """
    # This function will generate a string using the defined identifier name
    # i.e. catalog_name. This will be called if a "concatenate 'string" is encountered.
    global catalog_name
    token = get_next_token(s,index)
    index = token[1]
    string_value = ""
    if token[0] == "'string":
        while True:
            token = get_next_token(s,index)
            if token[0][0] == '"' and token[0][-1] == '"':
                index = token[1]
                string_value += token[0][1:-1]
            elif catalog_name.has_key(token[0]):
                index = token[1]
                string_value += catalog_name[token[0]]
            else:
                return (string_value,index)
    else:
        raise TypeError("generate_string: Don't support concatenate except \"'string\"")

def evaluate_expression(s,index):
    """
    Evaluate "setf" and "concatenate" expressions and get a string
    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()
    :return: Evaluated string
    :rtype: Same as in get_next_token()
    """
    # This function will evaluate those "expressions" defined by 'setf' or
    # 'concatenate', and dispatch them to the corresponding functions
    # No other expression type are supported for now
    token = get_next_token(s,index)
    if token[0] != '(':
        raise TypeError("evaluate_expression: '(' expected.")
    index = token[1]
    token = get_next_token(s,index)
    index = token[1]
    if token[0] == 'setf':
        ret = add_new_name(s,index)
        index = ret[1]
    elif token[0] == 'concatenate':
        ret = generate_string(s,index)
        index = ret[1]
    else:
        raise TypeError("evaluate_expression: Unknown method")
    token = get_next_token(s,index)
    index = token[1]
    if token[0] != ')':
        raise TypeError("evaluate_expression: ')' expected")
    else:
        return (ret[0],index)

def parse_expression(s,index):
    """
    Get a expression strated with "setf" and "concatenate"

    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()

    :return: A node in the parse tree together with the current reading position.
    :rtype: tuple(tuple(str,list(str)),integer)
    """
    # This function is used to parse an expression. i.e. those strings identified
    # by '"' at the start and the end, and also other types, such as 'setf'
    # and 'concatenate'.
    values = []
    while True:
        token = get_next_token(s,index)
        
        if token[0][0] == '"' and token[0][-1] == '"':
            values.append(token[0][1:-1])
            index = token[1]
        elif token[0][0] == '(':
            token_1 = get_next_token(s,token[1])
            if token_1[0] == ':': # A nested option list (identified with '(:')
                return [("expr",values),index]
            else:
                exp_value = evaluate_expression(s,index) # index is still on '('
                values.append(exp_value[0]) # parse "(something)"
                index = exp_value[1]
        else:
            return [("expr",values),index]

def parse_option(s,index):
    """
    An option started with ":"
    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()

    :return: A parsing tree node
    :rtype: tuple
    """
    # This function will parse an option and return the tree, each node of which
    # is actually a option entry of that option. An option is defined as being strated
    # by a ':' symbol, the format of which is :[option name] [option value]
    token = get_next_token(s,index)
    if token[0] != ':':
        return (None,index)
    else:
        index = token[1]
        t = get_next_token(s,index)
        option_name = t[0]
        index = t[1]
        exp = parse_expression(s,index)
        index = exp[1]
    return [("optn",option_name,exp[0]),index]

def parse_option_set(s,index):
    """
    Parse an option set starting with (: and end with )
    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()

    :return: A parsing tree node
    :rtype: list
    """
    # This function is used to parse an option set, which starts with a "(:"
    # and ends with a ")". There can be option entries or even another option
    # in an option, so that it is defined as naturally nested. Also we must
    # distinguish between an sub-option and option entry inside an option.
    token = get_next_token(s,index)
    if token[0] != '(':
        # push back the token just fetched by returning index
        return (None,index)

    options = []
    index = token[1]
    while True:
        opt = parse_option(s,index)
        index = opt[1]
        if opt[0] == None:
            opt = parse_option_set(s,index)
            index = opt[1]
            if opt[0] == None:
                break
            else:
                options.append(opt[0])
        else:
            options.append(opt[0])

    token = get_next_token(s,index)
    index = token[1]
    if token[0] != ')':
        raise TypeError("parse_option_set: ')' expected.")

    return [("opts",options),index]

def parse_language(s,index):
    """
    Parse a language in the english.gram file
    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()

    :return: A parsing tree node
    :rtype: list
    """
    # This function is called to parse a language in the .grammar file, which
    # starts with "(defgrammar [language name]" and ends with ")". There can
    # be only options in the language. And the parse supports more than one
    # language defined in one file, which is represented as a node under
    # the "top" node. 
    token = get_next_token(s,index)
    if token[0] != '(':
        return (None,index)

    token = get_next_token(s,token[1])
    if token[0] != 'defgrammar':
        raise TypeError("parse_language: 'defgrammar' expected.")

    token = get_next_token(s,token[1])
    language_name = token[0]

    option_set = []
    index = token[1]
    while True:
        opt = parse_option_set(s,index)
        index = opt[1]
        if opt[0] == None:
            break
        else:
            option_set.append(opt[0])

    token = get_next_token(s,index)
    if token[0] != ')':
        raise TypeError("parse_language: ')' expected")
    else:
        return [("lang",language_name,option_set),token[1]]
    
def parse_catalog(s,index):
    """
    Prase the whole english.gram file
    :param s: Same as in get_next_token()
    :type s: Same as in get_next_token()
    :param index: Same as in get_next_token()
    :type index: Same as in get_next_token()

    :return: A parsing tree root
    :rtype: tuple
    """
    # This function parses the catalog repersented in a string. The return value
    # is a node of the tree whose content is just the options and other
    # elements of the catalog string. The formats are presented below:
    # node[0] == top: A top node
    #     node[1] ~ end = languages
    # node[0] == lang: A language node
    #     node[1] = language name
    #     node[2] ~ end = option sets
    # node[0] == opts: An option set
    #     node[1] ~ end = option
    # node[0] == optn: An option entry
    #     node[1] = option entry name
    #     node[2] ~ end = option entry values
    # node[0] == expr: An expression node
    #     node[1] ~ end = expression values
    #
    # DON'T DIRECTLY CALL THIS
    #
    top = []
    while True:
        lang = parse_language(s,index)
        if lang[0] == None:
            break
        else:
            top.append(lang[0])
            index = lang[1]
            
    return ("top",top)

def print_tree(node,table=0):
    """
    Recursively print out a parsing tree

    :param node: The tree root for a parsing tree.
    :type node: tuple (returned by the parsing algorithm)
    :param table: Recursion parameter, the number of indents for the current line
    :type table: integer
    """
    # This function is used to print a parse tree in a pre-order manner
    # node should be the root or any sub-tree, and table should not be used
    if node[0] == "top":
        for lang in node[1]:
            print table * '    ' + "top"
            print_tree(lang,table + 1)
    elif node[0] == 'lang':
        print '    ' * table + node[1]
        for opts in node[2]:
            print_tree(opts,table + 1)
    elif node[0] == "opts":
        print '    ' * table + "opts"
        for optn in node[1]:
            print_tree(optn,table + 1)
    elif node[0] == 'optn':
        print '    ' * table + node[1]
        print_tree(node[2],table + 1)
    elif node[0] == 'expr':
        for value in node[1]:
            print '    ' * table + value
    return

def get_catalog(content):
    """
    Given a string of english.gram it will return the parsing tree
    
    :param content: The content of english.gram file
    :type content: str
    :return: The root of the parsing tree
    :rtype: The valued returned by the parsing algorithm
    """
    # Given the string, this function is used to get the parse tree from
    # that file. Only call that once, and the parse tree can be used multiple
    # times to get options.
    #fp = open(filename)
    #s = fp.read()
    s = content
    #fp.close()

    cata = parse_catalog(s,0)
    return cata
    #print_tree(cata,0)

# These three is used to extract a certain sub-tree from the parse tree
# and is used during recursion, so don't modify or read the content of
# these variables, the values are not defined.
file_list = None
suffix = None
path = None
opt_value = None
################

def get_file_tree(node,type_string):
    """
    Given the file type this fuinction will return a subtree which is of the
    given file type.
    
    :param node: The tree root or a subtree.
    :type node: The tree node
    :param type_string: The file type you want
    :type type_string: str
    """
    # DON'T DIRECTLY CALL THIS
    # Given the root node of the parsing tree, and the file type that you want
    # to extract, this function will return the tree containing the list
    # of the files of that type.
    global file_list,suffix,path
    ret = None
    if node[0] == "top":
        for lang in node[1]:
            ret = get_file_tree(lang,type_string)  
    elif node[0] == 'lang':
        for opts in node[2]:
            ret = get_file_tree(opts,type_string)
    elif node[0] == "opts":
        for optn in node[1]:
            if optn[1] == type_string:
                file_list = node[1][0][2][1]
                type_suffix = node 
                suffix = node[1][1][1][1][2][1][0]
                path = node[1][1][1][0][2][1][0]
                return None
            else:
                ret = get_file_tree(optn,type_string)
    elif node[0] == 'optn':
        ret = get_file_tree(node[2],type_string)
    elif node[0] == 'expr':
        pass
    else:
        raise TypeError("Unknown keyword in the catalog: " + node[0])
    return ret

def get_file_list(node,type_string):
    """
    This function is called to get the file list of a certain type.
    
    :param node: The parsing tree node
    :type node: Tree node returned by the parsing algorithm
    :param type_string: The type of files you want to get
    :type type_string: str
    """
    # Given the root node of the parse tree, and the file type
    # you want to get, this function will return a list containing
    # the file names as well as the absolute path of the files.
    # PLEASE CALL THIS ONE
    global file_list,suffix,path
    get_file_tree(node,type_string)
    file_list_full = []
    if suffix == 'db':
        suffix_str = 'flat'
    else:
        suffix_str = suffix
    for i in file_list:
        file_list_full.append(i + '.' + suffix_str)
    return (file_list_full,path[:]) # We must copy the path string


def get_option_value(node,opt_name):
    """
    get_option_value(node,opt_name) -> string

    Given the catalog tree and the option name, this fucntion will output the
    option value, which is a string.

    The option can be any options existing in the parse tree, but if multiple
    same option value exists, this function will return the one that emerges
    first in a pre-order traverse.

    If this function fails, i.e. no option with name opt_name is found, then
    it will return a None. So to detect None return value is necessary.

    Example:
    get_option_value(cata,'start-feature')
    Return:
    <mode> = ind/imp <comp> = nil <wh> = <invlink>  <punct term> = per/qmark/excl <punct struct> = nil
    """
    if node[0] == "top":
        for lang in node[1]:
            ret = get_option_value(lang,opt_name)
            if ret != None:
                return ret
    elif node[0] == 'lang':
        for opts in node[2]:
            ret = get_option_value(opts,opt_name)
            if ret != None:
                return ret
    elif node[0] == "opts":
        for optn in node[1]:
            ret = get_option_value(optn,opt_name)
            if ret != None:
                return ret
    elif node[0] == 'optn':
        if node[1] == opt_name:
            return node[2][1][0]
        else:
            ret = get_option_value(node[2],opt_name)
            if ret != None:
                return ret
    elif node[0] == 'expr':
        pass
    return None

def get_start_feature(node):
    s = get_option_value(node,'start-feature')
    return parse_feature_in_catalog(s)

############################################
# Analyze Morphology File ##################
############################################

def analyze_morph(morph_file_string):
    """
    Analyze the morph file in XTAG grammar.

    :param morph_file_string: The string read from the morph file
    :type morph_file_string: str
    :return: A dictionary repersenting the morph
    :rtype: dict(str,list(tuple(str,str,list(str))))

    This function does the parsing in the line order. Each line has a format like
    this,

    [index in morph] ([index in syntax] [POS in syntax] ([possible features])*)+

    in which the possible feature is the feature defined in the template file
    starting with '@'.

    The return value is a complex one. It is a dictionary using string (word in
    any form) as index, and the value is itself a list. The entries in the list
    some tuples indicating all possible morphs for that word. The tuple has three
    components, the first of which is the index in syntax, and the second is POS
    in syntax, while the third component is a list, which contains the features
    in the template.
    """
    morph = {}
    lines = morph_file_string.splitlines()
    for l in lines:
        # Filters out all blank lines using isspace() which filters out '\n' ' '
        if l.isspace() == True:
            continue
        index_pos_feature = l.split('#')
        # This is special
        m = index_pos_feature[0].split()
        # The first index_pos_feature is different since the first element after
        # split() is the index for the dictionary
        dict_key = m[0]
        morph_list = []  # To record multiple morphs in a line
        morph_list.append((m[1],m[2],m[3:]))
        for i in index_pos_feature[1:]:
            m = i.split()
            morph_list.append((m[0],m[1],m[2:]))
        morph[dict_key] = morph_list
        
    return morph
        

##############################################
# Analyze Syntax File ########################
##############################################

def check_index(index):
    if index == -1:
        raise TypeError('Invalid input line.')

def get_next_pair(s,start):
    # This function will extract next pair of <<XXXX>>OOOOO from the input string
    # s with a starting index = start. The return value is a tuple (entry,value,index)
    # The 3rd value is the next un-read position, could be -1 if there is no more
    # input
    index_start = s.find('<<',start)
    if index_start == -1:
        return (None,None,-1)
    index_end = s.find('>>',index_start) 
    check_index(index_end)
    entry = s[index_start + 2:index_end]
    start = index_end + 2
    index_start = s.find('<<',start)
    if index_start == -1:
        value = s[start:]
        index_return = len(s) - 1
    else:
        value = s[start:index_start]
        index_return = index_start

    return (entry,value,index_return)

def make_reverse_tree_dict(reverse_trees,tree_list,family_list,entry_list):
    """
    Make a dictionary to enable searching words using tree name and family name
    
    :param reverse_trees: The dictionary that you want to implement the reverse search
    :type reverse_trees: dict
    :param tree_list: The list of available trees for a word
    :type tree_list: list(str)
    :param family_list: The list of tree families available for the word
    :type fanily_list: list(str)
    :param entry_list: The list of words to be searched as an index
    :type entry_list: list(tuple(str,str))
    """
    for tree in tree_list:
        if not reverse_trees.has_key(tree):
            reverse_trees[tree] = []
        #reverse_tree_list = reverse_trees[tree] # Just an optimization
        #if not entry_list in reverse_tree_list: # Don't do this
        # We may have some repetitions here but we just keep that, because
        # it costs lots of time to do this. Same for below.
        reverse_trees[tree].append(entry_list[:]) 
    for tree in family_list:
        if not reverse_trees.has_key(tree):
            reverse_trees[tree] = []
        #reverse_tree_list = reverse_trees[tree] # The same as above
        #if not entry_list in reverse_tree_list: # Don't do this
        reverse_trees[tree].append(entry_list[:])
    return

def analyze_syntax(s):
    """
    A parser for the syntax file. A syntax file is indexed using the <<INDEX>>
    and the entries are made of several pairs of <<ENTRY>> and <<POS>>. Also
    we may have <<TREES>> and <<FAMILY>> in the syntax to specify the tree name
    or family name for that word. And finally, the <<FEATURES>> will give us
    some features about the word.

    Update: now we can also do tree-to-word searching, i.e. given a tree name or
    a family name, the dictionary can return a list of words which is applicable
    to the trees or tree families.
    
    :param s: A string read from the syntax file
    :type s: str

    :return: Two dictionaries enabling both word-to-trees and tree-to-words search
    :rtype: tuple(dict,dict)
    """
    # This function returns a dictionary, the index is exactly the <<INDEX>>
    # entry in the syntax file. Each keyword will fetch a list, the element of
    # which is just the lines with the same <<INDEX>>. Each list has four components
    # The first is called entry_list, the element of which is tuples with <<ENTRY>>
    # and <<POS>> being the 1st and 2nd element. The 2nd list is called tree_list
    # the element of which is tree name. The 3rd list is called family_list
    # the element of which is family name. The fourth list is called feature_list
    # the element of which is feature name.
    lines = s.splitlines()
    tokens = {}
    # This dictionary is used to use the tree names to do reverse query to get the
    # word or words
    reverse_trees = {}
    for l in lines:
        if l == '':
            continue
        next_start = 0
        entry_list = []
        tree_list = []
        family_list = []
        feature_list = []
        line_name = 'noname'
        while True:
            next_pair = get_next_pair(l,next_start)
            next_start = next_pair[2]
            entry = next_pair[0]
            value = next_pair[1]
            if next_start == -1:
                break
            elif entry == 'INDEX':
                line_name = value
            elif entry == 'ENTRY':
                entry_name = value
                next_pair = get_next_pair(l,next_start)
                next_start = next_pair[2]
                check_index(next_start)
                entry = next_pair[0]
                value = next_pair[1]
                if entry != 'POS':
                    raise TypeError('<<ENTRY>> must be followed by <<POS>>')
                else:
                    pos = value
                entry_list.append((entry_name,pos))
            elif entry == 'FAMILY':
                family_list = value.split()
            elif entry == 'TREES':
                tree_list = value.split()
            elif entry == 'FEATURES':
                feature_list = value.split()
            else:
                pass
                #raise TypeError('Unknown type: %s' % (entry))

        temp = (entry_list,tree_list,family_list,feature_list)
        if tokens.has_key(line_name):
            tokens[line_name].append(temp)
        else:
            tokens[line_name] = [temp]
            
        # Next we will construct the reverse trees
        make_reverse_tree_dict(reverse_trees,tree_list,family_list,entry_list)
            
    return (tokens,reverse_trees)

def analyze_template(s):
    # The return value of this function is a tuple. The first element of the tuple is a dictionary
    # using identifiers from morph.flat, and the entries are feature structures
    # with proper values set. The second element is a dictionary using keys from
    # syntax-coded.flat, which will return a list containing all feature structures
    # from a given identifier.
    lines = s.splitlines()
    feature_list = {}
    feature_list2 = {}
    for l in lines:
        #print l
        l = l.strip()
        if l == '' or l[0] == ';':
            continue
        
        index = l.find(';')
        if index != -1:
            l = l[:index]
            l = l.strip()
        
        if l[0] == '@':
            if l[-1] != '!':
                raise TypeError("Each line should be terminated with a '!'")
            l = l[1:-1]
            # we only split the name and the other part
            temp = l.split(None,1)
            name = temp[0]
            l = l[len(name):].strip()
            features = l.split(',')

            fs = FeatStruct()
            for f in features:
                f = f.strip()
                index = f.find('=')
                if f[0] == '@' and feature_list.has_key(f[1:]):
                    fs = fs.unify(feature_list[f[1:]])    # unify() does not change in-place
                elif index != -1:
                    lhs = f[:index].strip()
                    rhs = f[index + 1:].strip()
                    ref = False # If not a reference then ref is by default True
                    if rhs[0] == '@':      # rhs can also be reference
                        rhs = feature_list[rhs[1:]]
                        ref = True # Used in make_fs
                    if lhs[0] != '<' or lhs[-1] != '>':
                        raise TypeError('The left hand side of a feature structure must be wrapped with <>')
                    lhs = lhs[1:-1]
                    path = lhs.split()
                    #path.reverse()    # This method is in-place
                    #print "rhs = %s" % (rhs)
                    fs = fs.unify(make_fs(path,rhs,ref))
                else:
                    raise TypeError('Invalid line in template file.')
            feature_list[name] = fs
            #print name
            #print fs,'\n'
        elif l[0] == '#':
            if l[-1] != '!':
                raise TypeError('Invalid input line, must be terminated by "!"')
            l = l[1:-1]
            tokens = l.split(None,1)     # Split for once using space character
            word_pos = tokens[0].strip()

            features = tokens[1].split(',')
            new_fs = FeatStruct()
            for fs in features:
                tokens = fs.split(':',1)
                node_type = tokens[0].strip()
                tokens = tokens[1].split('=',1)
                lhs = tokens[0].strip()[1:-1]    # Remove <>
                rhs = tokens[1].strip()
                lhs = lhs.split()
                if new_fs.has_key(node_type):
                    #new_fs[node_type] = new_fs[node_type].unify(make_fs(lhs,rhs))
                    add_new_fs(new_fs[node_type],lhs,rhs) # Add the feature structure into an existing fs
                else:
                    new_fs[node_type] = make_fs(lhs,rhs)
                    
            if feature_list2.has_key(word_pos) == False:
                feature_list2[word_pos] = new_fs
            else:
                raise KeyError('Duplicate defitinion detected: %s.' % (word_pos))
        else:
            raise TypeError('Cannot recognize line: %s.' % (l))
    return (feature_list,feature_list2)


# analyze_tree_1(s) will split the options and trees into a list, the first and second
# element of which is None, the third being the tree, and the fourth being
# the list of oprion, which will be processed in later phases
def analyze_tree_1(s):
    """
    Process the tree file for later use. On this stage we just separate the
    definition of tree structure and feature structures.
    
    :param s: The string read from a tree file
    :type s: str
    :return: An intermediate result
    :rtype: list
    """
    i = 0
    last_time = 0    # To record the position since the latest ')'
    stack = 0  # We use a simple stack to match brackets

    # Store final result, it is a list of list
    xtag_trees = []    
    options = None
    single_tree = None
    
    is_option = True # Distinguish between trees and feature structures
    for i in range(0,len(s)):
        if s[i] == '(':
            stack += 1
        elif s[i] == ')':
            stack -= 1
            if stack == 0 and is_option == True:
                option = s[last_time:i + 1]
                last_time = i + 1
                is_option = False
            elif stack == 0 and is_option == False:
                single_tree = s[last_time:i + 1]
                last_time = i + 1
                is_option = True
                
                # None is a placeholder for those added in later phases
                xtag_trees.append([None,None,single_tree.strip(),option.strip(),None,None])
    ############### Temporal Patch ##################
    trees = LL1.analyze_tree_file(s)
    for i in range(0,len(trees)):
        xtag_trees[i][5] = trees[i][0][1]
        
    return xtag_trees

def analyze_tree_2(xtag_trees):
    """
    analyze_tree_2() -> list

    Given the result of analyze_tree_1(), this function will further
    split the options string into several small strings, each is started by
    a ':' and ended by the start of another option or by the end of the string.
    """
    for entry in xtag_trees:
        options_str = entry[3]
        name_start = options_str.find('"',0)
        name_end = options_str.find('"',name_start + 1)
        entry[0] = options_str[name_start + 1:name_end]

        option_length = len(options_str)
        option_start = name_end + 1
        option_end = option_start
        options_list = []

        # state = 0: outside any structure
        # state = 1: in an option
        # state = 2: in brackets
        # state = 3: in quotes
        state = 0
        
        # One character less, because we need to pre-fetch a character
        for i in range(name_end + 1,option_length - 1):
            ch = options_str[i]
            ch_forward = options_str[i + 1] # pre-fetch
            ch_backward = options_str[i - 1] # back_fetch
            
            if state == 0 and (ch == '\n' or ch == ' '):
                continue
            elif state == 0 and ch == ':':
                state = 1
                option_start = i + 1
            # We should avoid "(:" being considered as an ending symbol
            elif state == 1 and ch != '"' and ch != '(' and ch_forward == ':':
                state = 0
                option_end = i
                options_list.append(options_str[option_start:option_end])
            # This must happen as the last state transition
            elif state == 1 and ch_forward == ')': 
                options_list.append(options_str[option_start:i + 1])
            # skip everything between '(' and ')'
            elif state == 1 and ch == '(':
                state = 2
            elif state == 2 and ch == ')':
                state = 1
            # skip everything between '"' and '"', except '\"'
            elif state == 1 and ch == '"':
                state = 3
            elif state == 3 and ch == '"': # We must distinguish between '\"' and '"'
                if ch_backward != '\\':
                    state = 1
                    
        entry[3] = options_list
        
    return xtag_trees

def analyze_tree_3(xtag_trees):
    """
    analyze_tree_3() -> list

    Given the result of analyze_tree_2(), this function will extract
    the feature structure specifications into a separate list, and then extract
    RHS as well as LHS for further use.  
    """
    pattern = "UNIFICATION-EQUATIONS"
    pattern_len = len(pattern)

    for entry in xtag_trees:
        features = []
        f_temp = None
        
        for option in entry[3]:
            if option[0:pattern_len] == pattern:
                quote_start = option.find('"')
                quote_end = option.find('"',quote_start + 1)
                f_temp = option[quote_start + 1:quote_end]
                break
        else:
            raise NameError("Cannot find unification specification.")

        f_temp = f_temp.splitlines()
        for i in f_temp:
            i = str.strip(i)
            if i != '':
                exp = i.split('=')
                exp[0] = exp[0].strip()
                exp[1] = exp[1].strip()
                features.append(exp)
                
        entry[1] = features
    return xtag_trees

# This function is replaced by add_new_fs(), please use the new one at any
# situation!
#
#def add_two_feature(features,l_id,rhs,l_feature1,l_feature2 = None):
#    if l_feature2 == None:
#        if features.has_key(l_id):
#            features[l_id][l_feature1] = rhs
#        else:
#            features[l_id] = FeatStruct()
#            features[l_id][l_feature1] = rhs
#    else:
#        if features.has_key(l_id):
#            if features[l_id].has_key(l_feature1):
#                features[l_id][l_feature1][l_feature2] = rhs
#            else:
#                features[l_id][l_feature1] = FeatStruct()
#                features[l_id][l_feature1][l_feature2] = rhs
#        else:
#            features[l_id] = FeatStruct()
#            features[l_id][l_feature1] = FeatStruct()
#            features[l_id][l_feature1][l_feature2] = rhs
#    return

# This function is specially designed for processing the format used in .trees files, given the string indicating
# a path in the format like PP.b:<assign-case other> it will return a list [PP.b, assign-case, other]
def get_path_list(s):
    colon = s.find(':')
    if colon == -1:
        raise ValueError("No colon found in the path given.")
    left = s[:colon]
    right = s[colon + 2:-1]
    # Some features may not have a '.b' or '.t' explicitly so we assume that
    # there is a '.b' by default
    if left.find('.') == -1:
        left += '.b'
    right = [left] + right.split(' ')
    return right
    

def analyze_tree_4(xtag_trees):
    """
    analyze_tree_4() -> list

    Given the result of analyze_tree_3(), this function will make
    use of FeatStruct, and build a feature structure dictionary.  
    """
    for xtag_entry in xtag_trees:
        features =  {}
        for feature_entry in xtag_entry[1]:
            lhs = feature_entry[0]
            rhs = feature_entry[1]
            #l_separator = lhs.find(':')
            r_separator = rhs.find(':')
            
            # We do not process reference until the fifth pass
            # and reference is identified by a ':' on RHS
            if r_separator == -1:
                lhs_list = get_path_list(lhs)
                add_new_fs(features,lhs_list,rhs)
                
                ###
                # The code below is obsolete since we do not use add_two_features()
                # any more. So please do not validate them. We use add_new_fs()
                # instead!
                #l_id = lhs[:l_separator]
                #l_space = lhs.find(' ')

                #feat_rhs = FeatStruct()
                #feat_rhs["__value__"] = rhs                
                
                #if(l_space == -1):
                #    l_feature = lhs[l_separator + 2:-1]
                #    add_two_feature(features,l_id,feat_rhs,l_feature)
                #else:
                #    l_feature1 = lhs[l_separator + 2:l_space]
                #    l_feature2 = lhs[l_space + 1:-1]
                #    add_two_feature(features,l_id,feat_rhs,l_feature1,l_feature2)

        xtag_entry[4] = features
    
    return xtag_trees

def analyze_tree_5(xtag_trees):
    """
    analyze_tree_5() -> list

    Given the result of analyze_tree_4(), this function will continue
    to build the feature structure, and in this phase we must add all values
    even if they are not defined by the tree grammar.  
    """
    for xtag_entry in xtag_trees:
        features = xtag_entry[4]
        for feature_entry in xtag_entry[1]:
            lhs = feature_entry[0]
            rhs = feature_entry[1]
            l_separator = lhs.find(':')
            r_separator = rhs.find(':')   

            if r_separator != -1:
                # get_path_list will return a list, the first item of which
                # is the node name, and the remaining part is the path,
                # e.g. a:<b c d> will get the result as [a,b,c,d]
                lhs_list = get_path_list(lhs)
                rhs_list = get_path_list(rhs)
                rhs_value = features
                # If the path exists till the end, then this will keep True
                # but if we cannot find the key on some level then
                # this will be False
                found_key = True
                for i in rhs_list:
                    if not rhs_value.has_key(i):
                        rhs_value[i] = FeatStruct()
                        rhs_value = rhs_value[i]
                        found_key = False
                    else:
                        rhs_value = rhs_value[i]

                if found_key == False:
                    rhs_value['__or_'] = ''

                add_new_fs(features,lhs_list,rhs_value,1)
                    
                #for i in rhs_list:
                #    if not rhs_value.has_key(i):
                        #raise ValueError('No path %s found in the feature structure' % (rhs_list))
                        #print rhs_list
                #        rhs_value = make_rhs_using_or(i)
                #        print rhs_value
                #        print i
                        
                        #print rhs_value
                #        break
                #    else:
                #        rhs_value = rhs_value[i]
                #        add_new_fs(features,lhs_list,rhs_value)
                        #print rhs_value,'\n'
                #print rhs_value
                
                
                #l_id = lhs[:l_separator]
                #r_id = rhs[:r_separator]
                #r_feature = rhs[r_separator + 2:-1]
                #l_space = lhs.find(' ')

                #if not features.has_key(r_id): # Make sure features[r_id] exists
                #    features[r_id] = FeatStruct()
                #    features[r_id][r_feature] = FeatStruct(__value__ = '')
                #elif not features[r_id].has_key(r_feature): # Make sure features[r_id][r_feature] exists
                #    features[r_id][r_feature] = FeatStruct(__value__ = '')

                #if(l_space == -1):
                #    l_feature = lhs[l_separator + 2:-1]
                #    add_two_feature(features,l_id,features[r_id][r_feature],l_feature)
                #else:
                #    l_feature1 = lhs[l_separator + 2:l_space]
                #    l_feature2 = lhs[l_space + 1:-1]
                #    add_two_feature(features,l_id,features[r_id][r_feature],l_feature1,l_feature2)

    return xtag_trees
            

######################################
# Word and feature conversion ########
######################################

dicts = None
inited = False

def check_pos_equality(morph_pos,syntax_pos):
    if morph_pos == syntax_pos:  # Check literal equality first
        return True
    elif dicts[4].has_key(syntax_pos): # Then check mapping equality
        return dicts[4][syntax_pos] == morph_pos
    else:  # Else not equal
        return False
    

def check_init():
    """
    Checks whether the dictionary has been initialized with some morph, syntax
    and template. If not there will be a KeyError raised.
    """
    global inited
    if inited == False:
        raise KeyError("Initial file name not provided. Please run init() first.")
    return

def get_morph_from_syntax(syn_entry,word):
    m = []
    for i in syn_entry:
        for j in i[0]:
            if j[0] == word:
                if not (word,j[1],[]) in m:
                    m.append((word,j[1],[]))
    return m
    

def word_to_morph(word):
    """
    Accepts a word as the parameter amd returns all morphs of that word.

    :param word: The word you want to search
    :type word: str

    :return: The morph of the word
    :rtype: tuple(bool,list(tuple(str,str,list(str))))

    The first component of the return value is True or False, True means the
    word exist in the morph, so we can use it as a normal word. False means
    there is not an entry, and we will use the default grammar.

    The third component is actually the word for searching in the syntax.
    """
    global dicts
    check_init()

    if dicts[0].has_key(word):
        morph = dicts[0][word]
        ret = (True,morph)
    elif dicts[1].has_key(word):
        morph = get_morph_from_syntax(dicts[1][word],word)
        ret = (True,morph)
    else:
        morph = dicts[0]['%s']
        ret = (False,morph)
        
    return ret

def get_syntax_entry(morph_entry_zero):
    """
    :param morph_entry_zero: morph_entry[0] in morph_to_feature()
    :type morph_entry_zero: str
    :return: The syntax entry
    :rtype: tuple(list,bool), the second value is an indicator to control
    whether we should compare the morph.
    """
    if dicts[1].has_key(morph_entry_zero):
        return (dicts[1][morph_entry_zero],False)
    else:
        return (dicts[1]['%s'],True)

def morph_to_feature(morph_entry,word_exist,word,check_pos=True):
    """
    Accept morph entry as parameter and returns syntax entries.
    
    :param morph_entry: An entry in the morph list. Actually it should be
    an element of the result of word_to_morph()
    :type morph_entry: A morph entry, the structure is illustrated in analyze_morph()
    :param word_exist: Whether the word has been seen in the morph
    :typr word_exist: bool
    :param word: The original word
    :type word: str
    :param check_pos: Whether we should check POS equality before searching
    for feature structures.
    :type check_pos: bool
    :return: A component of the return value of word_to_features()
    :rtype: tuple
    """
    global dicts
    result = []
    # Mind that all words in syntax is lower case, but in morph it may be not
    # So convert them into lower case before searching in the dictionary
    morph_word = morph_entry[0].lower()
    (syn_entry,accept_morph_aux) = get_syntax_entry(morph_word)
    #######
    # syn_entry is the set of lines having the same index, of the same importance
    # syn_entry[i] is one line with a particular index
    # syn_entry[i][0] is the set of <<ENTRY>>sth<<POS>>N, a list
    # syn_entry[i][0][j] is a certain <<ENTRY>>sth<<POS>>N, s tuple
    # syn_entry[i][0][0] is the morph of the word, which is usually the same as the index
    # syn_entry[i][0][j][0] is the string of the word
    # syn_entry[i][0][j][1] is the POS of the word
    ######
    for i in syn_entry:
        word_pos = 0
        # First find the morph we are going to seaech in the morph list
        # i.e. i[0]. We cannot always assume that the morph is the first one
        for j in range(0,len(i[0])):
            if i[0][j][0] == morph_word:
                word_pos = j
                break
        # accept_morph_aux is used when the word has a morph but not in the syntax
        # If it is the case then we will use %s syntax instead, and then the
        # accept_morph_aux is always True to disable the accept_morph
        accept_morph = (morph_word == i[0][word_pos][0]) or accept_morph_aux
        accept_exist = (word_exist == False) # Not used any more

        if check_pos == True:  # We will check the pos
            # Move it to here to reduce calculation
            accept_pos = check_pos_equality(morph_entry[1],i[0][word_pos][1])
            accept = (accept_morph and accept_pos) #or accept_exist # See below
        else:  # Do not check pos
            accept = accept_morph #or accept_exist # Now pos must be checked even if
                                                   # the word is not found.

        if accept:
            morph_feature = []
            syn_feature = []
            for sf in i[3]:  # Like #Something which can be searched in the feature dictionary
                syn_feature.append(dicts[2][1][sf[1:]])
            for mf in morph_entry[2]:
                morph_feature.append(dicts[2][0][mf])

            if word_exist == False or accept_morph_aux == True:
                entry_pos_list = [(word,i[0][0][1])] # The list has only one entry
            else:
                entry_pos_list = i[0]
            tree_list = i[1]
            family_list = i[2]
            result.append((entry_pos_list,tree_list,family_list,syn_feature,morph_feature,morph_entry[1:]))
            
    return result

def word_to_features(word):
    # This function will convert the word into the feature structures associated
    # with this word. The return value of this function is a list, each element
    # of which is a tuple. The element of the list is the morph of the word.
    # throw the exception.
    """
    word_to_features(word) -> list

    Give a word of any form, e.g. take, took, taken, taking, this function will
    return a list of all possible features of this word. The return value is a
    list containing all possibilities.

    To run this function, the initialization procedure init() must be called, or
    an exception will be thrown.
    """
    result = []
    morph_ret = word_to_morph(word)
    morph = morph_ret[1]      # List of morph
    word_exist = morph_ret[0] # Whether the word exists
    
    # Each entry in morph has the following structure
    # tuple(morph,POS,list of features), and for the same word the morph can be
    # different, so we must 
    for morph_entry in morph: 
    #    if word_exist == True:
    #        temp_feature = dicts[1][entry[0]]
    #    else:
    #        temp_feature = dicts[1]['%s']
    #    
    #    for i in temp_feature:
    #        if (i[0][0][0] == entry[0] and i[0][0][1] == entry[1]) or unexist == True:
    #            features = []
    #            features2 = []
    #            for j in i[3]:
    #                features.append(dicts[2][1][j[1:]])
    #            for j in entry[2]:
    #                features2.append(dicts[2][0][j])
    #
    #            if unexist == True:
    #                new_i0 = [(original_word,i[0][0][1])]
    #            else:
    #                new_i0 = i[0]
    #            result.append((new_i0,i[1],i[2],features,features2,entry[1:]))
        feature_list = morph_to_feature(morph_entry,word_exist,word)
        result += feature_list

    # Some emergency processing
    if len(result) == 0:  # No word selected, we will loosen the condition
        for morph_entry in morph:
            feature_list = morph_to_feature(morph_entry,word_exist,word,False)
            result += feature_list
            
    return result

def tree_to_words(tree_name):
    global dicts
    if not dicts[3].has_key(tree_name):
        return []
    else:
        return dicts[3][tree_name]

def make_pos_mapping(s):
    lines = s.splitlines()
    mapping = {}
    for l in lines:
        if l.strip() == '':
            continue
        lr = l.split('->')
        if len(lr) != 2:
            raise ValueError('Not a valid line in the mapping file: %s\n' % (l))
        lr[0] = lr[0].strip()
        lr[1] = lr[1].strip()
        if mapping.has_key(lr[0]):
            raise KeyError('Key %s already exists!' % (lr[0]))
        mapping[lr[0]] = lr[1]

    return mapping

def init(morph,syntax,temp,default,mapping):
    # This function will initiate the environment where the XTAG grammar
    # system will run.
    # morph is the path of trunc_morph.flat
    # syntax is the path of syntax-coded.flat
    # temp is the path of templates.lex (there are two of them, both are OK)
    # All path can be absolute path or relative path
    """
    init(morph,syntax,temp) -> None

    Given the three dictionary files, the init() will initialize the environment
    for word_to_features() and other support functions to function. This should
    be the first call before any other calls to word_to_features().
    """
    global inited
    global dicts

    s = morph
    morph_dict = analyze_morph(s)

    default_syntax = default

    s = syntax
    s += "\n" + default_syntax
    # syntax_dict[0] is the dict for forward query, i.e. from word to trees and to feature structures
    # and syntax_dict[1] is the dict for reverse query, i.e. from tree name to entries (word or words)
    syntax_dict = analyze_syntax(s)

    s = temp
    template_dict = analyze_template(s)

    #### Do pos mapping
    mapping_dict = make_pos_mapping(mapping)
    ####

    dicts = (morph_dict,syntax_dict[0],template_dict,syntax_dict[1],mapping_dict)

    #### Patch for using default grammar: add '%s' into dicts[0] ####
    dicts[0]['%s'] = []
    default_morph_dict = dicts[0]['%s']
    for i in dicts[1]['%s']:
        entry = ('%s',i[0][0][1],[])
        if entry not in default_morph_dict:
            default_morph_dict.append(('%s',i[0][0][1],[]))
    ### Please Notice that there is not a line '%s' in the file, it is
    ### inserted here.
    
    inited = True
    
    return

def debug():
    morph = "../xtag-english-grammar/morphology/trunc_morph.flat"
    syntax = "../xtag-english-grammar/syntax/syntax-coded.flat"
    temp = "../xtag-english-grammar/syntax/templates.lex"
    default = "../xtag-english-grammar/syntax/syndefaults.dat"
    init(morph,syntax,temp,default)

    #print word_to_features('wzqw')
    for i in tree_to_words('Tnx0Vplnx1'):
        print i

def debug_make_rhs_using_or():
    fs = make_rhs_using_or('a/b/c')
    #fs['wzq'] = 'wer'
    print test_leaf(fs)

def debug_parse_feature_in_catalog():
    print parse_feature_in_catalog("<mode> = ind/imp <comp> = nil <wh> = <invlink>  <punct term> = per/qmark/excl <punct struct> = nil")

def debug_catalog():
    cata = get_catalog('../xtag-english-grammar/english.gram')
    print get_file_list(cata,"syntax-default")

def debug_get_path_list():
    path = 'Ad_f.t:<compar other wzq>'
    print get_path_list(path)

def debug_merge_fs():
    print fs1.unify(fs2)

def debug_remove_or_tag():
    print remove_or_tag(fs1)

def debug_modify_feature_entry():
    print modify_feature_entry(fs1,['apple'],'8888','1212121212')
    print '-------------------------'
    print fs1



def debug_parse_feature_in_catalog():
    print debug_start_feature

def debug_get_all_path():
    print get_all_path(debug_start_feature)

def debug_get_element_by_path():
    print get_element_by_path(fs1,['orange','less'])

def debug_fill_in_empty_entry():
    global debug_start_feature
    fs_test = copy.deepcopy(debug_start_feature)
    fs_test['comp'] = empty_feature
    fs_test['punct']['term'] = copy.deepcopy(empty_feature)
    debug_start_feature['wh'] = copy.deepcopy(empty_feature)
    debug_start_feature['mode'] = copy.deepcopy(empty_feature)
    print fs_test
    print '***********************************************'
    print debug_start_feature 
    fill_in_empty_entry(debug_start_feature,fs_test)
    fill_in_empty_entry(fs_test,debug_start_feature)
    print '***********************************************'
    print fs_test
    print '***********************************************'
    print debug_start_feature   

def debug_modify_feature_referece():
    modify_feature_reference(debug_start_feature,['punct','term'],'sdsdsdsd')
    print debug_start_feature

def debug_restore_reference():
    fs100 = FeatStruct()
    fs101 = FeatStruct()
    fs101['__or_1233454'] = '1233454'
    fs100['wzqqqqq'] = fs101
    fs102 = FeatStruct()
    fs102['sdsd'] = fs101
    result = debug_start_feature.unify(fs100)
    restore_reference(result,debug_start_feature,fs100)
    print result
    print '==================='
    result['wzqqqqq']['sdsd'] = 'ererer'
    print fs102
    print '==================='
    print result

def debug_test_contain():
    fs100 = FeatStruct()
    fs101 = FeatStruct()
    fs100['__or_123'] = 123
    fs101['__or_123'] = 123
    fs101['__or_456'] = 456
    fs100['__or_456'] = 456
    fs100['__or_789'] = 789
    print test_contain(fs100,fs101)

def debug_make_pos_mapping():
    s = """
    N -> N
    A -> A
    V -> V
    Ad -> Adv
    PL -> Part
    P -> Prep
    D -> Det
    Conj -> Conj
    Punct -> Punct
    I -> I
    G -> G
    Comp -> Comp
    """ 
    print make_pos_mapping(s)

def debug_word_to_features():
    word_to_features('be')

def debug_analyze_template():
    print analyze_template('@NOM-ACC-ASSIGN <assign-case>=nom/acc!')

if __name__ == "__main__":
    #debug_parse_feature_in_catalog()
    #debug_get_path_list()
    #debug_make_rhs_using_or()
    #debug()
    #debug_parse_feature_in_catalog()
    #debug_get_all_path()
    #debug_modify_feature_referece()
    #debug_restore_reference()
    #debug_test_contain()
    #debug_make_pos_mapping()
    #debug_word_to_features()
    debug_analyze_template()
