# -*- coding: utf-8 -*-
# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

# -*- coding: utf-8 -*-
from nltk.featstruct import FeatStruct
import re
import copy

###########################################
# LL Parser for catalog file ##############
###########################################

# Do not call these functions from the outside! Only be used by the parser

def get_next_token(s,index,length=None):
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

catalog_name = {}

def add_new_name(s,index):
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
    # This function will generate a string using the defined ifentifier name
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
    # This function will evaluate those "expressions" defined by 'setf' or
    # 'concatenate', and dispatch them to the corresponding functions
    # No other expression typeare supported for now
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

def get_file_tree(node,type_string):
    # DON'T DIRECTLY CALL THIS
    # Given the root node of the parsing tree, and the file type that you want
    # to extract, this function will return the tree containing the list
    # of the files of that type.
    # Legal file type:
    # 
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
    # Given the root node of the parse tree, and the file type
    # you want to get, this function will return a list containing
    # the file names as well as the absolute path of the files.
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

opt_value = None

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

#####################################################
# Operations on feature structures ##################
#####################################################

def remove_or_tag(feature):
    """
    remove_or_tag(FeatStruct) -> FeatStruct

    Given a feature structure in the internal repersentation of our xtag system
    (i.e. each leaf is wrapped with an '__or_' + lhs feature struct), this function
    will get rid of the __or_ tag, and produce a feature structure where no __or_
    is there, and the multiple or relation is represented as [__or_1]/[__or_2]/ ...

    e.g. for fs = [apple = [__or_a = 'a']]
                  [        [__or_b = 'b']]
                  [        [__or_c = 'c']]
                  
    remove_or_tag(fs) will return:

      fs_return = [apple = 'a/b/c']
    """
    new_feature = FeatStruct()
    for key in feature.keys():
        entry = feature[key]
        entry_keys = entry.keys()
        if test_leaf(entry) == True:
            str_or_removed = entry[entry_keys[0]]
            if len(entry_keys) > 1:
                for i in entry_keys[1:]:
                    str_or_removed += '/' + entry[i]
                    
            new_feature[key] = str_or_removed
        else:
            new_feature[key] = remove_or_tag(feature[key])
    return new_feature

def make_rhs_using_or(rhs):
    """
    make_rhs_using_or(string) -> FeatStruct

    This function will return a feature structure which satisfies the
    requirement for implementing the 'or' relationship in the xtag grammar.
    rhs must be a string, whose value will be used to construct the lhs
    inside the new feature structure. For example, if rhs = a/b/c then the
    result will be:
    [       [ __or_a = a ] ]
    [ rhs = [ __or_b = b ] ]
    [       [ __or_c = c ] ]
    """
    new_fs = FeatStruct()
    slash = rhs.find('/')
    if slash == -1:
        rhs = [rhs]
    else:
        rhs = rhs.split('/')
    # After this rhs is a list containing the entities in the 'or' relation
    for i in rhs:
        lhs = '__or_' + i
        new_fs[lhs] = i
    return new_fs

def test_leaf(fs):
    """
    test_leaf(FeatStruct) -> Bool

    This function will test whether a feature structure is a leaf node in
    the directed graph, by testing all of its keys to see if there is a
    prefix '__or_' for every left hand side (lhs) string. If this is true
    then we can make sure that we have reached the bottom of the feature structure
    graph, and the function will return true, and for some recursivelly
    implemented procedures this means the recursion will return.
    """
    is_leaf = False
    keys = fs.keys()
    for i in keys:
        if i[0:5] != '__or_':
            break
    # This will be executed if we've not met a break
    # in the for loop, which means all lhs are satisfied
    else: 
        is_leaf = True
        
    return is_leaf

def test_single_entry(fs):
    """
    test_single_entry(FeatStruct) -> Bool

    This function will test whether a given leaf node is a single entry
    node, which means that if we want to modify this node we need not to
    specify the LHS.

    If the feature structure given is not a leaf node then an error will be
    raised.

    For example: fs = [apple = [orange = [__or_123 = '123']]]
                 test_single_entry = True
                 
                 fs = [apple = [orange = [__or_123 = '123']]]
                      [                  [__or_456 = '456']]]
                 test_single_entry = False
    """
    if test_leaf(fs) == False:
        raise ValueError('The feature structure is not a leaf node')
    else:
        keys = fs.keys()
        if len(keys) == 1:
            return True
        else:
            return False

def test_empty_entry(fs):
    """
    test_empty_entry(FeatStruct) -> Bool

    This function will test whether a given feature structuer is an empty entry fs.
    An empty entry fs is defined not as an empty entry (i.e. []), it is defined
    as strictly [__or_ = '']. Only this feature structure will cause a return
    value of True, otherwise it will return False.
    """
    if fs.has_key('__or_') and len(fs.keys()) == 1:
        return True
    else:
        return False
    
def make_leaf_str(rhs):
    """
    make_leaf_str(str) -> str

    This simple function is mainly used to construct the LHS string using
    an RHS string. For the current stage we just append a '__or_' to it.

    For example: rhs = 'wzq'
                 make_leaf_str(rhs) = '__or_wzq'
    """
    return '__or_' + rhs

def make_fs(lhs,rhs,ref=0):
    # This function makes a feature structure using a list of lhs which are nested
    # e.g. if lhs = ['a','b','c','d'] and rhs = 'wzq' then the
    # fs shoule be [a = [b = [c = [d = 'wzq']]]]
    """
    make_fs(lhs,rhs) -> FeatStruct

    Given the lhs list and rhs object, this fucntion will return a feature structure
    using the parameters above. The lhs must be given as a list which contains
    the left hand side tag in each level, and the rhs can be any type of objects
    But the most commonly used is string object or another feature structure.

    Also notice that this function will aotumatically add a "__or_" + rhs tag at
    the last level, making it easier for other procedures in XTAG system

    Example:
    lhs = ['a','b','c','d']
    rhs = 'wzq'
    Then make_fs(lhs,rhs) will return
    FeatStruct = [a = [b = [c = [d = [__or_wzq = 'wzq']]]]]
    """
    new_fs = FeatStruct()
    
    if len(lhs) == 1:
        #inner = FeatStruct()
        #inner['__value__'] = rhs
        #rhs = inner
        # if ref == 0 then we are not making references so we will process
        # rhs, and it must be a string
        if ref == 0:
            rhs = make_rhs_using_or(rhs)
        elif ref == 1:
            rhs = rhs # Do nothing
        else:
            raise ValueError('Undefined ref value %d' % (ref))
        
        new_fs[lhs[0]] = rhs
    else:
        new_fs[lhs[0]] = make_fs(lhs[1:],rhs,ref)
        
    return new_fs

def add_new_fs(fs,lhs,rhs,ref=0):
    """
    add_new_fs(fs,lhs,rhs) -> None

    This function will add the feature structure defined by lhs and rhs
    into an existing feature fs. The lhs of the lowest level is defined
    to be '__or_' + rhs to facilitate other procedures.

    If any of the paths defined by lhs has already existed in fs, then
    it will be merged into that existing path, instead of erasing the existing
    one and make a new one, so it is safe to use this function to merge two
    feature structures.

    Example:
    fs = [a = ['www']]
    lhs = ['a','b','c','d','e']
    rhs = 'wzq'
    Result:
    [a = [['www']                                 ]
    [    [b = [c = [d = [e = [__or_wzq = 'wzq']]]]
    """
    if len(lhs) == 1:
        #inner = FeatStruct()
        #inner['__value__'] = rhs
        #fs[lhs[0]] = inner
        # ref means reference. If we are not making reference, then rhs must
        # be a string, and we will process that string
        # But if ref == 1 then we are just making references, so we will not
        # process rhs, but only attach it to the existing feature structure
        if ref == 0:
            fs[lhs[0]] = make_rhs_using_or(rhs)
        elif ref == 1:
            fs[lhs[0]] = rhs
        else:
            raise ValueError('Undefined ref value %d' % (ref))
    else:
        if fs.has_key(lhs[0]):
            add_new_fs(fs[lhs[0]],lhs[1:],rhs,ref)
        else:
            fs[lhs[0]] = FeatStruct()
            add_new_fs(fs[lhs[0]],lhs[1:],rhs,ref)

def merge_fs(fs1,fs2):
    # This function merges fs2 into fs1, changing fs1 in-place
    # It's a cheaper and faster alternative of unify(), which will check
    # all the similarities and differences between fs1 and fs2. But this one
    # just assumes that fs2 and fs1 does not have any entries in common
    # NOTICE: In Templates.lex we cannot guarantee there is no overlap
    # so only use this function when it IS clear.
    for k in fs2.keys():
        if fs1.has_key(k):
            merge_fs(fs1[k],fs2[k])
        else:
            fs1[k] = fs2[k]
    return

def parse_feature_in_catalog(s):
    # This function parses the string in catalog file, i.e. english.gram
    # with the option 'start-feature', into a FeatStruct. We MUST write
    # separate parsers for different strings from different files, since
    # these features are represented in different forms.
    """
    parse_feature_in_catalog(string) -> FeatStruct

    Given the string, this function will return a feature structure parsed
    from that string. The feature structure should be encoded like this:

    <mode> = ind/imp <comp> = nil <wh> = <invlink>  <punct term> = per/qmark/excl <punct struct> = nil
    
    All tokens shall be separated by a single space, no comma and period and
    semicolon is used. This parses is designed specially for the string from
    the catalog (i.e. english.gram) file, since there are multiple ways to
    represent the FS in xtag grammar, so we need multiple parsers.
    """
    # token _list is a list of tuples, the element of which is the LHS and
    # RHS of a feature structure definition, i.e. [('mode','ind/imp'),('comp','nil')]
    token_list = []
    while True:
        equal_sign = s.find('=')
        if equal_sign == -1:
            break
        # find between '=' and '<', which is the RHS if no "<LHS> = <RHS>"
        # is used. If it is then we can know that the no-white string between
        # '=' and '<' is an empty string.
        angle_bracket = s.find('<',equal_sign)
        if angle_bracket == -1:
            rhs = s[equal_sign + 1:].strip()
        else:
            rhs = s[equal_sign + 1:angle_bracket].strip()
            if rhs == '':
                angle_bracket = s.find('<',angle_bracket + 1)
                if angle_bracket == -1:
                    rhs = s[equal_sign + 1:].strip()
                else:
                    rhs = s[equal_sign + 1:angle_bracket].strip()
        lhs = s[:equal_sign].strip()[1:-1]
        token_list.append((lhs,rhs))
        s = s[angle_bracket:]

    new_fs = FeatStruct()
    for token in token_list:
        add_new_fs(new_fs,token[0].split(),token[1])

    return new_fs

def get_start_feature(node):
    s = get_option_value(node,'start-feature')
    return parse_feature_in_catalog(s)

#########################################################
# Feature Structure Function For Future Use #############
#########################################################

def modify_feature_reference(feature,path,ref):
    """
    Change the reference of a node

    :param feature: The feature structure to change
    :type feature: FeatStruct

    :param path: The path in the feature structure to change
    :type path: list(str)

    :param ref: Anything that will be put to the path as the reference
    :type ref: Any Object

    This function is almost the same as modify_feature_entry, except that
    it will only change the reference.

    This function will change the feature structure in-place.
    
    e.g. fs = [apple = [orange = [__or_wzq = 'wzq']]]
                       [         [__or_123 = '123']]]
         path = ['apple','orange']
         ref = [__or_qwer = 'qwer']
         modify_feature_reference(fs,path,ref) ->
                       [apple = [orange = [__or_qwer = 'qwer']]         
    """
    current_fs = feature
    # Only go (n-1) steps, where n is the length of the path
    for node in path[:-1]:
        if current_fs.has_key(node):
            current_fs = current_fs[node]
        else:
            raise KeyError('No such node %s in the feature structure' % (node))

    current_fs[path[-1]] = ref # Change the reference
    
    return  

def modify_feature_entry(feature,path,rhs,lhs=None):
    """
    modify_feature_entry(FeatStruct,list,str,str) -> FeatStruct

    This function is called when the user would like to modify the value
    of some entry in a feature structure. The path is a list containing
    the LHSs of all levels along the path (must be valie, i.e. all LHSs
    must exist), and rhs is the value we want to modify. In this case
    the value of lhs will be ignored, but you can always add one in order
    to achieve some consistency.

    For example, fs = [apple = [orange = [__or_wzq = 'wzq']]]
                 path = [apple,orange], rhs = 'www'
                 modify_feature_entry(fs,path,rhs) ->
                      [apple = [orange = [__or_www = 'www']]]

    Because the internal repersentation of the feature structure is different
    from what it looks like, i.e. we adapted the (__or_ + lhs) lhs to deal with
    the situation where we must handle "or" relation in one feature structure
    which is not supported by FeatStruct (or we cannot find a more simpler one).
    So the function provides another parameter called lhs, which is by default
    a None object, but you can assign value to it under some condition. If the
    target feature struct is a __or_ structure, which has multiple __or_ entries
    you must specify which one you would like to modify, or if it is detected that
    there are multiple entries but no lhs was specified, the function will throw
    out an error.

    Also notice that lhs is the string where __or_ is removed, or to say, lhs
    is actually the old rhs of the entry which we want to remove.

    For example, fs = [apple = [orange = [__or_wzq = 'wzq']]]
                      [                  [__or_123 = '123']]]
                 path = [apple,orange], rhs = 'www', lhs = 'wzq'
                 modify_feature_entry(fs,path,rhs,lhs) ->
                      [apple = [orange = [__or_www = 'www']]]
                      [                  [__or_123 = '123']]]
    """
    # We must make a copy of the feature and modify on that copy
    # or the original feature structure will be affected and other
    # operations may get undefined error.
    current_fs = copy.deepcopy(feature)
    # Make a copy pointer points to the whole fs, in order to return it in the
    # future. Because current_fs will be changed and cannot come back.
    returned_fs = current_fs
    for node in path:
        if current_fs.has_key(node):
            current_fs = current_fs[node]
        else:
            raise KeyError('No such node %s in the feature structure' % (node))

    if test_single_entry(current_fs) == True:
        # Remove the only entry, since we have been assurred there is only 1
        current_fs.pop(current_fs.keys()[0])
    else:
        current_fs.pop('__or_' + lhs)
    current_fs['__or_' + rhs] = rhs
    
    return returned_fs

def get_all_path(fs):
    """
    get_all_path(FeatStruct) -> list[list,list,...]

    This function will retuen all possible paths in a feature structure. The
    term path means one way from the root to a leaf (not including __or_ level)
    and each path is repersented by a list, the element of which is the node name
    (i.r. LHS in the feature structure).

    The return value itself is also a list, which contains all paths in the
    feature structure given.

    For example:

    fs = 

    [ comp  = [ __or_nil = 'nil' ]                  ]
    [                                               ]
    [ mode  = [ __or_imp = 'imp' ]                  ]
    [         [ __or_ind = 'ind' ]                  ]
    [                                               ]
    [         [ struct = [ __or_nil = 'nil' ]     ] ]
    [         [                                   ] ]
    [ punct = [          [ __or_excl  = 'excl'  ] ] ]
    [         [ term   = [ __or_per   = 'per'   ] ] ]
    [         [          [ __or_qmark = 'qmark' ] ] ]
    [                                               ]
    [ wh    = [ __or_<invlink> = '<invlink>' ]      ]

    result = 
    
    [['comp'], ['punct', 'term'], ['punct', 'struct'], ['mode'], ['wh']]
    """
    this_level = []
    for key in fs.keys():
        entry = fs[key]
        if test_leaf(entry) == True:
            this_level.append([key])
        else:
            next_level = get_all_path(entry)
            for i in next_level:
                i.insert(0,key)
            this_level += next_level

    return this_level

def get_element_by_path(fs,path):
    """
    get_element_by_path(FeatStruct,list) -> FeatStruct / None

    This function will return the entry in feature struct using the path given.
    If the path does not exist then it will return a None object, so please
    check the result value before using it. If the return value is not None
    then it is the entry fetched using the path, which is a list containing
    all nodes along the path down from the root to a certain node.

    For example:

    fs =    [          [ __or_a   = 'a'   ]              ]
            [ apple  = [ __or_qwe = 'qwe' ]              ]
            [          [ __or_wzq = 'wzq' ]              ]
            [                                            ]
            [ orange = [ more = [ __or_4567 = '4567' ] ] ]
            [          [        [ __or_zxcv = 'zxcv' ] ] ]
    path = ['orange','more']
    return =    [ __or_4567 = '4567' ]
                [ __or_zxcv = 'zxcv' ]

    path = ['orange','less']
    return = None
    """
    current_fs = fs
    for node in path:
        if current_fs.has_key(node):
            current_fs = current_fs[node]
        else:
            return None
    return current_fs

def restore_reference(new_feat,old_feat_1,old_feat_2):
    """
    Restore the reference relationship after doing unify to a feature structure.

    :param new_feat: The feature structure after unification
    :type new_feat: FeatStruct

    :param old_feat_1: One of the feature structure before unification
    :type old_feat_1: FeatStruct

    :param old_feat_2: Another feature structure before unification
    :type old_feat_2: FeatStruct

    :return: The modified feature strucrture
    :rtype: FeatStruct

    This function is used to solve the problem that in the feature structure set
    of a tree, which consists of many feature structures of different nodes, where
    many of the structures share the same RHS value, and these value is repersented
    by independent feature structures, i.e. the '__or_' entity. But the unification
    routine provided by the NLTK library will not consider these references, and
    it only re-creates everything and will not do a in-place change. So we need
    to restore these references.

    To do this we only need to compare between the new and old feature structures
    and copy the reference if they share common paths, or create new enteies.
    """
    path_1 = get_all_path(old_feat_1)
    path_2 = get_all_path(old_feat_2)
    for i in path_1:
        new_entry = get_element_by_path(new_feat,i)
        if new_entry != None:  # That path exists
            old_entry = get_element_by_path(old_feat_1,i) # Must return a result
            # If there is __or_ then these two can be different so we must check
            # But __or_ may also produce a brand-new feature struct, in this case
            # no work should be done.
            # e.g. [__or_123 = '123']
            #      [__or_456 = '456'] unified with [__or_456 = '456']
            # will return exactly the first one, and the reference goes to
            # the first one. But if [__or_123 = '123'] and [__or_456 = '456']
            # are unified, then the result is independent of both.
            if old_entry == new_entry:  
                modify_feature_reference(new_feat,i,old_entry)

    for i in path_2:
        new_entry = get_element_by_path(new_feat,i)
        if new_entry != None:
            old_entry = get_element_by_path(old_feat_2,i)
            if old_entry == new_entry:
                modify_feature_reference(new_feat,i,old_entry)
    return

def fill_in_empty_entry(fs1,fs2):
    """
    fill_in_empty_entry(FeatStruct,FeatStruct) -> None

    This function will try to find common entries between the two feature
    structures, and if one of them is of empty value, then we will rewrite
    it using the value in another feature structure. Only those whose path
    is the same and one of them is empty while one of them while another is
    not, will be rewritten.

    If both entries are empty, although it is very weird, we will let it pass
    since this is not a fatal error. And if both are not empty, but their values
    are different, then it is natural that this entry will be deleted during
    unification, so we also won't say anything about that.

    Besides, this function will only check all possible paths in fs1, and then
    rewrite all entries found qualified in fs2. But in practice
    we usually want a symmetric result, i.e. the value of the unification is
    indepedent of the order in which the two feature structures are given. So
    it is proper practice to call this function two times, with the parameters
    exchanged, to ensure that all paths available have been checked.

    e.g. fill_in_empty_entry(fs1,fs2)
         fill_in_empty_entry(fs2,fs1)

    What's more, this function will change fs1 and fs2, so if you are
    not expecting this kind of behaviour, then just make a deepcopy of the fs
    before calling this function.
    """
    all_path = get_all_path(fs1)
    for p in all_path:
        old_value = get_element_by_path(fs2,p)
        if old_value != None: # Such path exist in fs2
            overwrite_value = get_element_by_path(fs1,p)
            # Need to test respectively whether the entry is empty
            if test_empty_entry(old_value) == True and test_empty_entry(overwrite_value) == False:
                for i in overwrite_value.keys():
                    old_value[i] = overwrite_value[i]
                old_value.pop('__or_') # Remove the '__or_' entry
    return
                
                        
            
    
############################################
# Analyze Morphology File ##################
############################################

def analyze_morph(s):
    # The return value is a dictionary using words in the sentence as index. The
    # entry is a list, the element of which is a tuple. The first element of the
    # tuple is the lexicon, the second element of the tuple is the type of this lex,
    # and the third element of the tuple is again a list 
    # the entries of which are strings indicating the features.
    """
    analyze_morph(string) -> dictionary
    
    This function accepts input as a string read form file 'morph_english.flat'
    which contains the morphology information of XTAG system. The output is a
    dictionary using a single word as index and returns the morphology entry.
    """
    morph = {}
    lines = s.splitlines()
    for l in lines:
        if l == '':
            continue

        sub_line = []
        start = 0
        while True:
            index = l.find('#',start)
            if index == -1:
                sub_line.append(l[start:].split())
                break
            else:
                sub_line.append(l[start:index].split())
                start = index + 1
        #print sub_line
        morph_list = []
        for i in range(0,len(sub_line)):
            m = sub_line[i]
            if i == 0:
                morph_list.append((m[1],m[2],m[3:]))
            else:
                morph_list.append((m[0],m[1],m[2:]))
                
        morph[sub_line[0][0]] = morph_list
        
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

def analyze_syntax(s):
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
        for tree in tree_list:
            if not reverse_trees.has_key(tree):
                reverse_trees[tree] = []
            reverse_trees[tree].append(entry_list[:])
        for tree in family_list:
            if not reverse_trees.has_key(tree):
                reverse_trees[tree] = []
            reverse_trees[tree].append(entry_list[:])
        #print entry_list
            
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
                    if rhs[0] == '@':      # rhs can also be reference
                        rhs = feature_list[rhs[1:]]
                    if lhs[0] != '<' or lhs[-1] != '>':
                        raise TypeError('The left hand side of a feature structure must be wrapped with <>')
                    lhs = lhs[1:-1]
                    path = lhs.split()
                    #path.reverse()    # This method is in-place
                    fs = fs.unify(make_fs(path,rhs,1))
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
    analyze_tree_1() -> list

    Given the raw string read from a grammar document, this
    function will split the options and TAG trees into a list.  
    """
    i = 0
    last_time = 0    # To record the position since the latest ')'
    stack = 0  # We use a simple stack to match brackets

    # Store final result, it is a list of list
    xtag_trees = []    
    options = None
    single_tree = None
    
    is_option = True
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
                xtag_trees.append([None,None,single_tree.strip(),option.strip(),None]) #None here is a placeholder

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

#def parse_feature(filename):
#    """
#    parse_feature() -> list

#    Given the name of the file which contains the definition
#    of several TAG trees, this function will return a data structure that
#    describes those trees as well as options including feature structures.  
#    """
#    fp = open(filename)
#    s = fp.read()
#    fp.close()
#
#    return fifth_pass(fourth_pass(third_pass(second_pass(first_pass))))

#def remove_value_tag(feature):
#    new_feature = FeatStruct()
#    for i in feature.keys():
#        if feature[i].has_key('__value__'):
#            new_feature[i] = feature[i]['__value__']
#        else:
#            new_feature[i] = remove_value_tag(feature[i])
#    return new_feature
            

# This function acceps a normalized feature structure (which uses __value__
# as the last level of indexing) and a regular expression, and returns
# a new feature structure that match the regexp or do not match.
def match_feature(feature,regexp,operation=0):
    """
    match_feature(feature,regexp,operation=0) -> FeatStruct

    This function is used to filter a feature structure with a regular exression.
    The regular expression should be written in the form that XTAG system uses,
    which has a '__value__' entry at the last level of indexing.

    feature: The feature that you would like to filter

    regexp: An acceptable regular expression by module re

    operation: 0 if positive filtering will be done, 1 if negative filtering.
    positive filtering means that all RHS values that match the regexp will be
    retained, while negative filtering means that all RHS values that doesn't
    match will be retained.
    """
    new_feature = FeatStruct()
    count = 0
    for i in feature.keys():
        val = feature[i]
        if test_leaf(val) == True:
            search_ret = re.search(regexp,i)
            if operation == 0 and search_ret != None:
                new_feature[i] = val
                count += 1
            elif operation == 1 and search_ret == None:
                new_feature[i] = val
                count += 1
        else:
            search_ret = re.search(regexp,i)
            if operation == 0 and search_ret != None:
                new_feature[i] = val
                count += 1
            elif operation == 1 and search_ret == None:
                ret = match_feature(val,regexp,operation)
                if ret != None:
                    new_feature[i] = ret
                else:
                    new_feature[i] = FeatStruct()
                count += 1
            elif operation == 1 and search_ret != None:
                pass
            else:
                ret = match_feature(val,regexp,operation)
                #print ret,'\n'
                if ret != None:
                    new_feature[i] = ret
                    count += 1

    #print new_feature,'\n'
    if count == 0:
        return None
    else:
        return new_feature

dicts = None
inited = False

def word_to_features(word):
    # This function will convert the word into the feature structures associated
    # with this word. The return value of this function is a list, each element
    # of which is a tuple. The element of the list is the morph of the word.
    # NOTICE: This function must be run after init() be called, or it will
    # throw the exception.
    """
    word_to_features(word) -> list

    Give a word of any form, e.g. take, took, taken, taking, this function will
    return a list of all possible features of this word. The return value is a
    list containing all possibilities.

    To run this function, the initialization procedure init() must be called, or
    an exception will be thrown.
    """
    if inited == False:
        raise KeyError("Initial file name not provided. Please run init() first.")

    global dicts
    result = []
    #print dicts[0][word]
    # If this word doesn't exist then we will just make a mark, and inside the loop
    # we will just use the syntax from syndefaults.dat instead of from dicts[1]
    if not dicts[0].has_key(word):
        unexist = True
        original_word = word
        word = '%s'
    else:
        unexist = False
    for entry in dicts[0][word]:
        #print entry
        if unexist == False:
            temp_feature = dicts[1][entry[0]]
        else:
            temp_feature = dicts[1]['%s']
        
        for i in temp_feature:
            #print entry[0], " ",i[0][0][0]
            #print entry[1],"",i[0][0][1]
            if (i[0][0][0] == entry[0] and i[0][0][1] == entry[1]) or unexist == True:
                features = []
                features2 = []
                for j in i[3]:
                    features.append(dicts[2][1][j[1:]])
                for j in entry[2]:
                    features2.append(dicts[2][0][j])

                if unexist == True:
                    new_i0 = [(original_word,i[0][0][1])]
                else:
                    new_i0 = i[0]
                result.append((new_i0,i[1],i[2],features,features2,entry[1:]))
                
    return result
        #print dicts[1][entry[0]]

def tree_to_words(tree_name):
    global dicts
    return dicts[3][tree_name]

def init(morph,syntax,temp,default):
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
    #fp = open(morph)
    s = morph
    morph_dict = analyze_morph(s)
    #fp.close()

    #fp = open(default)
    default_syntax = default
    #fp.close()

    #fp = open(syntax)
    s = syntax
    s += "\n" + default_syntax
    # syntax_dict[0] is the dict for forward query, i.e. from word to trees and to feature structures
    # and syntax_dict[1] is the dict for reverse query, i.e. from tree name to entries (word or words)
    syntax_dict = analyze_syntax(s)
    #print default_syntax
    #fp.close()

    #fp = open(temp)
    s = temp
    template_dict = analyze_template(s)
    #fp.close()

    dicts = (morph_dict,syntax_dict[0],template_dict,syntax_dict[1])

    #### Patch for using default grammar: add '%s' into dicts[0] ####
    temp = dicts[1]['%s']
    dicts[0]['%s'] = []
    for i in temp:
        dicts[0]['%s'].append(('%s',i[0][0][1],""))
    ###
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

fs1 = FeatStruct()
fs2 = FeatStruct()
fs3 = FeatStruct()
fs4 = FeatStruct()
fs4['more'] = fs3
fs2['__or_a'] = 'a'
fs2['__or_wzq'] = 'wzq'
fs2['__or_qwe'] = 'qwe'
fs1['apple'] = fs2
fs1['orange'] = fs4
fs3['__or_zxcv'] = 'zxcv'
fs3['__or_4567'] = '4567'

def debug_merge_fs():
    print fs1.unify(fs2)

def debug_remove_or_tag():
    print remove_or_tag(fs1)

def debug_modify_feature_entry():
    print modify_feature_entry(fs1,['apple'],'8888','1212121212')
    print '-------------------------'
    print fs1

debug_start_feature = parse_feature_in_catalog('<mode> = ind/imp <comp> = nil <wh> = <invlink>  <punct term> = per/qmark/excl <punct struct> = nil')
empty_feature = FeatStruct()
empty_feature['__or_'] = ''

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
    

if __name__ == "__main__":
    #debug_parse_feature_in_catalog()
    #debug_get_path_list()
    #debug_make_rhs_using_or()
    #debug()
    #debug_parse_feature_in_catalog()
    #debug_get_all_path()
    #debug_modify_feature_referece()
    debug_restore_reference()
