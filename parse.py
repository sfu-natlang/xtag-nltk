# -*- coding: utf-8 -*-
from nltk.featstruct import FeatStruct
import re

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
    # This function is used to paese an expression. i.e. those strings identified
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

def get_catalog(filename):
    # Given the filename, this function is used to get the parse tree from
    # that file. Only call that once, and the parse tree can be used multiple
    # times to get options.
    fp = open(filename)
    s = fp.read()
    fp.close()

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
    get_option_value(cata,start-feature)
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

def make_fs(lhs,rhs):
    # This function makes a feature structure using a list of lhs which are nested
    # e.g. if lhs = ['a','b','c','d'] and rhs = 'wzq' then the
    # fs shoule be [a = [b = [c = [d = 'wzq']]]]
    """
    make_fs(lhs,rhs) -> FeatStruct

    Given the lhs list and rhs object, this fucntion will return a feature structure
    using the parameters above. The lhs must be given as a list which contains
    the left hand side tag in each level, and the rhs can be any type of objects
    But the most commonly used is string object or another feature structure.

    Also notice that this function will aotumatically add a "__value__" tag at
    the last level, making it easier for other procedures in XTAG system

    Example:
    lhs = ['a','b','c','d']
    rhs = 'wzq'
    Then make_fs(lhs,rhs) will return
    FeatStruct = [a = [b = [c = [d = [__value__ = 'wzq']]]]]
    """
    new_fs = FeatStruct()
    
    if len(lhs) == 1:
        inner = FeatStruct()
        inner['__value__'] = rhs
        rhs = inner
        new_fs[lhs[0]] = rhs
    else:
        new_fs[lhs[0]] = make_fs(lhs[1:],rhs)
        
    return new_fs

def add_new_fs(fs,lhs,rhs):
    """
    add_new_fs(fs,lhs,rhs) -> None

    This function will add the feature structure defined by lhs and rhs
    into an existing feature fs. The lhs of the lowest level is defined
    to be '__value__' to facilitate other procedures.

    If any of the paths defined by lhs has already existed in fs, then
    it will be merged into that existing path, instead of erasing the existing
    one and make a new one, so it is safe to use this function to merge two
    feature structures.

    Example:
    fs = [a = ['www']]
    lhs = ['a','b','c','d','e']
    rhs = 'wzq'
    Result:
    [a = ['www']                                  ]
    [    [b = [c = [d = [e = [__value__ = 'wzq']]]]
    """
    if len(lhs) == 1:
        inner = FeatStruct()


        inner['__value__'] = rhs
        rhs = inner
        fs[lhs[0]] = rhs
    else:
        if fs.has_key(lhs[0]):
            add_new_fs(fs[lhs[0]],lhs[1:],rhs)
        else:
            fs[lhs[0]] = FeatStruct()
            add_new_fs(fs[lhs[0]],lhs[1:],rhs)

def merge_fs(fs1,fs2):
    # This function merges fs2 into fs1, changing fs1 in-place
    # It's a cheaper and faster alternative of unify(), which will check
    # all the similarities and differences between fs1 and fs2. But this one
    # just assumes that fs2 and fs1 does not have any entries in common
    # NOTICE: In Templates.lex we cannot guarantee there is no overlap
    # so only use this function when it IS clear.
    for k in fs2.keys():
        fs1[k] = fs2[k]

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
    for l in lines:
        if l == '':
            continue
        start = 0
        entry_list = []
        tree_list = []
        family_list = []
        feature_list = []
        line_name = 'noname'
        while True:
            next_pair = get_next_pair(l,start)
            start = next_pair[2]
            entry = next_pair[0]
            value = next_pair[1]
            if start == -1:
                break
            elif entry == 'INDEX':
                line_name = value
            elif entry == 'ENTRY':
                entry_name = value
                next_pair = get_next_pair(l,start)
                start = next_pair[2]
                check_index(start)
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
    return tokens

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
                    fs = fs.unify(make_fs(path,rhs))
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
                    new_fs[node_type] = new_fs[node_type].unify(make_fs(lhs,rhs))
                else:
                    new_fs[node_type] = make_fs(lhs,rhs)
            if feature_list2.has_key(word_pos) == False:
                feature_list2[word_pos] = new_fs
            else:
                #feature_list2[word_pos].append(new_fs)
                raise KeyError('Duplicate defitinion detected: %s.' % (word_pos))
        else:
            raise TypeError('Cannot recognize line: %s.' % (l))
    return (feature_list,feature_list2)



# first_pass(s) will split the options and trees into a list, the first and second
# element of which is None, the third being the tree, and the fourth being
# the list of oprion, which will be processed in later phases
def first_pass(s):
    """
    first_pass() -> list

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

def second_pass(xtag_trees):
    """
    second_pass() -> list

    Given the result of first_pass(), this function will further
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

def third_pass(xtag_trees):
    """
    third_pass() -> list

    Given the result of second_pass(), this function will extract
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

def add_two_feature(features,l_id,rhs,l_feature1,l_feature2 = None):
    if l_feature2 == None:
        if features.has_key(l_id):
            features[l_id][l_feature1] = rhs
        else:
            features[l_id] = FeatStruct()
            features[l_id][l_feature1] = rhs
    else:
        if features.has_key(l_id):
            if features[l_id].has_key(l_feature1):
                features[l_id][l_feature1][l_feature2] = rhs
            else:
                features[l_id][l_feature1] = FeatStruct()
                features[l_id][l_feature1][l_feature2] = rhs
        else:
            features[l_id] = FeatStruct()
            features[l_id][l_feature1] = FeatStruct()
            features[l_id][l_feature1][l_feature2] = rhs
    return
    
def fourth_pass(xtag_trees):
    """
    fourth_pass() -> list

    Given the result of third_pass(), this function will make
    use of FeatStruct, and build a feature structure dictionary.  
    """
    for xtag_entry in xtag_trees:
        features =  {}
        for feature_entry in xtag_entry[1]:
            lhs = feature_entry[0]
            rhs = feature_entry[1]
            l_separator = lhs.find(':')
            r_separator = rhs.find(':')

            if r_separator == -1:
                l_id = lhs[:l_separator]
                l_space = lhs.find(' ')

                feat_rhs = FeatStruct()
                feat_rhs["__value__"] = rhs
                #feat_rhs = rhs                
                
                if(l_space == -1):
                    l_feature = lhs[l_separator + 2:-1]
                    add_two_feature(features,l_id,feat_rhs,l_feature)
                else:
                    l_feature1 = lhs[l_separator + 2:l_space]
                    l_feature2 = lhs[l_space + 1:-1]
                    add_two_feature(features,l_id,feat_rhs,l_feature1,l_feature2)

        xtag_entry[4] = features
    
    return xtag_trees

def fifth_pass(xtag_trees):
    """
    fifth_pass() -> list

    Given the result of fourth_pass(), this function will continue
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
                l_id = lhs[:l_separator]
                r_id = rhs[:r_separator]
                r_feature = rhs[r_separator + 2:-1]
                #print r_feature
                l_space = lhs.find(' ')

                if not features.has_key(r_id): # Make sure features[r_id] exists
                    features[r_id] = FeatStruct()
                    features[r_id][r_feature] = FeatStruct(__value__ = '')
                elif not features[r_id].has_key(r_feature): # Make sure features[r_id][r_feature] exists
                    features[r_id][r_feature] = FeatStruct(__value__ = '')

                if(l_space == -1):
                    l_feature = lhs[l_separator + 2:-1]
                    add_two_feature(features,l_id,features[r_id][r_feature],l_feature)
                else:
                    l_feature1 = lhs[l_separator + 2:l_space]
                    l_feature2 = lhs[l_space + 1:-1]
                    add_two_feature(features,l_id,features[r_id][r_feature],l_feature1,l_feature2)

    return xtag_trees

def parse_feature(filename):
    """
    parse_feature() -> list

    Given the name of the file which contains the definition
    of several TAG trees, this function will return a data structure that
    describes those trees as well as options including feature structures.  
    """
    fp = open(filename)
    s = fp.read()
    fp.close()

    return fifth_pass(fourth_pass(third_pass(second_pass(first_pass))))

def remove_value_tag(feature):
    new_feature = FeatStruct()
    for i in feature.keys():
        if feature[i].has_key('__value__'):
            new_feature[i] = feature[i]['__value__']
        else:
            new_feature[i] = remove_value_tag(feature[i])
    return new_feature

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
        if val.has_key('__value__'):
            #search_ret = re.search(regexp,val['__value__'])
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
    fp = open(morph)
    s = fp.read()
    morph_dict = analyze_morph(s)
    fp.close()

    fp = open(default)
    default_syntax = fp.read()
    fp.close()

    fp = open(syntax)
    s = fp.read()
    s += "\n" + default_syntax
    syntax_dict = analyze_syntax(s)
    fp.close()

    fp = open(temp)
    s = fp.read()
    template_dict = analyze_template(s)
    fp.close()

    dicts = (morph_dict,syntax_dict,template_dict)

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

    print word_to_features('wzqw')


def debug_parse_feature_in_catalog():
    print parse_feature_in_catalog("<mode> = ind/imp <comp> = nil <wh> = <invlink>  <punct term> = per/qmark/excl <punct struct> = nil")

def debug_catalog():
    cata = get_catalog('../xtag-english-grammar/english.gram')
    print get_file_list(cata,"syntax-default")

if __name__ == "__main__":
    #debug_parse_feature_in_catalog()
    debug()
