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

def get_name_no_prefix(name):
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
    foot_2 = tree_2.get_foot_node()
    if foot_2 == None:
        return []
    foot_name = foot_2.get_node_name()
    foot_name_no_prefix = get_name_no_prefix(foot_2.get_node_name())
    names = foot_1.prefix_search(foot_name_no_prefix)
    for i in names:
        new_tree_1 = deepcopy(tree_1)
        new_tree_2 = deepcopy(tree_2)
        new_foot = new_tree_2.search(foot_name)
        new_node = new_tree_1.search(i.get_node_name())
        new_node_child = new_node.get_child_node()
        for j in new_node_child:
            new_tree_2.search(foot_name).append_new_child(j)
        new_node.delete_all_child()
        for j in new_tree_2.get_child_node():
            new_node.append_new_child(j)
        t = new_node.get_top_feature()
        b = new_node.get_bottom_feature()
        tr = new_tree_2.get_top_feature()
        br = new_tree_2.get_bottom_feature()
        tf = new_foot.get_top_feature()
        bf = new_foot.get_bottom_feature()
        new_node.set_top_feature(t.unify(tr))
        new_node.set_bottom_feature(br)
        new_foot.set_bottom_feature(b.unify(bf))
        result.append(new_tree_1)
    return result
    

def tree_compatible(tree_1,tree_2):
    pass

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
