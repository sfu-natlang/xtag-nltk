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

#################################
# Node testing functions ########
#################################

def test_leaf(fs):
    """
    :param fs: The feature you want to test
    :type fs: FeatStruct

    :return: True means this is a leaf node, including a multiple entry "__or_"
    node or a single entry node.
    :rtype: bool

    This function will test whether a feature structure is a leaf node in
    the directed graph, by testing all of its keys to see if there is a
    prefix '__or_' for every left hand side (lhs) string. If this is true
    then we can make sure that we have reached the bottom of the feature structure
    graph, and the function will return true, and for some recursivelly
    implemented procedures this means the recursion will return.

    Also please note that we cannot expect a mixture of '__or_' and non '__or_'
    entry, this is an inconsistency. But this function will not throw exception
    and will just return a False (because a non '__or_' is detected)

    [__or_123 = 123]
    [__or_456 = 456] --> return True

    [apple = [__or_red = red]] --> return False
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
    :param fs: The feature structure that you want to test
    :type fs: FeatStruct

    :return: True if the fs is a single entry node, False if not.

    This function will test whether a given leaf node is a single entry
    node, which means that if we want to modify this node we need not to
    specify the LHS.

    If the feature structure given is not a leaf node then an excaption will be
    raised. For example:

    fs = [__or_123 = '123'] -> True
                 
    fs = [__or_123 = '123']
         [__or_456 = '456'] -> False

    fs = [apple = [__or_123 = '123']] -> exception
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
    :param fs: The feature structure that you want to test
    :type fs: FeatStruct

    :return: True if it is an empty entry, False if not
    :rtype: bool

    This function will test whether a given feature structuer is an empty entry fs.
    which has the form [__or_ = ''], and this is the only form that will cause
    a True to be returned. In other situations a False will be returned.
    """
    if fs.has_key('__or_') and len(fs.keys()) == 1:
        return True
    else:
        return False

def test_contain(fs1,fs2):
    """
    Test if one feature structure contains another, i.e. is the super set of another.

    :param fs1: The first feature structure you want to test
    :type fs1: FeatStruct
    :param fs2: The second feature structure you wang to test
    :type fs2: FeatStruct
    :return: 0 if they are equal to each other
             1 if fs1 is a subset of fs2
            -1 if fs2 is a subset of fs1
    FeatStruct if there is some intersection
          None if there is no intersection

          One exception is that, if the two fs are both empth then we will return
          equal instead of None.
    :rtype: integer/FeatStruct/None

    This function requires that fs1 and fs2 are leaf nodes, if they are not then an
    an exception will be raised. Besides, since in a leaf node the left hand side
    is actually derivable from the right hang side, so if we know one we can know
    another. Based on this observation we just make comparisions to the left hand
    side, i.e. keys().
    """
    if test_leaf(fs1) == False or test_leaf(fs2) == False:
        raise ValueError('Two arguments must be leaf nodes.')
    key_1 = fs1.keys()
    key_2 = fs2.keys()
    new_key_1 = []
    new_key_2 = []
    for i in key_1:
        if i in key_2:
            new_key_1.append(i)
    for i in key_2:
        if i in key_1:
            new_key_2.append(i)
    len_1 = len(key_1)
    len_2 = len(key_2)
    new_len_1 = len(new_key_1)
    new_len_2 = len(new_key_2)
    # Now new_len_1 and new_len_2 are the same keys in both fs, or both []
    # means no same keys
    #print new_key_1
    #print new_key_2
    if new_len_1 == 0 and new_len_2 == 0:
        return None
    elif len_1 != new_len_1 and len_2 != new_len_2:
        ret = FeatStruct()
        for i in new_key_1:
            ret[i] = fs1[i]
        return ret
    elif len_1 == new_len_1 and len_2 != new_len_2:
        return 1 # len_1 not changed, it is contained in len_2
    elif len_1 != new_len_1 and len_2 == new_len_2:
        return -1 # len_2 contained in len_1
    else:
        return 0 # Neigher has changed, so they are equal

##############################
# Node Constructing ##########
##############################

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

def make_leaf_str(rhs):
    """
    :param rhs: A string in the right hand side
    :type rhs: str

    :return: The string with a '__or_' attached as prefix
    :rtype: str

    This simple function is mainly used to construct the LHS string using
    an RHS string. For the current stage we just append a '__or_' to it.

    For example:

    rhs = 'wzq'
    -> '__or_wzq'
    """
    return '__or_' + rhs

def make_rhs_using_or(rhs):
    """
    :param rhs: The right hand string which may contain the 'or' relationship
    :type rhs: str

    :return: A feature structure using '__or_' structure
    :rtype: FeatStruct

    This function will return a feature structure which satisfies the
    requirement for implementing the 'or' relationship in the xtag grammar.
    rhs must be a string, whose value will be used to construct the lhs
    inside the new feature structure.

    For example,

    rhs = a/b/c ->  [ __or_a = a ]
                    [ __or_b = b ]
                    [ __or_c = c ]
    """
    new_fs = FeatStruct()
    slash = rhs.find('/')
    if slash == -1:
        rhs = [rhs]
    else:
        rhs = rhs.split('/')
    # After this rhs is a list containing the entities in the 'or' relation
    for i in rhs:
        lhs = make_leaf_str(i)
        new_fs[lhs] = i
    return new_fs

def make_fs(lhs,rhs,ref=0):
    # This function makes a feature structure using a list of lhs which are nested
    # e.g. if lhs = ['a','b','c','d'] and rhs = 'wzq' then the
    # fs shoule be [a = [b = [c = [d = 'wzq']]]]
    """
    :param lhs: The path on the left hand side
    :type lhs: list(str)
    :param rhs: The string on the right hand side / Any object
    :type rhs: str / object
    :param ref: Control whether to treat rhs as a string or as an abitrary object
    :type ref: 0 / 1
    :return: A constructed feature structure
    :rtype: FeatStruct
    
    Given the path and the right hand side of a feature structure this function
    will return a feature structure exactly has the path defined in lhs and the
    value inside it is the rhs. There are two choices, we can either pass in a
    string as the rhs to let the code to deal with the 'or' problem. or just
    pass in an object and the code will not touch that (ref = 1 needed).
    
    lhs = ['a','b','c','d']
    rhs = 'wzq'
    ->FeatStruct = [a = [b = [c = [d = [__or_wzq = 'wzq']]]]]
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
            pass # Do nothing
        else:
            raise ValueError('Undefined ref value %d' % (ref))
        
        new_fs[lhs[0]] = rhs
    else:
        new_fs[lhs[0]] = make_fs(lhs[1:],rhs,ref) # Recursively call
        
    return new_fs

def add_new_fs(fs,lhs,rhs,ref=0):
    """
    :param fs: The feature structure that we are going to add to it.
    :type fs: FeatStruct
    :param lhs: The path defined for the new node
    :type lhs: list(str)
    :param rhs: The value of the node
    :type rhs: str / Any object
    :param ref: Controls whether rhs should be treated as a string or other object
    :type ref: 0 / 1

    This function will add the feature structure defined by lhs and rhs
    into an existing feature fs. The lhs of the lowest level is defined
    to be '__or_' + rhs to facilitate other procedures.

    If any of the paths defined by lhs has already existed in fs, then
    it will be merged into that existing path, instead of erasing the existing
    one and make a new one, so it is safe to use this function to merge two
    feature structures.

    For example,
    
    fs = [a = ['www']]
    lhs = ['a','b','c','d','e']
    rhs = 'wzq'
    ->
    [a = [['www']                                ]
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
    return

def merge_fs(fs1,fs2):
    # This function merges fs2 into fs1, changing fs1 in-place
    # It's a cheaper and faster alternative of unify(), which will check
    # all the similarities and differences between fs1 and fs2. But this one
    # just assumes that fs2 and fs1 does not have any entries in common
    # NOTICE: In Templates.lex we cannot guarantee there is no overlap
    # so only use this function when it IS clear.
    """
    Please do not use this one, call add_new_fs() instead
    """
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
    :param s: The string repersenting start feature in the catalog file
    :type s: str
    :return: A feature structure which is the start feature
    :rtype: FeatStruct

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
    # Only single entry modification is applicable. If you want to change a
    # reference instead of a value please use modify_feature_reference()
    """
    :param feature: The feature structure you want to modify
    :type feature: FeatStruct
    :param path: The path of the node being modified
    :type path: list(str)
    :param rhs: The new srring that will substitued a old one (no '/' contained)
    :type rhs: str

    :return: A new feature structure with the entry modified
    :rtype: FeatStruct

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
        current_fs.pop(make_leaf_str(lhs))
    current_fs[make_leaf_str(rhs)] = rhs
    
    return returned_fs

def get_all_path(fs):
    """
    :param fs: The feature structure you want to working on
    :type fs: FeatStruct
    :return: A list of all paths
    :rtype: list(list(str))

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
    :param fs: The feature structure you want to work on
    :type fs: FeatStruct
    :param path: The path of the node
    :type path: list(str)

    :return: If the path is valid then the node will be returned; Or else a
    None will be returned
    :rtype: FeatStruct / None

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

##############################
# Fix Unify Result ###########
##############################

def restore_reference(new_feat,old_feat_1,old_feat_2):
    """
    Restore the reference relationship after doing unification to a feature structure.

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
    :param fs1: One of the feature structure acting as the target
    :type fs1: FeatStruct
    :param fs2: Another feature structure acting as the source
    :type fs2: FeatStruct

    This function will try to find common entries between the two feature
    structures, and if one of them is of empty value, then we will rewrite
    it using the value in another feature structure. Only those whose path
    is the same and one of them is empty while one of them while another is
    not, will be rewritten.

    If both entries are empty, although it is very weird, we will let it pass
    since this is not a fatal error. And if both are not empty, but their values
    are different, then it is natural that unification will return None, so we
    also won't raise exceptions.

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

def search_correction(corr_list,item):
    """
    Used in special_unify(), please do not call this.
    
    :param corr_list: A list of tuples repersenting the old value and new value
    used in the correction.
    :type corr_list: list(tuple(FeatStruct,FeatStruct,FeatStruct))
    :param item: The leaf node to be checked against the list
    :type item: FeatStruct

    This function checks the id of the item (using built-in function id()) and
    see whether the id already exists in the corr_list, both tuple[0] or tuple[1]
    which are the two values before unification. And if there is a match, just
    return tuple[2], which is the new value after unification.
    """
    for i in corr_list:
        item_id = id(item)
        if item_id == id(i[1]) or item_id == id(i[2]):
            return i[0]
        return None

def correct_other_nodes(corr_list,tree):
    """
    :param corr_list: correction list in special_unify()
    :type corr_list: list(tuple(FeatStruct,FeatStruct,FeatStruct))
    :param tree: The tree on which you want to restore value reference
    :type tree: TAGTree
    
    The goal of this function is to do some correction work after unification,
    when there is shared values between nodes, the unification function cannot
    tell which node refers to a certain value, and will make new values on some
    condition. So in order to restore this kind of reference we must do a
    correction after the unification.

    During unification the method special_unify() will make a record of these
    new nodes, together with the old values, in order to do a matching with
    the nodes on the feature structures of other nodes. This record is exactly
    corr_list.
    """
    fs = tree.get_all_fs()
    fs_list = fs.values()
    for i in fs_list: # Enumerate all feature structures
        path = get_all_path(i)
        for j in path: # j is all paths in the feature
            corr_check = search_correction(corr_list,j)
            if corr_check != None:
                # If we find some entry whose value exists in the correction list
                # then just change the value of that entry to the new entry
                # we've just created in the new feature structure.
                modify_feature_reference(i,j,corr_check)
    return

def special_unify(fs1,fs2,tree1=None,tree2=None):
    """
    :param fs1: One of the feature structures you want to unify
    :type fs1: FeatStruct
    :param fs2: Another feature structure
    :type fs2: FeatStruct
    :param tree1: The tree that you want to restore inter-node reference
    :type tree1: TAGTree
    :param tree2: Another tree, optional.
    :type tree2: TAGTree

    This function will do a unify just like what the normal unify() does, but
    in addition to a normal unification we also have the following features:

    1. Disjunction is considered, e.g. [x = a/b/c] and [x = b/c/d] should yield
    [x = b/c]; [x = a/b/c] and [x = a/b] should yield [x = a/b]
    2. The result is a new feature structure, but the leaf node is not new;
    actually we will make reference to the leaf nodes in fs1 and fs2
    3. When the path and the value are both the same, we will make new nodes,
    and then fix the references in the trees given by parameters tree1 and tree2
    to make the entry point to the new node.
    """
    new_fs = FeatStruct()
    correction_list = []
    path_2 = get_all_path(fs2) # To save time, no path_1
    for i in path_2:
        item_1 = get_element_by_path(fs1,i)
        if item_1 == None:
            item_2 = get_element_by_path(fs2,i)
            add_new_fs(new_fs,i,item_2,1) # ref == 1, we only do reference!!
        else:
            item_2 = get_element_by_path(fs2,i)
            tc = test_contain(item_1,item_2) # Single entry is the same as multiple entry
            if tc == 1: # t1 is a subset of t2, we always use the smaller one
                add_new_fs(new_fs,i,item_1,1)
            elif tc == -1:
                add_new_fs(new_fs,i,item_2,1)
            elif tc == 0: # Two entries are the same, we create a new one
                corr_check = search_correction(correction_list,item_1)
                if corr_check == None:
                    new_entry = copy.deepcopy(item_1)
                    # This tuple is used to correct the reference in tree(s)
                    # Enumerating all paths, check whether the id of the value is
                    # equal to either item1 or item2, if it is then change the
                    # reference to new_entry
                    correction_tuple = (new_entry,item_1,item_2)
                    correction_list.append(correction_tuple)
                else:
                    # The return value is the new entry stored if three is not None
                    new_entry = corr_check
                # Add new reference (new entry or existing entry)
                add_new_fs(new_fs,i,new_entry,1)
            elif tc == None:
                return None # Conflict
            # Partial intersection, return value is a new FeatStruct only contains
            # the intersection. But we do not need to correct this, since it
            # is brand-new
            else: 
                add_new_fs(new_fs,i,tc,1)
            #if i[0] == 'comp': print tc

    # We do not need to check when item_2 != None, because we have already
    # done it in the first loop. In other words, we have processed the overlapping
    # paths, and what is left is to add those in fs1 but not in fs2 into the
    # new feature structure
    path_1 = get_all_path(fs1)
    for i in path_1:
        item_2 = get_element_by_path(fs2,i)
        if item_2 == None:
            item_1 = get_element_by_path(fs1,i)
            add_new_fs(new_fs,i,item_1,1)

    if tree1 != None:
        correct_other_nodes(correction_list,tree1)
    if tree2 != None:
        correct_other_nodes(correction_list,tree2)
    
    return new_fs

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
debug_start_feature = parse_feature_in_catalog('<mode> = ind/imp <comp> = nil <wh> = <invlink>  <punct term> = per/qmark/excl <punct struct> = nil')
empty_feature = FeatStruct()
empty_feature['__or_'] = ''

def debug_special_unify():
    print debug_start_feature
    fs100 = copy.deepcopy(debug_start_feature)
    fs100.pop('wh')
    fs100.pop('mode')
    fs100['wzq'] = fs2
    #fs100['comp'].pop('__or_nil')
    fs100['comp']['__or_sdsdsd'] = 'sdsdsd'
    print '=========================='
    print special_unify(fs100,debug_start_feature)

def debug_test_contain():
    fs100 = FeatStruct()
    fs100['__or_wzq'] = 'wzq'
    #fs100['__or_qwe'] = 'qwe'
    fs101 = FeatStruct()
    fs101['__or_123'] = '123'
    fs101['__or_wzq'] = 'wzq'
    print test_contain(fs100,fs101)
    

if __name__ == '__main__':
    debug_special_unify()
    #debug_test_contain()
                    
