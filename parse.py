# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

from nltk.parse.projectivedependencyparser import *
from nltk.classify.naivebayes import *
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from util import *
import time
import pickle
from copy import deepcopy
import nltk.data

####################################
# Tree Compatibility ###############
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
    name_1 = get_name_prefix(name_1)
    name_2 = get_name_prefix(name_2)
    if name_1 == name_2:
        return True
    else:
        return False


def check_substitution(tree_1,tree_2,anchor_pos,feature_enabled=False):
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
        #if tree_1.at_anchor_left(i) == anchor_pos:
        if True:
            if check_name_equality(i.get_node_name(),root_tree_2) == True:
                new_tree_1 = deepcopy(tree_1)
                new_tree_2 = deepcopy(tree_2)
                new_sub_node = new_tree_1.search(i.get_node_name())

                if feature_enabled == True:
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

def check_adjunction(tree_1,tree_2,feature_enabled=False):
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
    # root_name_no_prefix = get_name_prefix(tree_2.get_node_name())
    # is actually the same, but we will not rely on that
    # Strip prefix
    foot_name_prefix = get_name_prefix(foot_2.get_node_name())
    # Using prefix to search for a list of nodes
    names = tree_1.prefix_search(foot_name_prefix)
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
            
        if feature_enabled == True:
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
        
        
def tree_compatible(tree_1,tree_2,word_list=None,feature_enabled=False,operation='AS'):
    """
    To combine two trees together using substitution or adjunction.

    :param tree_1: The first tree
    :type tree_1: TagTree

    :param tree_2: The second tree
    :type tree_2: TagTree

    :param word_list: A list of words to enforce word order in the resulting trees
    :type word_list: list(str)

    :param feature_enabled: Whether to include feature structure during the combination of trees
    :type feature_enabled: bool
    
    :return: The result of substitution and adjunction
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

    Also take care that there is not a valid way to prohibit order enforcement in
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
        sub_1 = check_substitution(tree_1,tree_2,False,feature_enabled)
        sub_2 = check_substitution(tree_2,tree_1,True,feature_enabled)
    else:
        sub_1 = []
        sub_2 = []
    # Adjunction does not guarantee the order so we have an additional step
    # To control if we need to do adjunction
    if 'S' in operation:
        adj_1 = check_adjunction(tree_1,tree_2,feature_enabled)
        adj_2 = check_adjunction(tree_2,tree_1,feature_enabled)
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



######################################
# Parse Viewer #######################
######################################
class DependencyGraphView(TAGTreeSetView):
    def __init__(self, tagset):

        TAGTreeSetView.__init__(self, tagset)

        self._cframe = CanvasFrame(self._top, closeenough=1, width=4)
        self._widgets = []
        self._merge = TreeMerge([], self)
        self._import_trees = {}
        self._import_trees_selected = False
        self._tset = self._merge.tree()
        self._ps = None
        self._os = None
        self.w['text'] = '    Input Sentence:    '
        self.remove_button['text'] = '  Parse  '
        self.remove_button['command'] = self.parse
        self.keep_button['text'] = 'Import Tree'
        self.highlight_button['text'] = 'Export Tree'
        self.highlight_button['command'] = self.exportparsefile
        self._show_fs_button['text'] = 'Select'
        self.node_trees = {}
        self.node_treename = {}
        self.node_parsed = {}
        self.tree_widget = {}
        self._show_fs_button['command'] = self.select_tree
        self.file_opt = {}
        self.keep_button['command'] = self.openparsefile
        self._sfs_button['text'] = "Show Result"
        self._sfs_button['command'] = self.pop_selector
        self.notfl['text'] = ''
        self.nottl['text'] = ''
        self.tfcl.pack_forget()
        self.tcl.pack_forget()
        self.alltrees = tagset
        self.elements = []
        self.graphs = None
        self.tagmap = {}
        self.relmap = {}
        self.redraw(self._tset)
        self.clear()

    def display(self, event=None):
        if self._import_trees_selected:
            node = self._tagview.focus()
            path = self._tagview.set(node, "fullpath").split('/')
            self.init_selector(self._import_trees[path[1]])
        else:
            node = self._tagview.focus()
            path = self._tagview.set(node, "fullpath").split('/')
            tree = self._trees
            for subpath in path[1:]:
                if subpath in tree:
                    if not isinstance(tree, type(self._trees)):
                        if tree._lex:
                            tree[subpath] = tree[subpath].copy(True)

                    tree = tree[subpath]
                else:
                    raise TypeError("%s: tree does not match"
                                 % type(self).__name__)

            if not isinstance(tree, type(self._trees)):
                if tree._lex:
                    tree.lexicalize()
                    tree._lex = False
                    self._tw.redraw(self._show_fs, tree)
                else:
                    self._tw.redraw(self._show_fs, tree)

    def compatible_tree_select(self, tree):
        self.node_parsed[id(self.node_selected)] = tree[0]

    def select_tree(self):
        if self.node_trees[id(self.node_selected)] == None:
            t, name = self.focus()
            if t == None:
                return
            self.node_trees[id(self.node_selected)] = t
            self.node_treename[id(self.node_selected)] = name
            self._show_fs_button['text'] = 'Cancel'
            self.tree_selected = False
            for tree in self._tset:
                self.level_trav(tree)
            if len(self.node_selected) == 0:
                self.node_parsed[id(self.node_selected)] = t
                return
            for subtree in self.node_selected:
                if id(subtree) in self.node_parsed and not self.node_parsed[id(subtree)] == None:
                    if id(self.node_selected) in self.node_parsed:
                        t = self.node_parsed[id(self.node_selected)]
                    comp_trees = tree_compatible(t, self.node_parsed[id(subtree)])
                    tagset = TAGTreeSet()
                    count = 0
                    for ct_list in comp_trees:
                        for ct in ct_list:
                            tagset['tree '+str(count)] = ct
                            count += 1
                    selector = TAGTreeSelector(tagset, self.compatible_tree_select)
                    selector._top.wait_window(self._top)                     
        else:
            self._show_fs_button['text'] = 'Select'
            self.tree_selected = True
            self.node_trees[id(self.node_selected)] = None
            self.node_treename[id(self.node_selected)] = None

    def pop_selector(self):
        if not id(self.node_selected) in self.node_parsed:
            return
        t = self.node_parsed[id(self.node_selected)]
        tagset = TAGTreeSet()
        tagset['parse result'] = t
        selector = TAGTreeSelector(tagset, self.compatible_tree_select)
        selector._top.wait_window(self._top)  
    
    def draw_parsed_tree(self):
        self._import_trees_selected = False
        if self.node_selected == None:
            return
        if self.node_trees[id(self.node_selected)]:
            self._show_fs_button['text'] = 'Cancel'
            tree = self.node_trees[id(self.node_selected)]
            self._tw.redraw(self._show_fs, tree)
        else:
            self._show_fs_button['text'] = 'Select'

    def clear(self):
        x = self._tagview.get_children()
        for item in x: 
            self._tagview.delete(item)
        self._trees = TAGTreeSet()
        self._tw.clear()

    def openparsefile(self):
        self.clear()
        self.filename = tkFileDialog.askopenfilename(**self.file_opt)
        if not self.filename:
            return
        data = open(self.filename, 'r').read()
        self.initree = {}
        filtdata = ""
        self.ininame = {}
        for entry in data.split('\n\n'):
            if not entry:
                continue
            for line in entry.split("\n"):
                elements = line.split()
                if len(elements) < 4:
                    continue
                if len(elements) == 5:
                    lex_list = word_to_features(elements[0])
                    fset = lex_search(lex_list, {}, self.alltrees)
                    for cata in fset:
                        if elements[4] in fset[cata]:
                            tree = fset[cata][elements[4]]
                            tree.lexicalize()
                            tree._lex = False
                            self.initree[elements[0]] = tree
                            self.ininame[elements[0]] = elements[4]
                self.relmap[elements[0]] = elements[1]
                self.tagmap[elements[0]] = elements[3]
                filtdata += "\t".join(elements[:4])
                filtdata += '\n'
            filtdata += "\n\n"
        self.graphs = [DependencyGraph(entry)
              for entry in filtdata.split('\n\n')[:-1] if entry]
        trees = [graph.tree() for graph in self.graphs]
        count = 0
        for t in trees:
            key = 'tree '+ str(count)
            self._import_trees[key] = t
            count += 1
        self.populate_tree('', self._import_trees)
        self._import_trees_selected = True
        self.init_selector(trees[0])

    def init_selector(self, t):
        self._merge = TreeMerge([t], self)
        self._tset = self._merge.tree()
        stack = [tree for tree in self._tset]
        while len(stack) > 0:
            e = stack.pop()
            self.node_trees[id(e)] = None
            try:
                label = e.node
            except NotImplementedError:
                label = e._label
            if label in self.initree:
                self.node_trees[id(e)] = self.initree[label]
                self.node_treename[id(e)] = self.ininame[label]
                
            if len(e) > 0:
                stack += [tree for tree in e]
        self.redraw(self._tset)
        self.level_trav(self._tset[0])

    def level_trav(self, tree):
        trav = {}
        level = 0
        stack = [tree]
        trav[level] = stack
        while len(stack) > 0:
            temp = []
            for t in stack:
                temp += [subtree for subtree in t]
            level += 1
            trav[level] = temp
            stack = temp
        dec_level = level - 1
        filled_node = []
        while dec_level >= 0:
            subtree = trav[dec_level]
            dec_level -= 1
            for t in subtree:
                if not self.node_trees[id(t)] == None:
                    if len(t) == 0:
                        self.node_parsed[id(t)] = self.node_trees[id(t)]
                    else:                          
                        for child in t:
                            if id(t) in self.node_parsed and self.node_parsed[id(t)] != None:
                                continue
                            if id(child) in self.node_parsed and not self.node_parsed[id(child)] == None:
                                comp_trees = tree_compatible(self.node_trees[id(t)], self.node_parsed[id(child)])
                                tagset = TAGTreeSet()
                                count = 0
                                for ct_list in comp_trees:
                                    for ct in ct_list:
                                        tagset['tree '+str(count)] = ct
                                        count += 1
                                self.node_selected = t
                                selector = TAGTreeSelector(tagset, self.compatible_tree_select)
                                selector._top.wait_window(self._top)



    def exportparsefile(self):
        filename = tkFileDialog.asksaveasfilename(**self.file_opt)

        if filename:
            fp = open(filename, 'w')

        for tree in self._tset:
            count = 0
            stack = [(tree, count)]
            while len(stack) > 0:
                e, n = stack.pop()
                count += 1
                if len(e) > 0:
                    stack += [(t, count) for t in e]
                tagtree = ""
                if id(e) in self.node_treename:
                    tagtree = self.node_treename[id(e)]
                try:
                    label = e.node
                except NotImplementedError:
                    label = e._label
                if label in self.relmap and label in self.tagmap:
                    fp.write("\t".join([label, self.relmap[label], str(n), 
                                    self.tagmap[label], tagtree, '\n']))
                else:
                    fp.write("\t".join([label, "None", str(n), 
                                    "None", tagtree, '\n']))
            fp.write("\n")

    def parse(self):
        self.clear()
        words = word_tokenize(self._e.get())
        trees = [Tree(word, []) for word in words]
        self._merge = TreeMerge(trees, self)
        self._tset = self._merge.tree()
        self.redraw(self._tset)
        self.node_trees = {}
        for tree in self._tset:
            self.node_trees[id(tree)] = None

    def compatible(self, word):
        self.clear()
        lex_list = word_to_features(word)
        fset = lex_search(lex_list, {}, self.alltrees)
        self.update(fset)
        return fset

    def redraw(self, tree):
        """
        Update the current canvas to display another tree, set te feature
        sturctures to display or hidden.

        :param show: a boolean value for whether to show the feature
        sturcture on the canvas
        :param trees: a list of tree segments
        """
        for i in self._widgets:
            self._cframe.destroy_widget(i)
        self._size = IntVar(self._top)
        self._size.set(12)
        bold = ('helvetica', -self._size.get(), 'bold')
        helv = ('helvetica', -self._size.get())

        self._width = 0
        for i in tree:
            self._width += int(ceil(sqrt(len(i))))
        self._widgets = []
        for i in range(len(tree)):
            widget = GraphWidget(self._cframe.canvas(), tree[i], self._merge,
                             self._top, self, self.boxit)
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)

    def _layout(self):
        i = x = y = ymax = 0
        width = self._width
        for i in range(len(self._widgets)):
            widget = self._widgets[i]
            (oldx, oldy) = widget.bbox()[:2]
            if width == 0:
                width = 10
            if i % width == 0:
                y = ymax
                x = 0
            widget.move(x-oldx, y-oldy)
            x = widget.bbox()[2] + 10
            ymax = max(ymax, widget.bbox()[3] + 10)

    def boxit(self, canvas, text):
        big = ('helvetica', -16, 'bold')
        return GraphElementWidget(canvas, self, TextWidget(canvas, text,
                                            font=big), text, fill='green')

    def select(self, element):
        if self._ps == None:
            self._ps = element
            self._os = self._ps
            return
        if self._ps == element or self._ps._select == 2:
            return
        self._ps.reset()
        self._os = self._ps
        self._ps = element

    def rollback(self, element):
        if self._os == None:
            return
        self._os = None
        self._ps = None

def demo(lang):
    t = load(lang)
    viewer = DependencyGraphView(t)
    viewer.mainloop()

class TreeMerge(object):
    def __init__(self, tree_set, parent):
        self.trees = []
        for t in tree_set:
            self.trees.append(self.str_to_tree(t))
        self.merge = None
        self.current = None
        self._parent = parent

    def str_to_tree(self, tree):
        if isinstance(tree, basestring):
            return Tree(tree, [])
        stack = [tree]
        while len(stack) > 0:
            t = stack.pop()
            for child in t:
                if isinstance(child, basestring):
                    index = t.index(child)
                    t.pop(index)
                    t.insert(index, Tree(child,[]))
                else:
                    stack.append(child)
        return tree

    def connect(self, tree):
        if self.merge == None:
            self.merge = tree
        else:
            top = self.merge.parent()
            otop = tree.parent()
            if not isinstance(top.parent(), type(top)):
                head = top
                parent = tree
            elif not isinstance(otop.parent(), type(otop)):
                head = tree
                parent = top
            else:
                self.merge.reset()
                self.merge = tree
                return

            if self.root(self.merge) != self.root(tree):
                pid = id(parent._tree)
                hid = id(head._tree)
                parent._tree.append(head._tree)
                if head._tree in self.trees:
                    self.trees.remove(head._tree)
                self.merge.reset()
                self.merge = None
                self._parent._tw.clear()
                self._parent.redraw(self._parent._tset)
            else:
                self.merge.reset()
                self.merge = tree

    def root(self, tree):
        child = tree.parent()
        while isinstance(child.parent(), type(child)):
            child = child.parent()
        return child

    def tree(self):
        return self.trees

class GraphSegmentWidget(TreeSegmentWidget):
    def __init__(self, canvas, node, subtrees, tree, parent, merge, **attribs):
        TreeSegmentWidget.__init__(self, canvas, node, 
                                      subtrees, **attribs)
        self._merge = merge
        self._canvas = canvas
        self._select = False
        self._press = 0
        self._tree = tree
        self._anc = parent
        self.__press = None
        self.__drag_x = self.__drag_y = 0
        self.__callbacks = {}
        self.__draggable = 0

    def box_size(self):
        return self.node().bbox()

class GraphElementWidget(BoxWidget):
    def __init__(self, canvas, parent, child, text, **attribs):
        self.box = BoxWidget.__init__(self, canvas, child, **attribs)
        self._text = text
        self._select = 0
        self._press = 0
        self._subtrees = []
        self._lines = []
        self._node = self.box
        self._tree = None
        self.bind_click(self.click)
        self._canvas = canvas
        self.viewer = parent
        if not self in self.viewer.elements:
            self.viewer.elements.append(self)

    def color(self):
        self['fill'] = 'yellow'

    def click(self, node):
        if self._select == 1:
            parent = self
            parent._merge.connect(parent)
            self._select = 2
            self['fill'] = 'red'
            self.viewer.node_selected = None
        elif self._select == 2:
            node['fill'] = 'green'
            self._select = 0
            self._merge.merge = None
            self.viewer.node_selected = None
        else:
            node['fill'] = 'yellow'
            if self._merge.current != None:
                self._merge.current.reset()
            self._merge.current = self
            self._select = 1
            self.viewer.compatible(self._text)
            self.viewer.node_selected = self.parent()._tree
            self.viewer.draw_parsed_tree()
        self.viewer._cframe.pack(expand=1, fill='both', side = LEFT)


    def set_merge(self, tree):
        self._merge = tree

    def set_tree(self, tree):
        self._tree = tree

    def set_leaf(self, tree):
        if isinstance(tree, basestring):
            self._tree = Tree(tree, [])
        else:
            self._tree = tree

    def reset(self):
        self._select = 0
        self['fill'] = 'green'

    def select(self):
        self._select = 1
        self['fill'] = 'yellow'

class GraphWidget(TreeWidget):
    def __init__(self, canvas, t, merge, top, parent, make_node=TextWidget, **attribs):

        self._l = []
        self._merge = merge        
        self._parent = parent
        self.tree_set = merge.tree()
        self.tw = TreeWidget.__init__(self, canvas, t, make_node,
                            make_node, **attribs)
        self._top = top
        self._xy_map = {}
        self._make_xy_map()

        self._canvas = canvas
        self._select = False
        self._press = 0
        for leaf in self._l:
            leaf.set_merge(self._merge)

        for tseg in self._expanded_trees.values():
            tseg.node().set_merge(self._merge)

        self.__press = None
        self.__drag_x = self.__drag_y = 0
        self.__callbacks = {}
        self.__draggable = 1
        self['draggable'] = 1

        self.init_tags()

    def _init_menubar(self):
        pass

    def init_tags(self):
        self._ltconnect = defaultdict(list)
        self._line_tags = defaultdict(list)
        self._tree_tseg = defaultdict(list)
        self._element_tags = {}

        for tseg in self._expanded_trees.values():
            self._ltconnect[tseg] += tseg._subtrees
            self._line_tags[tseg] += tseg._tags()

        for i in self._line_tags:
            for tag in self._line_tags[i]:
                self._canvas.tag_bind(tag, '<ButtonPress-1>',
                                       lambda event, line=tag:self.__press_cb(event, line))

        for i in self._element_tags:
            for tag in  self._element_tags[i]:
                self._canvas.tag_bind(tag, '<ButtonPress-1>',
                                       lambda event, line=tag:self.__press_cb(event, line))

    def __press_cb(self, event, tag):
        """
        Handle a button-press event:
          - record the button press event in ``self.__press``
          - register a button-release callback.
          - if this CanvasWidget or any of its ancestors are
            draggable, then register the appropriate motion callback.
        """
        # If we're already waiting for a button release, then ignore
        # this new button press.
        if (self._canvas.bind('<ButtonRelease-1>') or
            self._canvas.bind('<ButtonRelease-2>') or
            self._canvas.bind('<ButtonRelease-3>')):
            return

        # Unbind motion (just in case; this shouldn't be necessary)
        self._canvas.unbind('<Motion>')

        # Record the button press event.
        self.__press = event

        # If any ancestor is draggable, set up a motion callback.
        # (Only if they pressed button number 1)
        if event.num == 1:
            widget = self
            while widget is not None:
                if widget['draggable']:
                    widget._start_drag(event)
                    break
                widget = widget.parent()

        #self.__callbacks[1] = self._double_click
        # Set up the button release callback.
        self._canvas.bind('<ButtonRelease-%d>' % event.num,
                          lambda event, line=tag:self.__release_cb(event, line))

    def _start_drag(self, event):
        """
        Begin dragging this object:
          - register a motion callback
          - record the drag coordinates
        """
        self._canvas.bind('<Motion>', self.__motion_cb)
        self.__drag_x = event.x
        self.__drag_y = event.y
        x = self.canvas().canvasx(event.x)
        y = self.canvas().canvasy(event.y)

    def __motion_cb(self, event):
        """
        Handle a motion event:
          - move this object to the new location
          - record the new drag coordinates
        """
        self.move(event.x-self.__drag_x, event.y-self.__drag_y)
        self.__drag_x = event.x
        self.__drag_y = event.y

    def __release_cb(self, event, tag):
        """
        Handle a release callback:
          - unregister motion & button release callbacks.
          - decide whether they clicked, dragged, or cancelled
          - call the appropriate handler.
        """
        # Unbind the button release & motion callbacks.
        self._canvas.unbind('<ButtonRelease-%d>' % event.num)
        self._canvas.unbind('<Motion>')

        # Is it a click or a drag?
        if (event.time - self.__press.time < 100 and
            abs(event.x-self.__press.x) + abs(event.y-self.__press.y) < 5):
            # Move it back, if we were dragging.
            if self.__draggable and event.num == 1:
                self.move(self.__press.x - self.__drag_x,
                          self.__press.y - self.__drag_y)
            self.__double_click(self, tag)
        elif event.num == 1:
            self.__drag()

        self.__press = None

    def __drag(self):
        """
        If this ``CanvasWidget`` has a drag callback, then call it;
        otherwise, find the closest ancestor with a drag callback, and
        call it.  If no ancestors have a drag callback, do nothing.
        """
        if self.__draggable:
            if 'drag' in self.__callbacks:
                cb = self.__callbacks['drag']
                try:
                    cb(self)
                except:
                    print 'Error in drag callback for %r' % self

    def __double_click(self, treeseg, tag):
        current = time.time()
        if current - self._press < 0.5:
            for i in self._line_tags:
                for j in range(0, len(self._line_tags[i])):
                    if tag == self._line_tags[i][j]:
                        parent = i
                        child = self._ltconnect[i].pop(j)
                        for k in range(0, len(parent._tree)):
                            if isinstance(parent._tree[k], basestring):
                                if len(child._tree) == 0 and parent._tree[k] == child._tree.node:
                                    pid = id(parent._tree)
                                    cw = child
                                    pw = parent
                                    parent._tree.pop(k)
                                    break
                            elif parent._tree[k] == child._tree:
                                pid = id(parent._tree)
                                cw = child
                                pw = parent
                                parent._tree.pop(k)
                                break
                        if isinstance(child._tree, basestring):
                            child._tree = Tree(child._tree, [])

                        self.tree_set.append(child._tree)
                        self._parent._merge.merge = None
                        self._parent._merge.current = None
                        self._parent.redraw(self._parent._tset)
                        self._parent._tw.clear()
                        child['draggable'] = 1
        self._press = current

    def _make_xy_map(self):
        for tseg in self._expanded_trees.values():
            self._xy_map[tseg] = self.canvas().coords(tseg.node()._tags()[0])
        for leaf in self._l:
            self._xy_map[leaf] = leaf.bbox()

    def _make_expanded_tree(self, canvas, t, key):
        make_node = self._make_node
        make_leaf = self._make_leaf

        if isinstance(t, Tree):
            node = make_node(canvas, t.node, **self._nodeattribs)
            node.set_tree(t)
            self._nodes.append(node)
            children = t
            subtrees = [self._make_expanded_tree(canvas, children[i], key+(i,))
                        for i in range(len(children))]
            treeseg = GraphSegmentWidget(canvas, node, subtrees, t, self._parent, self._merge, 
                                        color=self._line_color,
                                        width=self._line_width)
            self._expanded_trees[key] = treeseg
            self._keys[treeseg] = key
            return treeseg
        else:
            leaf = make_leaf(canvas, t, **self._leafattribs)
            leaf.set_leaf(t)
            self._leaves.append(leaf)
            self._l.append(leaf)
            return leaf

    def _make_collapsed_trees(self, canvas, t, key):
        if not isinstance(t, Tree): return
        make_node = self._make_node
        make_leaf = self._make_leaf

        node = make_node(canvas, t.node, **self._nodeattribs)
        node.set_tree(t)
        self._nodes.append(node)
        leaves = [make_leaf(canvas, l, **self._leafattribs)
                  for l in t.leaves()]
        for i in range(0, len(leaves)):
            leaves[i].set_leaf(t.leaves()[i])
        self._leaves += leaves
        treeseg = GraphSegmentWidget(canvas, node, leaves, t, self._parent, self._merge, 
                                    roof=1, color=self._roof_color,
                                    fill=self._roof_fill,
                                    width=self._line_width)

        self._collapsed_trees[key] = treeseg
        self._keys[treeseg] = key
        treeseg.hide()

        for i in range(len(t)):
            child = t[i]
            self._make_collapsed_trees(canvas, child, key + (i,))    

class TAGTreeSelector(TAGTreeSetView):
    """
    A window that displays a selector of parse result. The
    result contains a group of TAG trees, when clicking the
    tree name on the tree list, the tree will be displayed on
    the canvas.

    """
    def __init__(self, tagtree, callback):
        TAGTreeSetView.__init__(self, tagtree)
        self._show_fs = False
        self._show_fs_button['text'] = 'Show Feature'
        self._sfs_button['text'] = 'Select Tree'
        self._sfs_button['command'] = self.tag_tree_select
        self.call = callback
        if len(tagtree.keys()) == 1:
            tree = tagtree[tagtree.keys()[0]]
            self._tw.redraw(self._show_fs, tree, hide_comment=True)

    def display(self, event=None):
        """
        Display the tag tree on the canvas when the tree
        is selected.
        """
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                if not isinstance(tree, type(self._trees)):
                    if tree._lex:
                        tree[subpath] = tree[subpath].copy(True)

                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)

        if not isinstance(tree, type(self._trees)):
            self._sfs_button['text'] = 'Select'
            if tree._lex:
                tree.lexicalize()
                tree._lex = False
                self._tw.redraw(self._show_fs, tree, hide_comment=True)
            else:
                self._tw.redraw(self._show_fs, tree, hide_comment=True)

    def tag_tree_select(self):
        """
        Return the selection to the call function
        """
        t = self.focus()
        if t:
            self.call(t)
            self._top.destroy()

if __name__ == '__main__':
    #debug_check_name_equality()
    #test()
    #dump()
    demo('english')
    #projective_parse('Hells Angels was formed in 1948 and incorporated in 1966.')
