# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

from nltk.featstruct import FeatStruct
import re
import copy

#####################################################
# Operations on feature structures ##################
#####################################################

def remove_or_tag(feature):
    """
    :param feature: The feature structure that you want to remove the '__or_' tag
    :type feature: FeatStruct

    :return: A new feature structure with "__or_" removed and combined
    :rtype: FeatStruct

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
