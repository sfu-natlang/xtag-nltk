# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

from nltk.parse.nonprojectivedependencyparser import *
import pickle
from copy import deepcopy

#help(ProbabilisticNonprojectiveParser)

def print_lable_dist(lable_dist,fp):
    d = lable_dist.freqdist()
    for i in d.keys():
        fp.write(i + ' ' + str(d[i]) + '\n')
    fp.write('?????\n')
    return

def print_feature_dist(feature_dist,fp):
    for i in feature_dist.keys():
        # For debugging
        if len(i) != 2:
            raise ValueError('Invalid tuple in feature_dist')
        
        fp.write(i[0] + ' ' + i[1] + ' ' + str(feature_dist[i]._bins) + '\n')
        d = feature_dist[i].freqdist()
        for j in d.keys():
            fp.write(str(j) + ' ' + str(d[j]) + '\n')
        fp.write(';;;;;\n')
    return
        

def print_train_data(lable_dist,feature_dist,filename="TAGParseData.dat"):
    fp = open(filename, 'w')
    print_lable_dist(lable_dist,fp)
    print_feature_dist(feature_dist,fp)
    fp.close()

def dump_to_disk(filename,obj):
    """
    Dump an object into the disk using pickle
    :param filename: The name of the dumping file
    :type filename: str
    :param obj: Any object you want to dump
    :type obj: Any object
    """
    fp = open(filename,'wb')
    pickle.dump(obj,fp)
    fp.close()

def restore_from_disk(filename):
    """
    Restore the dumped file using pickle to an obejct
    :param filename: The file you want to read from
    :type filename: str
    :return: The restored object
    :rtype: Any object
    """
    fp = open(filename,'rb')
    obj = pickle.load(fp)
    fp.close()
    return obj

####################################
# Tree operation ###################
####################################

def get_name_prefix(name):
    """
    Return the name prefix, if there is no prefix then just return itself.

    e.g. S_r --> S; NP_1 --> NP; VP --> VP

    :type name: str
    :param name: The name of a node
    """
    index = name.find('_')
    if index != -1:
        name = name[:index]
    return name

def check_name_equality(name_1,name_2):
    """
    Check whether the two nodes' name are the same. Notice that the name of
    a node may contain a '_XXX' suffix, so we need to get rid of this.

    :type name_1: str
    :param name_1: The name of first node

    :type name_2: str
    :param name_2: The name of the second node
    """
    name_1 = get_name_no_prefix(name_1)
    name_2 = get_name_no_prefix(name_2)
    if name_1 == name_2:
        return True
    else:
        return False

def check_substitution(tree_1,tree_2,anchor_pos):
    """
    Check whether one tree can be combined with another tree using substitution.
    And tree_2 must be under tree_1 in the substitution.
    Any possible combination will be contained in the list returned. Also we need
    to provide a parameter called anchor_pos, which is a boolean.

    :type tree_1: TagTree
    :param tree_1: The first tree

    :type tree_1: TagTree
    :param tree_1: The second tree

    :type anchor_pos: bool
    :param anchor_pos: False if the the anchor of tree_1 is at the left side of
     the anchor of tree_2, and True if the anchor of tree_1 is at the right of
     the anchor of tree_2.

    :return: All possible combinations, also TagTree
    :rtype: list
    
    If we are not sure which tree is under which tree, then we need to call this
    function twice, e.g. if tree_1 must be at the left of tree_2

    check_substitution(tree_1,tree_2,False)
    check_substitution(tree_2,tree_1,True)

    The False and True is to make sure that the anchor of tree_1 must be at the
    left side of the anchor of tree_2.
    """
    result = []

    sn = tree_1.get_substitution_node()
    for i in sn:
        root_tree_2 = tree_2.get_node_name()

        # If anchor_pos == True then the anchor of tree_2 must be at the left
        # side of tree_1.
        if tree_1.at_anchor_left(i) == anchor_pos:
            if check_name_equality(i.get_node_name(),root_tree_2) == True:
                new_tree_1 = deepcopy(tree_1)
                new_tree_2 = deepcopy(tree_2)
                new_sub_node = new_tree_1.search(i.get_node_name())
                # When doing substitution we need to unify the top features, and check whether it is null
                new_top_feature = new_sub_node.get_top_feature().unify(new_tree_2.get_top_feature())
                # Cannot unify
                if new_top_feature == None:
                    print "unify_failed" # For debugging
                    continue
                new_sub_node.set_top_feature(new_top_feature)
                # Bottom feature is just a copy
                new_sub_node.set_bottom_feature(new_tree_2.get_bottom_feature())
                # Append all child nodes of tree_2 to the substitution node
                for j in tree_2.get_child_node():
                    new_sub_node.append_new_child(j)
                # This node cannot be designeted as a substitution node, so we need to cancel that
                new_sub_node.cancel_substitution()
                result.append(new_tree_1)
                
    return result

def check_adjunction(tree_1,tree_2):
    """
    To check adjunction using tree_2 to tree_1, i.e. tree_2 is the auxiliary tree
    
    :type tree_1: TagTree
    :param tree_1: The first tree

    :type tree_2: TagTree
    :param tree_2: The second tree

    :return: A list containing all possible combinations using adjunction
    :rtype: list
    """
    result = []
    # this will return only a node
    foot_2 = tree_2.get_foot_node() 
    # The method returns None if not found (not an auxiliary tree)
    if foot_2 == None:  
        return []
    # Get the string name
    foot_name = foot_2.get_node_name()
    # root_name_no_prefix = get_name_no_prefix(tree_2.get_node_name())
    # is actually the same, but we will not rely on that
    # Strip prefix
    foot_name_prefix = get_name_prefix(foot_2.get_node_name())
    # Using prefix to search for a list of nodes
    names = foot_1.prefix_search(foot_name_prefix)
    # Check each possible node that is 
    for i in names:
        # Make copies, including feature structures in each tree
        new_tree_1 = deepcopy(tree_1)
        new_tree_2 = deepcopy(tree_2)
        # Locate the foot node, since it is a different instance
        new_foot = new_tree_2.search(foot_name)
        # Locate the node being adjoint, the reason is the same
        adj_node = new_tree_1.search(i.get_node_name())
        # It is a list
        new_node_child = adj_node.get_child_node()
        # Append all child node to the foot node
        for j in new_node_child:
            new_foot.append_new_child(j)
        # Delete all nodes on the node being adjoint
        adj_node.delete_all_child()
        # Then attach tree_2 in the whole to the adj_node
        for j in new_tree_2.get_child_node():
            adj_node.append_new_child(j)

        # Next we will change the feature structure
        # The detail is recorded in the technical report
        t = adj_node.get_top_feature()
        b = adj_node.get_bottom_feature()
        tr = new_tree_2.get_top_feature()
        br = new_tree_2.get_bottom_feature()
        tf = new_foot.get_top_feature()
        bf = new_foot.get_bottom_feature()
        adj_node.set_top_feature(t.unify(tr))
        adj_node.set_bottom_feature(br)
        new_foot.set_bottom_feature(b.unify(bf))
        # Don't forget to let the foot node become a normal node
        new_foot.cancel_adjunction()
        # Add this new tree into the list
        result.append(new_tree_1)
        
    return result

def check_word_order(t,word_list):
    """
    Given a TagTree and a list of words, make sure that the leaves in the tree
    which are words are in the same order as those in word_list.

    word_list need not to be a full list describing all lex in the tree, but
    it must not contain un-existing word. As all words in word_list has the same
    order as it is in word_list, this function will return True. Or else a False
    will be returned.

    :param t: TagTree to be checked
    :type t: TagTree

    :param word_list: A list of words (exact word, not the lex)
    :type word_list: list(str)

    :return: True if the order is the same and False if different
    :rtype: boolean`
    """
    # Get the list of all leaf words from the tree
    tree_word_list = t.get_word_list()
    tree_word_list_2 = []
    # Check if all words in word_list exist in the tree, if not raise an error
    for i in word_list:
        if not i in tree_word_list:
            raise ValueError('No word %s found in the tree' % (i))
    # Remove those word not in word_list. After this step the two list
    # should be of the same length, only the order is different
    for i in tree_word_list:
        if i in word_list:
           tree_word_list_2.append(i)
    # For debug: if the length is different then out theory is wrong
    if len(tree_word_list_2) != len(word_list):
        raise ValueError('Something strange happened here (for debug)')
    # Check the order by comparing all indexes, if one comparision fails
    # then the test will fail
    for i in range(0,len(word_list)):
        if word_list[i] != tree_word_list_2[i]:
            return False
    # Passed all test, succeed
    return True

def enforce_word_order(tree_list,word_list):
    """
    Just a wrapper of check_word_order, iteratively checking the order for a list
    of trees, and remove those not qualified.

    :param tree_list: The list of trees
    :type tree_list: list(TagTree)

    :param word_list: A list of words (exact word, not the lex)
    :type word_list: list(str)

    :return: A reduced list with non-qualified trees removed
    :rtype: list(TagTree)
    """
    ret = []
    for i in tree_list:
        if check_word_order(i,word_list) == True:
            ret.append(i)
    return ret
        
        
def tree_compatible(tree_1,tree_2,word_list=None,operation='AS'):
    """
    To combine two trees together using substitution or adjunction.

    :param tree_1: The first tree
    :type tree_1: TagTree

    :param tree_2: The second tree
    :type tree_2: TagTree

    :param word_list: A list of words to enforce word order in the resulting trees
    :type word_list: list(str)

    :return: The result of sunstitution and adjunction
    :rtype: tuple(list,list,list,list)

    The first two parameters, tree_1 and tree_2, have an order constraint, i.e.
    in the result of substitution, the words in tree_1 must be before the words
    in tree_2. But in the result of adjunction, no such constraint exist. Optionally
    we can choose to pass another parameter called word_list, to enforce the
    correct order in the result of adjunction. The word_list is a list of words
    the order of which must be followed in the resulting tree. The default value
    is None, which means do not check this, but usually we need a check and need
    not to code another checking procedure.

    Besides there is another option parameter called operation. This parameter
    is used to control the behaviour of the function. Essentially it is a string
    including controlling charaters. 'A' stands for Adjunction, 'S' stands for
    substitution. 'AS' or 'SA' will do both, and 'A' will only do adjunction while
    'S' will only do substitution. Other characters have no effect except that
    in the later version of this function we may add more functionalities and make
    extensions to the control characters.

    The return value is a tuple which has four components, and they are the result
    of substitution tree_1 <- tree_2, substitution tree_2 <- tree_1, adjunction
    tree_1 <- tree_2 and adjunction tree_2 <- tree_1. For substitution
    tree_x <- tree_y means the root of tree_y is combined with the leaf of tree_x
    and for adjunction it menas the foot node in on tree_y.

    Also take care that there is not a valid way to prohibit order enforcing in
    substitution. I did this with no reason.

    For more details about substitution and adjunction please refer to the
    technical report of the XTAG project.

    http://www.cis.upenn.edu/~xtag/gramrelease.html
    """
    # Convert to upper case
    operation = operation.upper()
    # These two is to make sure the word in tree_1 must be at the left
    # of tree_2, whild trying all possible combinations
    # To control if we need to do substitution
    if 'A' in operation:
        sub_1 = check_substitution(tree_1,tree_2,False)
        sub_2 = check_substitution(tree_2,tree_1,True)
    else:
        sub_1 = []
        sub_2 = []
    # Adjunction does not guarantee the order so we have an additional step
    # To control if we need to do adjunction
    if 'S' in operation:
        adj_1 = check_adjunction(tree_1,tree_2)
        adj_2 = check_adjunction(tree_2,tree_1)
    else:
        adj_1 = []
        adj_2 = []

    # To control if we need an order enforcement
    if word_list != None:
        enforce_word_order(adj_1,word_list)
        enforce_word_order(adj_2,word_list)
        
    # We return them separately to enable more flexable process later
    return (sub_1,sub_2,adj_1,adj_2)

####################################
# Debugging information ############
####################################

def debug_print_train_data():
    print_train_data(None,None)

def debug_dump_and_restore():
    d = {'a': 1,'b': 2,'c':3,None:4}
    e = ['ed','ser','56','wertwert']
    f = {3:d,5:e,7:'dffdfdf'}
    dump_to_disk('dict.dat',f)
    rd = restore_from_disk('dict.dat')
    print rd

def debug_check_name_equality():
    print check_name_equality('S_r',"Ss")
    
if __name__ == '__main__':
    debug_check_name_equality()
