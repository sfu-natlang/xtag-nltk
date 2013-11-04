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

#help(ProbabilisticNonprojectiveParser)
"""
class XTAGScorer(NaiveBayesDependencyScorer):

    A dependency scorer built around a MaxEnt classifier.  In this
    particular class that classifier is a ``NaiveBayesClassifier``.
    It uses head-word, head-tag, child-word, and child-tag features
    for classification.


    def __init__(self, label_freqdist, feature_probdist):
        self.label_freqdist = label_freqdist
        self.feature_probdist = feature_probdist

    def train(self, graphs):
        self.classifier = NaiveBayesClassifier(self.label_freqdist, self.feature_probdist)
"""
class TAGTreeSelector(TAGTreeSetView):
    def __init__(self, tagtree, callback):
        TAGTreeSetView.__init__(self, tagtree)
        self._sfs_button['text'] = 'Select Tree'
        self._sfs_button['command'] = self.tag_tree_select
        self.call = callback

    def tag_tree_select(self):
        t = self.focus()
        if t:
            self.call(t)
            self._top.destroy()

class DependencyGraphView(TAGTreeSetView):
    def __init__(self, tagset):

        TAGTreeSetView.__init__(self, tagset)
        """
        self._top = Tk()
        self._top.title('NLTK')
        self._top.bind('<Control-p>', lambda e: self.print_to_file())
        self._top.bind('<Control-x>', self.destroy)
        self._top.bind('<Control-q>', self.destroy)
        #"""
        self._cframe = CanvasFrame(self._top, closeenough=1, width=4)
        self._widgets = []
        self._merge = TreeMerge([], self)
        #self._merge = TreeMerge([trees], self)
        self._tset = self._merge.tree()
        self._ps = None
        self._os = None
        self.w['text'] = '    Input Sentence:    '
        self.remove_button['text'] = '  Parse  '
        self.remove_button['command'] = self.parse
        self.keep_button['text'] = 'Import Tree'
        self.highlight_button['text'] = 'Export Tree'
        self.highlight_button['command'] = self.exportparsefile
        #self.tree_selected = {}
        self._show_fs_button['text'] = 'Select'
        self.node_trees = {}
        self.node_treename = {}
        self.node_parsed = {}
        self.tree_widget = {}
        self._show_fs_button['command'] = self.select_tree
        self.file_opt = {}
        self.keep_button['command'] = self.openparsefile
        self._sfs_button.pack_forget()
        self.notfl['text'] = ''
        self.nottl['text'] = ''
        self.tfcl.pack_forget()
        self.tcl.pack_forget()
        self.alltrees = tagset
        self.elements = []
        self.redraw()
        self.clear()
        #self.parser = parser

    def compatible_tree_select(self, tree):
        self.node_parsed[id(self.node_selected)] = tree[0]
        print tree


    def select_tree(self):
        if self.node_trees[id(self.node_selected)] == None:
            t, name = self.focus()
            if t == None:
                return
            self.node_trees[id(self.node_selected)] = t
            self.node_treename[id(self.node_selected)] = name
            self._show_fs_button['text'] = 'Cancel'
            self.tree_selected = False
            if len(self.node_selected) == 0:
                self.node_parsed[id(self.node_selected)] = t
                return
            for subtree in self.node_selected:
                if id(subtree) in self.node_parsed and not self.node_parsed[id(subtree)] == None:
                    if id(self.node_selected) in self.node_parsed:
                        t = self.node_parsed[id(self.node_selected)]
                    comp_trees = tree_compatible(t, self.node_parsed[id(subtree)])
                    print comp_trees
                    tagset = TAGTreeSet()
                    count = 0
                    for ct_list in comp_trees:
                        for ct in ct_list:
                            tagset['tree'+str(count)] = ct
                            count += 1
                    selector = TAGTreeSelector(tagset, self.compatible_tree_select)
                    selector._top.wait_window(self._top)
                            #i[0].draw()
                    #self.update(tagset)
                             
        else:
            self._show_fs_button['text'] = 'Select'
            self.tree_selected = True
            self.node_trees[id(self.node_selected)] = None
            self.node_treename[id(self.node_selected)] = None
    
    def draw_parsed_tree(self):
        if self.node_selected == None:
            return
        if self.node_trees[id(self.node_selected)]:
            self._show_fs_button['text'] = 'Cancel'
            tree = self.node_trees[id(self.node_selected)]
            self._tw.redraw(self._show_fs, tree)
        else:
            self._show_fs_button['text'] = 'Select'


    def openparsefile(self):
        self.filename = tkFileDialog.askopenfilename(**self.file_opt)
        data = open(self.filename, 'r').read()
        graphs = [DependencyGraph(entry)
              for entry in data.split('\n\n') if entry]
        self._merge = TreeMerge([graph.tree() for graph in graphs], self)
        self._tset = self._merge.tree()
        stack = [tree for tree in self._tset]
        while len(stack) > 0:
            e = stack.pop()
            self.node_trees[id(e)] = None
            if len(e) > 0:
                stack += [tree for tree in e]
        self.redraw()

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
                fp.write(e.node + " " + str(n) + '\n')
            fp.write("\n")

    def parse(self):
        self.clear()
        words = word_tokenize(self._e.get())
        trees = [Tree(word, []) for word in words]
        self._merge = TreeMerge(trees, self)
        self._tset = self._merge.tree()
        self.redraw()
        self.node_trees = {}
        for tree in self._tset:
            self.node_trees[id(tree)] = None
        #graph = self.parser.parse(words)
        #print graph

    def compatible(self, word):
        self.clear()
        lex_list = word_to_features(word)
        fset = search(lex_list, {}, self.alltrees)
        self.update(fset)
    """
    def redraw(self, pid=None, hid=None):
        #cf = CanvasFrame(width=550, height=450, closeenough=2)
        #GraphWidget(self._cframe.canvas(), self._tset[0], self._merge,
        #                     self._top, self, self.boxit)
        #self._cframe.pack(expand=1, fill='both', side = LEFT)
        #print self._merge.trees

        self._size = IntVar(self._top)
        self._size.set(12)
        bold = ('helvetica', -self._size.get(), 'bold')
        helv = ('helvetica', -self._size.get())

        pw = None
        hw = None
        self._width = 0
        for i in self._tset:
            self._width += int(ceil(sqrt(len(i))))

        for i in self._widgets:
            if i in self.tree_widget.values():
                #self._cframe.remove_widget(i)
                continue
            else:
                self._cframe.destroy_widget(i)

        if isinstance(pid, int):
            pw = self.tree_widget[pid]
            del self.tree_widget[pid]
        if isinstance(hid, int):
            hw = self.tree_widget[hid]
            del self.tree_widget[hid]
        for i in range(len(self._tset)):

            if not id(self._tset[i]) in self.tree_widget:
                if pw and hw:
                    self._cframe.remove_widget(pw)
                    self._cframe.remove_widget(hw)

                    parent = pw._treeseg
                    child = hw._treeseg
                    child.parent()._remove_child_widget(child)
                    #print child.parent(), 231
                    parent._subtrees.insert(-1, child)
                    parent._add_child_widget(child)
                    parent._lines.append(parent.canvas().create_line(0,0,0,0, fill='#006060'))
                    parent.update(parent._node)                   
                    widget = pw
                    widget.init_tags()
                elif pid:
                    if pid._tree == self._tset[i]:
                        widget = pid.parent()
                    elif hid._tree == self._tset[i]:
                        widget = GraphWidget(self._cframe.canvas(), self._tset[i], self._merge,
                                     self._top, self, self.boxit)
                        self.node_trees[widget._treeseg._node] = self.node_trees[hid._node]
                        del self.node_trees[hid._node]
                else:
                    print pid, 200, self._tset[i]
                    widget = GraphWidget(self._cframe.canvas(), self._tset[i], self._merge,
                                     self._top, self, self.boxit)
            else:
                print pid, 300, self._tset[i]
                widget = self.tree_widget[id(self._tset[i])]
                print widget._treeseg
                self._cframe.remove_widget(widget)
            print widget, self._tset[i], 12415425
            self.tree_widget[id(self._tset[i])] = widget
        print self.tree_widget

        self._widgets = []
        for widget in self.tree_widget.values():
            print widget#, widget._treeseg, 1
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        for e in self.elements:
            if not e in self.node_trees:
                self.node_trees[e] = None

        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)
        #self._init_menubar()
        """

    def redraw(self):
        """
        Update the current canvas to display another tree, set te feature
        sturctures to display or hidden.

        :param show: a boolean value for whether to show the feature
        sturcture on the canvas
        :param trees: a list of tree segments
        """
        #cf = CanvasFrame(width=550, height=450, closeenough=2)
        #GraphWidget(self._cframe.canvas(), self._tset[0], self._merge,
        # self._top, self, self.boxit)
        #self._cframe.pack(expand=1, fill='both', side = LEFT)
        #print self._merge.trees
        for i in self._widgets:
            self._cframe.destroy_widget(i)
        self._size = IntVar(self._top)
        self._size.set(12)
        bold = ('helvetica', -self._size.get(), 'bold')
        helv = ('helvetica', -self._size.get())

        self._width = 0
        for i in self._tset:
            self._width += int(ceil(sqrt(len(i))))
        self._widgets = []
        for i in range(len(self._tset)):
        # print trees[i]
            #if isinstance(trees[i], TAGTree):
            # fs = trees[i].get_all_fs()
            #else:
            # fs = None
            widget = GraphWidget(self._cframe.canvas(), self._tset[i], self._merge,
                             self._top, self, self.boxit)
            #widget.set_parent_window(self._top)
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)
        #self._init_menubar()

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
        #self._ps.select()

def demo():
    t = load()
    #grammar = restore()
    #ppdp = XTAGParser()
    #ppdp._grammar = grammar
    
    viewer = DependencyGraphView(t)
    viewer.mainloop()
    #a = t[t.keys()[0]]
    #b = t[t.keys()[1]]
    #aa = a[a.keys()[0]]
    #bb = b[b.keys()[0]]
    #aaa = aa[aa.keys()[0]]
    #bbb = bb[bb.keys()[1]]

    #aaa= t['family-files']['TEnx1V.trees']['\x02DEnx1V']
    #bbb= t['tree-files']['determiners.trees']['\x03dD']
    #print aaa.draw()
    #print bbb.draw()
    #print tree_compatible(aaa, bbb)
    #ttt = tree_compatible(aaa, bbb)[0][0]
    #ttt.correct_name().draw()
    #ttt.check_name([ttt.node],0)
    #ttt.draw()
    #tree_compatible(aaa, bbb)[2][0].draw()


def projective_parse(sent):
    words = word_tokenize(sent)
    #tag_tuples = pos_tag(words)
    #tags = [tag for word, tag in tag_tuples]
    
    #print time.time()
    grammar = restore()
    #print time.time()
    
    """
    string = ''
    import os
    directory = os.path.join('/Users/zhanghaotian/Downloads','penn-wsj-deps')
    for root,dirs,files in os.walk(directory):
        for d in dirs:
            if d != '00' and d!= '01' and d!='22' and d!='23' and d!='24':
                direct = os.path.join(directory, d)
                for root,dirs,files in os.walk(direct):
                    for f in files:
                        f = os.path.join(direct,f)
                        fp = open(f, 'r').readlines()
                        for a in fp:
                            string += a

    print len(string)
    graphs = [DependencyGraph(entry)
              for entry in string.split('\n\n') if entry]
    ppdp = XTAGParser()
    ppdp.train(graphs)
    """
    ppdp = XTAGParser()
    ppdp._grammar = grammar
    print words
    parse_graph = ppdp.parse(words)
    print parse_graph[0]


def dump():
    string = ''
    import os
    directory = os.path.join('/Users/zhanghaotian/Downloads','penn-wsj-deps')
    for root,dirs,files in os.walk(directory):
        for d in dirs:
            if d != '00' and d!= '01' and d!='22' and d!='23' and d!='24':
                direct = os.path.join(directory, d)
                for root,dirs,files in os.walk(direct):
                    for f in files:
                        f = os.path.join(direct,f)
                        fp = open(f, 'r').readlines()
                        for a in fp:
                            string += a
    print len(string)
    graphs = [DependencyGraph(entry)
              for entry in string.split('\n\n') if entry]
    ppdp = ProbabilisticProjectiveDependencyParser()
    ppdp.train(graphs)
    dump_to_disk('ppdp_grammar.pickles', ppdp._grammar)
    print 'finish.'
    #label_freqdist = npp._scorer.classifier._label_probdist
    #feature_probdist = npp._scorer.classifier._feature_probdist
    #print_train_data(label_freqdist, feature_probdist, 'data.txt')
    #dump_to_disk('lfd', label_freqdist)
    #dump_to_disk('fpd', feature_probdist)

def restore():
    grammar_file = nltk.data.find('xtag_grammar/pickles/ppdp_grammar.pickles').open()
    #fpd = nltk.data.find('xtag_grammar/pickles/fpd').open()
    grammar = restore_from_disk(grammar_file)
    #feature_probdist = restore_from_disk(fpd)
    return grammar


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
    
if __name__ == '__main__':
    #debug_check_name_equality()
    #test()
    #dump()
    demo()
    #projective_parse('Hells Angels was formed in 1948 and incorporated in 1966.')
