# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#
import ttk
import os
import re
import copy

from nltk.tree import *
from nltk.featstruct import FeatStruct
from Tkinter import *
from nltk.util import in_idle
from nltk.tree import Tree
from math import sqrt, ceil
from load import *
from nltk.draw.tree import (TreeView, TreeWidget, TreeSegmentWidget)
from nltk.sem.logic import (Variable, Expression)
from nltk.draw.util import *
from nltk.tokenize import word_tokenize
from collections import defaultdict
import time
import nltk.data
import pickle

def dump_to_disk(filename,obj):
    """
    Dump an object into the disk using pickle
    :param filename: The name of the dumping file
    :type filename: str
    :param obj: Any object you want to dump
    :type obj: Any object
    """
    fp = open(filename,'wb')
    pickle.dump(obj,fp, -1)
    fp.close()

def restore_from_disk(fp):
    """
    Restore the dumped file using pickle to an obejct
    :param filename: The file you want to read from
    :type filename: str
    :return: The restored object
    :rtype: Any object
    """
    #fp = open(filename,'rb')
    obj = pickle.load(fp)
    #fp.close()
    return obj

def install():
    try:
        nltk.data.find('xtag_grammar/pickles/tagtreeset.pickle')
    except LookupError:
        for path_item in nltk.data.path:

        # Is the path item a zipfile?
            p = os.path.join(path_item, *'xtag_grammar'.split('/'))
        #p = os.path.join(path_item, ['xtag_grammar'])
            if os.path.exists(p):
                t = init_tree()
                pic_dir = os.path.join(p, 'pickles')
                if not os.path.exists(pic_dir):
                    os.makedirs(pic_dir)
                tree_dir = os.path.join(pic_dir, 'tagtreeset.pickle')
                dump_to_disk(tree_dir, t)
                return

def init_tree():
    cata_str = nltk.data.find('xtag_grammar/english.gram').open().read()
    cata = get_catalog(cata_str)
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    return t
    
def load():
    cata_str = nltk.data.find('xtag_grammar/english.gram').open().read()
    
    cata = get_catalog(cata_str)
    #start = time.time()
    """
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    dump_to_disk('tagtreeset.pickle', t)
    """

    treefile = nltk.data.find('xtag_grammar/pickles/tagtreeset.pickle').open()
    treeset = restore_from_disk(treefile)
    #print time.time()-start
    morph = get_file_list(cata, 'morphology-files')
    syn = get_file_list(cata, 'lexicon-files')
    temp = get_file_list(cata, 'templates-files')
    default = get_file_list(cata, 'syntax-default')

    morph_path = 'xtag_grammar' + os.sep + morph[1] + os.sep + morph[0][0]
    syn_path = 'xtag_grammar' + os.sep + syn[1] + os.sep + syn[0][0]
    temp_path = 'xtag_grammar' + os.sep + temp[1] + os.sep + temp[0][0]
    default_path = 'xtag_grammar' + os.sep + default[1] + os.sep + default[0][0]
    
    morph_str = nltk.data.find(morph_path).open().read()
    syn_str = nltk.data.find(syn_path).open().read()
    temp_str = nltk.data.find(temp_path).open().read()
    default_str = nltk.data.find(default_path).open().read()


    init(morph_str, syn_str, temp_str, default_str)
    return treeset

#    treetok = Tree.parse('(A (walk C D) (E (F G) (H I)))')
#    treetok = graph_parse(treetok)
#    graph = DependencyGraphView(treetok, t)
#    graph.mainloop()  

def debug():
    cata = get_catalog('../xtag-english-grammar/english.gram')
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    morph = get_file_list(cata, 'morphology-files')
    syn = get_file_list(cata, 'lexicon-files')
    temp = get_file_list(cata, 'templates-files')
    default = get_file_list(cata, 'syntax-default')
    #print morph[0]
    morph_path = morph[1]+morph[0][0]
    #print morph[1]
    syn_path = syn[1]+syn[0][0]
    temp_path = temp[1]+temp[0][0]
    default_path = default[1]+default[0][0]
    init(morph_path, syn_path, temp_path, default_path)
    treetok = Tree.parse('(A (walk C D) (E (F G) (H I)))')
    treetok = graph_parse(treetok)
    graph = DependencyGraphView(treetok, t)
    graph.mainloop()    

def graph_parse(graph):
    if isinstance(graph, basestring):
        node_name = graph
        return Tree(node_name, [])
    else:
        node_name = graph.node
        subtree = []
        for i in range(0, len(graph)):
            subtree.append(graph_parse(graph[i]))
        return Tree(node_name, subtree)


def _tree_to_graphseg(canvas, t, make_node, make_leaf,
                     tree_attribs, node_attribs,
                     leaf_attribs, loc_attribs):
    if isinstance(t, Tree):
        node = make_node(canvas, t.node, **node_attribs)
        subtrees = [_tree_to_graphseg(canvas, child, make_node, make_leaf,
                                     tree_attribs, node_attribs,
                                     leaf_attribs, loc_attribs)
                    for child in t]
        return GraphSegmentWidget(canvas, node, subtrees, **tree_attribs)
    else:
        return make_leaf(canvas, t, **leaf_attribs)

def tree_to_graphsegment(canvas, t, make_node=TextWidget,
                        make_leaf=TextWidget, **attribs):
    tree_attribs = {}
    node_attribs = {}
    leaf_attribs = {}
    loc_attribs = {}

    for (key, value) in attribs.items():
        if key[:5] == 'tree_': tree_attribs[key[5:]] = value
        elif key[:5] == 'node_': node_attribs[key[5:]] = value
        elif key[:5] == 'leaf_': leaf_attribs[key[5:]] = value
        elif key[:4] == 'loc_': loc_attribs[key[4:]] = value
        else: raise ValueError('Bad attribute: %s' % key)
    return _tree_to_graphseg(canvas, t, make_node, make_leaf,
                                tree_attribs, node_attribs,
                                leaf_attribs, loc_attribs)

class TreeMerge(object):
    def __init__(self, tree_set, parent):
        self.trees = tree_set
        self.merge = None
        self._parent = parent

    def connect(self, tree):
        print self.trees
        if self.merge == None:
            self.merge = tree
        else:
            top = self.merge.parent()
            otop = tree.parent()
            if not isinstance(top.parent(), type(top)):
                head = top
                parent = tree
                print 1
            elif not isinstance(otop.parent(), type(otop)):
                head = tree
                parent = top
                print 2
            else:
                self.merge.reset()
                #tree.reset()
                self.merge = tree
                print 3
                return

            if self.root(self.merge) != self.root(tree):
                if isinstance(parent._tree, basestring):
                    parent._tree = Tree(parent._tree, head._tree)
                    print 4
                else:
                    print parent._tree
                    parent._tree.append(head._tree)
                    print parent._tree
                    print 5
                if head._tree in self.trees:
                    print 6
                    print head._tree, self.trees
                    self.trees.remove(head._tree)
                self.merge = None
                self._parent.redraw()
            else:
                print 7
                self.merge.reset()
                #tree.reset()
                self.merge = tree
            print self.trees

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
        #self.bind_click(self._double_click, 1)
        #self.bind_drag(self.click)
        self._merge = merge
        self._canvas = canvas
        self._select = False
        self._press = 0
        self._tree = tree
        self._anc = parent
        #self.__hidden = 0

        # Update control (prevents infinite loops)
        #self.__updating = 0

        # Button-press and drag callback handling.
        self.__press = None
        self.__drag_x = self.__drag_y = 0
        self.__callbacks = {}
        self.__draggable = 0
        for tag in self._tags():
            self._canvas.tag_bind(tag, '<ButtonPress-1>',
                                   lambda event, line=tag:self.__press_cb(event, line))
            #self._canvas.tag_bind(tag, '<ButtonPress-2>',
            #                       self.__press_cb)
            #self._canvas.tag_bind(tag, '<ButtonPress-3>',
            #                       self.__press_cb)
    
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
        elif self.__parent is not None:
            self.__parent.__drag()


    #def __double_click(self, treeseg, tag):
    #    current = time.time()
    #    if current - self._press < 0.5:
    #        ind = self._lines.index(tag)
    #        child = self._subtrees[ind]
    #        self.remove_child(child)
    #        child['draggable'] = 1

    #        child.__draggable = 1
    #    self._press = current


    def box_size(self):
        return self.node().bbox()

class GraphElementWidget(BoxWidget):
    def __init__(self, canvas, child, text, **attribs):
        self.box = BoxWidget.__init__(self, canvas, child, **attribs)
        #self.bind_click(self._double_click, 1)
        #self.bind_drag(self.click)
        self._text = text
        self._select = 0
        self._press = 0
        self._subtrees = []
        self._lines = []
        self._node = self.box
        self._tree = None
        self.bind_click(self.click)
        self._canvas = canvas
        #self._canvas.tag_bind(self._tags(), '<Double-Button-1>', self.double_click)

    def color(self):
        self['fill'] = 'yellow'

    #def double_click(self):
    #    parent = self
    #    parent._merge.connect(parent)
    #    self['fill'] = 'red'

    def click(self, node):
        #current = time.time()
        if self._select == 1:
            #if self.parent() == None:
            #    parent = self
            #else:
            #    parent = self.parent()
            parent = self
            parent._merge.connect(parent)
            self._select = 2
            #self.parent()._anc.rollback(self)
            self['fill'] = 'red'
        elif self._select == 2:
            node['fill'] = 'green'
            self._select = 0
        else:
            node['fill'] = 'yellow'
            self._select = 1
            #self.parent()._anc.select(self)
            #lex_list = word_to_features(self._text)
            
        #self._press = current

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
        self._ltconnect = defaultdict(list)
        self._line_tags = defaultdict(list)
        self._element_tags = {}

        for tseg in self._expanded_trees.values():
            self._ltconnect[tseg] += tseg._subtrees
            self._line_tags[tseg] += tseg._tags()
        
        """
        for tseg in self._expanded_trees.values():
            self._element_tags[tseg] = tseg.node().child()._tags()
        for leaf in self._l:
            self._element_tags[leaf] = leaf.child()._tags()
        """

        for i in self._line_tags:
            for tag in self._line_tags[i]:
                self._canvas.tag_bind(tag, '<ButtonPress-1>',
                                       lambda event, line=tag:self.__press_cb(event, line))

        for i in self._element_tags:
            for tag in  self._element_tags[i]:
                self._canvas.tag_bind(tag, '<ButtonPress-1>',
                                       lambda event, line=tag:self.__press_cb(event, line))

            #self._canvas.tag_bind(tag, '<ButtonPress-2>',
            #                       self.__press_cb)
            #self._canvas.tag_bind(tag, '<ButtonPress-3>',
            #                       self.__press_cb)
    """
    def merge(self, tree):
        if len(merge) > 0:
            oldtree = merge.pop()
            parent = oldtree
            child = tree
            parent._add_child_widget(child)
            parent._lines.append(self.canvas().create_line(0,0,0,0, fill='#006060'))
            parent.update(parent._node)
            parent.insert_child(0, child)
        else:
            merge.append(tree)
    """

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
        #for tseg in self._xy_map:
        #    if x > self._xy_map[tseg][0] and x < self._xy_map[tseg][2]:
        #        if y > self._xy_map[tseg][1] and x < self._xy_map[tseg][3]:
        #            print tseg
        #print x, y
        #print event.x, event.y
        #for i in self._xy_map:
        #    print i, self._xy_map[i]

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
        #elif self.__parent is not None:
        #    self.__parent.__drag()

    def __double_click(self, treeseg, tag):
        #import random
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
                                    parent._tree.pop(k)
                                    break
                            elif parent._tree[k] == child._tree:
                                parent._tree.pop(k)
                                break
                        if isinstance(child._tree, basestring):
                            child._tree = Tree(child._tree, [])
                        self.tree_set.append(child._tree)
                        self._parent.redraw()
                        #parent.remove_child(child)
                        child['draggable'] = 1
                        #child.__parent = parent.parent()
        self._press = current

    """
    def _tags(self):
        tags = []
        for tseg in self._expanded_trees.values():
            tags += tseg._tags()
            tags += tseg.node()._tags()
            tags += tseg.node().child()._tags()
        for leaf in self._l:
            tags += leaf._tags()
            tags += leaf.child()._tags()
        return tags
    """
    def _make_xy_map(self):
        #for tseg in self._expanded_trees.values():
        #    self._xy_map[tseg] = tseg.box_size()
        #for leaf in self._l:
        #    self._xy_map[leaf] = leaf.bbox()
        for tseg in self._expanded_trees.values():
            self._xy_map[tseg] = self.canvas().coords(tseg.node()._tags()[0])
            #print self._xy_map[tseg]
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
        #self._add_child_widget(treeseg)
        treeseg.hide()

        # Build trees for children.
        for i in range(len(t)):
            child = t[i]
            self._make_collapsed_trees(canvas, child, key + (i,))

class TAGTreeSegmentWidget(TreeSegmentWidget):
    """
    A canvas widget that displays a single segment of a hierarchical
    TAG tree, inherit from ``TreeSegmentWidget``, Each ``TAGTreeSegmentWidget``
    contains an extra top feature strucuture and a bottom feature structure
    than the ``TreeSegmentWidget``.
    """
    def __init__(self, canvas, node, subtrees, top_fs, bot_fs, **attribs):
        """
        :type top_fs:
        :type bot_fs: FeatStruct
        """
        TreeSegmentWidget.__init__(self, canvas, node, 
                                      subtrees, **attribs)
        self._top_fs = top_fs
        self._bot_fs = bot_fs

    def top_fs(self):
        return self._top_fs

    def bot_fs(self):
        return self._bot_fs        

class TAGTreeWidget(TreeWidget):
    """
    A canvas widget that displays a single TAG Tree, inherit from 
    ``TreeWidget``. ``TAGTreeWidget`` manages a group of ``TAGTreeSegmentWidgets``
    that are used to display a TAG Tree. The each TAG Tree node
    contains a top feature structure and a bottom feature structure.
    The feature structures can be set to display or hidden on the canvas.

    Attributes:

      - ``keep``: Display the feature structures which match the
        input regular expression.
        node widgets for this ``TreeWidget``.
      - ``remove``: Remove the feature structures which match the
        input regular expression from the canvas.
      - ``highlight``: Highlight the feature structures which match 
        the input regular expression.
      - ``reg``: The input regular expression for keep, remove or
        highlight.

    """
    def __init__(self, canvas, t, fs, show, parent, make_node=TextWidget,
                 make_leaf=TextWidget, **attribs):
        self._all_fs = fs
        self._show_fs = show
        self._attr = {}
        # Attributes.
        for (i, j) in attribs.items():
            if i in ['keep', 'remove', 'highlight', 'reg']:
                self._attr[i] = j
                del attribs[i]
        TreeWidget.__init__(self, canvas, t, make_node,
                            make_leaf, **attribs)   
        self._top = parent

    def _make_expanded_tree(self, canvas, t, key):        
        make_node = self._make_node
        make_leaf = self._make_leaf

        if isinstance(t, TAGTree):
            node_name = self._set_node_name(t)
            bold = ('helvetica', -24, 'bold')
            node = make_node(canvas, node_name, font=bold,
                                color='#004080')

            if self._show_fs:
                top_fs = fs_widget(t.top_fs, self._all_fs, canvas, 
                                   _fs_name(node_name, True), **self._attr)
                bot_fs = fs_widget(t.bot_fs, self._all_fs, canvas,
                                   _fs_name(node_name, False), **self._attr)
                cstack = StackWidget(canvas, top_fs, bot_fs, align='left')
                node =  SequenceWidget(canvas, node, cstack, align='top')

            self._nodes.append(node)
            children = t
            subtrees = [self._make_expanded_tree(canvas, children[i], key+(i,))
                        for i in range(len(children))]
            top_name = _fs_name(t.node, True)
            bot_name = _fs_name(t.node, False)
            top_fs = FeatStruct()
            bot_fs = FeatStruct()
            if top_name in self._all_fs:
                top_fs = self._all_fs[top_name]
            if bot_name in self._all_fs:
                bot_fs = self._all_fs[bot_name]
            treeseg = TAGTreeSegmentWidget(canvas, node, subtrees, 
                                        top_fs, bot_fs,
                                        color=self._line_color,
                                        width=self._line_width)
            self._expanded_trees[key] = treeseg
            self._keys[treeseg] = key

            return treeseg
        else:
            leaf = make_leaf(canvas, t, **self._leafattribs)
            self._leaves.append(leaf)
            return leaf

    def _set_node_name(self, t):        
        if t.attr == 'subst':
            return t.node + u'\u2193'.encode('utf-8')
        elif t.attr == 'head':
            return t.node + u'\u25c7'.encode('utf-8')
        elif t.attr == 'foot':
            return t.node + u'\u2605'.encode('utf-8')
        elif t.attr == None:
            return t.node
        elif t.attr == 'lex':
            return t.node
        else:
            raise TypeError("%s: Expected an attribute with value"
                            "subst, head or foot ")

    #def toggle_collapsed(self, treeseg):        
    #    self.show_fs(treeseg)

    def show_fs(self, treeseg):
        """
        Open a new window and display the top and bottom feature
        structure for the treesegment.
        """
        def fill(cw):
            from random import randint
            cw['fill'] = '#00%04d' % randint(0,9999)
        def color(cw):
            from random import randint
            cw['color'] = '#ff%04d' % randint(0,9999)
        
        self._fsw = Toplevel(self._top)
        node_name = treeseg.node()._text
        self._fsw.title('Feature Structure of ' + node_name)
        self._fsw.bind('<Control-p>', lambda e: self.print_to_file())
        self._fsw.bind('<Control-x>', self.destroy)
        self._fsw.bind('<Control-q>', self.destroy)

        top_str = 'Top Feature Structure'
        bot_str = 'Bottom Feature Structure'

        cf = CanvasFrame(self._fsw, closeenough=10, width=400, height=300)
        c = cf.canvas()
        top_fs = fs_widget(treeseg.top_fs(), self._all_fs, c, _fs_name(node_name, True))
        bot_fs = fs_widget(treeseg.bot_fs(), self._all_fs, c, _fs_name(node_name, False))
        top_text = TextWidget(c, top_str, justify='center')
        bot_text = TextWidget(c, bot_str, justify='center')
        cstack = StackWidget(c, top_text, top_fs, bot_text, bot_fs, align='center')
        cf.add_widget(cstack, 30, 30)
        cf.pack(expand=1, fill='both')
        self._fsw.mainloop()

#    def set_parent_window(self, parent):
#        self._top = parent

class TAGTreeView(TreeView):
    """
    A graphical diagram that displays a single TAG Tree, inherit from 
    ``TreeView``. ``TAGTreeView`` manages a group of ``TAGTreeWidget``
    that are used to display a TAG Tree. When read another
    tree to display, the ``TAGTreeWidget`` will be updated.

    """
    def __init__(self, parent, trees):

        if parent[0] is False:
            self._top = Tk()
            self._top.title('NLTK')
            self._top.bind('<Control-p>', lambda e: self.print_to_file())
            self._top.bind('<Control-x>', self.destroy)
            self._top.bind('<Control-q>', self.destroy)
        else:
            self._top = parent[1]

        self._cframe = CanvasFrame(self._top)
        self._widgets = []
        self.redraw(True, trees)

    def clear(self):
        """
        Clean canvas
        """
        self.redraw(False)

    def redraw(self, show, *trees, **attribs):
        """
        Update the current canvas to display another tree, set te feature
        sturctures to display or hidden.

        :param show: a boolean value for whether to show the feature
        sturcture on the canvas
        :param trees: a list of tree segments
        """   
        self._trees = trees
        for i in self._widgets:
            self._cframe.destroy_widget(i)
        self._size = IntVar(self._top)
        self._size.set(12)
        bold = ('helvetica', -self._size.get(), 'bold')
        helv = ('helvetica', -self._size.get())

        self._width = int(ceil(sqrt(len(trees))))
        self._widgets = []
        for i in range(len(trees)):
            if isinstance(trees[i], TAGTree):
                fs = trees[i].get_all_fs()
            else:
                fs = None
            widget = TAGTreeWidget(self._cframe.canvas(), trees[i], fs,
                                show, self._top, leaf_color='#008040',
                                roof_color='#004040', roof_fill='white',
                                line_color='#004040', leaf_font=helv, 
                                **attribs)
            widget['yspace'] = 70
            widget['xspace'] = 70
            #widget.set_parent_window(self._top)
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)
        self._init_menubar()

    def pack(self, cnf={}, **kw):
        """
        Pack the canvas frame of ``TreeView``.  See the documentation 
        for ``Tkinter.Pack`` for more information.
        """
        self._cframe.pack(cnf, **kw)


class TAGTreeSetView(object):
    """
    A window that displays a TAG Tree set. TAG Tree Set
    contains a group of TAG trees, when clicking the tree
    name on the tree list, the tree will be displayed on
    the canvas.

    """
    def __init__(self, tagtrees, parent=None):
        self._trees = tagtrees

        if parent is None:
            self._top = Tk()
            self._top.title('NLTK')
            self._top.bind('<Control-p>', lambda e: self.print_to_file())
            self._top.bind('<Control-x>', self.destroy)
            self._top.bind('<Control-q>', self.destroy)
            self._top.geometry("1400x800")
        else:
            self._top = parent[0]

        frame = Frame(self._top)

        v = StringVar()
        self.w = Label(frame, text='Regexp:')
        self._e = Entry(frame, textvariable=v)
        self._e.bind("<Return>", self.return_pressed)
        self._show_fs = True
        self._show_fs_button = Button(frame, text="Hide Features", command=self.show_fs)
        self._sfs_button = Button(frame, text="Add Start Features", command=self._start_fs)
        self.highlight_button = Button(frame, text="Highlight", command=self.highlight)
        self.remove_button = Button(frame, text="Remove", command=self.remove)
        self.keep_button = Button(frame, text="Keep", command=self.keep)
        self._sfs_button.pack(side=LEFT)
        self._show_fs_button.pack(side=LEFT)
        self.w.pack(side=LEFT)
        self._e.pack(expand=1, fill='both', side = LEFT)
        self.highlight_button.pack(side=RIGHT)
        self.keep_button.pack(side=RIGHT)
        self.remove_button.pack(side=RIGHT)
        

        statframe = Frame(self._top)
        self.notfl = Label(statframe, text='Tree Framilies:')
        self.notf = StringVar()
        self.nott = StringVar()
        self.tfcl = Label(statframe, textvariable=self.notf)
        self.nottl = Label(statframe, text='Trees:')
        self.tcl = Label(statframe, textvariable=self.nott)

        self.notf.set(str(self._trees.tree_family_count()))
        self.nott.set(str(self._trees.tree_count()))

        statframe.pack(side = BOTTOM, fill='both')
        self.notfl.pack(side = LEFT)
        self.tfcl.pack(side = LEFT)
        self.nottl.pack(side = LEFT)
        self.tcl.pack(side = LEFT)

        frame.pack(side = BOTTOM, fill='both')

        self._frame = Frame(self._top)
        self._frame.pack(fill='both', side = LEFT)
        
        self.cols = ('fullpath', 'type') 
        self._add_fs = True
        self._tagview = ttk.Treeview(self._frame, columns=self.cols, displaycolumns='',
                                     yscrollcommand=lambda f, l:autoscroll(vsb, f, l),
                                     xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
        ysb = ttk.Scrollbar(self._frame, orient=VERTICAL, command=self._tagview.yview)
        xsb = ttk.Scrollbar(self._frame, orient=HORIZONTAL, command=self._tagview.xview)
        self._tagview['yscroll'] = ysb.set
        self._tagview['xscroll'] = xsb.set
        if parent:
            self._tagview.bind('<<TreeviewSelect>>', parent[1])
        else:
            self._tagview.bind('<<TreeviewSelect>>', self.display)
        self.populate_tree('', self._trees)
        self._tagview.configure(xscrollcommand=xsb.set,
                                yscrollcommand=ysb.set)
        ysb.pack(fill='y', side='right')
        xsb.pack(fill='x', side='bottom')

        self._tagview.heading('#0', text='Trees', anchor=W)
        self._tagview.column('#0', stretch=1, width=220)

        self._tagview.pack(expand=1, fill='both')
        self._tw = TAGTreeView((True, self._top), None)
        self._tw.pack(expand=1, fill='both', side = LEFT)

    def return_pressed(self, event):
        words = self._e.get().split()
        if len(words) == 0:
            self._show_fs = False
            self.show_fs()
        return

    def _start_fs(self):
        if self._trees.start_fs is None:
            raise TypeError("Should set start feature for the TAG Trees First")
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        if self._add_fs:
            self._sfs_button['text'] = 'Delete Start Features'
            self.add_start_fs(tree, self._trees.start_fs)
        else:
            self._sfs_button['text'] = 'Add Start Features'
            self.del_start_fs(tree)
        self._add_fs = not self._add_fs

    def add_start_fs(self, tree, start_fs):
        root = tree.get_node_name() + '.t'
        all_fs = tree.get_all_fs()
        self._old_sfs = copy.deepcopy(all_fs[root])
        for i in start_fs:
            all_fs[root][i] = start_fs[i]
        tree.set_all_fs(all_fs)
        self._tw.redraw(self._show_fs, tree)

    def del_start_fs(self, tree):
        root = tree.get_node_name() + '.t'
        all_fs = tree.get_all_fs()
        all_fs[root] = self._old_sfs
        tree.set_all_fs(all_fs)
        self._old_sfs = None
        self._tw.redraw(self._show_fs, tree)
    
    def pack(self):
        """
        Pack the canvas frame of ``TAGTreeView``.
        """
        self._tagview.pack(expand=1, fill='both')
        self._frame.pack(fill='both', side = LEFT)
        self._tw.pack(expand=1, fill='both', side = LEFT)

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
            if tree._lex:
                tree.lexicalize()
                tree._lex = False
                self._tw.redraw(self._show_fs, tree)
            else:
                self._tw.redraw(self._show_fs, tree)

    def populate_tree(self, parent, trees):
        """
        Popluate the trees on the treeview.
        """
        if not trees:
            return
        #print sorted(trees.keys())
        for t in sorted(trees.keys()):
            node = parent
            parent_path = self._tagview.set(parent, "fullpath")
            path = parent_path + '/' + t
            if ord(t[0]) < 10:
                f_chr = self._tran_greek(t[0])
            else:
                f_chr = t[0]
            if isinstance(trees[t], type(trees)):
                node = self._tagview.insert(parent, END, text=f_chr+t[1:],
                                      values=[path, 'directory'])
                self.populate_tree(node, trees[t])
            else:
                self._tagview.insert(parent, END, text=f_chr+t[1:],
                                      values=[path, 'file'])
    
    def clear(self):
        """
        Empty the treeview and TAG tree set.
        """
        x = self._tagview.get_children()
        for item in x: 
            self._tagview.delete(item)
        self._trees = TAGTreeSet()

    def update(self, trees):
        """
        Update the window when the change the TAG tree set.
        """
        self._tw.clear()
        self._trees = trees
        self.populate_tree('', trees)
        self.notf.set(str(self._trees.tree_family_count()))
        self.nott.set(str(self._trees.tree_count()))

    def _tran_greek(self, ascii):    
        i = ord(u'\u03af') + ord(ascii)
        return unichr(i)

    def destroy(self, *e):
        if self._top is None: return
        self._top.destroy()
        self._top = None

    def mainloop(self, *args, **kwargs):
        """
        Enter the Tkinter mainloop.  This function must be called if
        this demo is created from a non-interactive program (e.g.
        from a secript); otherwise, the demo will close as soon as
        the script completes.
        """
        if in_idle(): return
        self._top.mainloop(*args, **kwargs)

    def show_fs(self):
        """
        Display or hide the feature structure on the canvas.
        """
        if self._show_fs:
            self._show_fs_button['text'] = 'Show Feature'
        else:
            self._show_fs_button['text'] = 'Hide Feature'
        self._e.delete(0, END)
        self._show_fs = not self._show_fs
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        if not isinstance(tree, type(self._trees)):
            self._tw.redraw(self._show_fs, tree)

    def keep(self):
        """
        Display the feature structures which match the
        input regular expression.
        """
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        if not isinstance(tree, type(self._trees)):
            self._tw.redraw(self._show_fs, tree, keep=True, reg=self._e.get())
        #return

    def highlight(self):
        """
        Remove the feature structures which match the
        input regular expression from the canvas.
        """
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        if not isinstance(tree, type(self._trees)):
            self._tw.redraw(self._show_fs, tree, highlight=True, reg=self._e.get())

    def remove(self):
        """
        Highlight the feature structures which match 
        the input regular expression.
        """
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        if not isinstance(tree, type(self._trees)):
            self._tw.redraw(self._show_fs, tree, remove=True, reg=self._e.get())
        #return

class TAGTreeSet(dict):
    """
    Basic data classes for representing a set of TAG Trees, and for
    iterating the set and performing basic operations on those 
    TAG Tree Set.  The set is a mapping from tree names to TAG trees.

    TAG Tree Sets are typically used to store the Tree information
    about TAG Tree Set. It can be merged with other TAG Tree Set.
    """
    def __init__(self, trees=None):
        dict.__init__(self)
        self.depth = 0
        self.start_fs = None
        if trees:
            self.update(trees)

    def __setitem__(self, tree_name, tree):
        dict.__setitem__(self, tree_name, tree)

    def __getitem__(self, tree_name):
        return self.get(tree_name, 0)

    def __str__(self):
        items = ['%r: %r' % (s, self[s]) for s in self.keys()[:10]]
        if len(self) > 10:
            items.append('...')
        return '<TAGTreeSet: %s>' % ', '.join(items)

    def __repr__(self):
        return '<TAGTreeSet with %d trees>' % (len(self))

    def __add__(self, other):
        clone = self.copy()
        clone.update(other)
        return clone

    def __le__(self, other):
        if not isinstance(other, TAGTreeSet): return False
        return set(self).issubset(other) and all(self[key] <= other[key] for key in self)
    def __lt__(self, other):
        if not isinstance(other, TAGTreeSet): return False
        return self <= other and self != other
    def __ge__(self, other):
        if not isinstance(other, TAGTreeSet): return False
        return other <= self
    def __gt__(self, other):
        if not isinstance(other, TAGTreeSet): return False
        return other < self

    def tree_names(self):
        """
        Get the name of trees
        """
        return self.keys()

    def update(self, trees):
        if not isinstance(trees, type(self)):
            raise TypeError("%s: Expected a TAGTreeSet value"
                             % type(self).__name__)
        for j in trees:
            if j in self:
                raise TypeError("%s: Overlapped Set " 
                                 % type(self).__name__)
            else:
                self[j] = trees[j]

    def view(self):
        """
        Display the TAG Tree Set
        """
        TAGTreeSetView(self).mainloop()

    def tree_count(self):
        """
        Get the total number of trees
        """
        total = 0 
        for tree in self:
            if isinstance(self[tree], TAGTreeSet):
                total += self[tree].tree_count()
            else:
                total += 1
        return total

    def tree_family_count(self):
        """
        Get the total number of tree families
        """
        total = 0 
        for tree in self:
            if isinstance(self[tree], TAGTreeSet) and tree[-6:] == '.trees':
                total += 1
            elif isinstance(self[tree], TAGTreeSet):
                total += self[tree].tree_family_count()
        return total

    def copy(self, deep=True):
        """
        Return a new copy of ``self``. 

        :param deep: If true, create a deep copy; if false, create
            a shallow copy.
        """
        if deep:
            return copy.deepcopy(self)
        else:
            clone = type(self)()
            for tree in self:
                if not isinstance(self[tree], TAGTreeSet):
                    clone[tree] = self[tree].copy(False)
                else:
                    clone += copy.copy(tree)
            return clone    

    def set_start_fs(self, fs):
        self.start_fs = fs 

def _parse_tree_list(txt, fs):
    tree_list = _parse_brackets(txt)
    t = _build_tree(tree_list[0], fs)
    return t

def _build_tree(tree_list, fs):
    node = _parse_node(tree_list[0])
    node_name = node[0]
    node_attr = node[1]
    top_fs = FeatStruct()
    bot_fs = FeatStruct()
    if node_name + '.t' in fs:
        top_fs = fs[node_name + '.t']
    if node_name + '.b' in fs:
        bot_fs = fs[node_name + '.b']
    if len(tree_list) == 1:
        return TAGTree((node_name, top_fs, bot_fs), [], node_attr)
    else:
        sub_tree = []
        for i in range(1, len(tree_list)):
	        sub_tree.append(_build_tree(tree_list[i], fs))
        return TAGTree((node_name, top_fs, bot_fs), sub_tree, node_attr)
 
def _parse_node(node_list):
    clist = []
    pre = node_list[0][0][0]
    suf = node_list[0][0][2]
    pre = pre.replace('"', '')
    suf = suf.replace('"', '')
    for i in range(0,2):
        if len(node_list) > 1:
            clist = [(node_list[2*j - 1], node_list[2 * j]) 
                      for j in range(1, len(node_list)/2 + 1)]
    if ord(pre[0]) == 6 and len(pre) == 1:
        pre = u'\u03b5'.encode('utf-8')
    
    if len(suf) != 0:
        pre = pre + '_' + suf
    if (':substp', 'T') in clist:
        attr = 'subst'
    elif (':headp', 'T') in clist:
        attr = 'head'
    elif (':footp', 'T') in clist:
        attr = 'foot'
    else:
        attr = None
    return (pre, attr, clist)
 
def _parse_brackets(txt):
    txt = '(' + txt + ')'
    lresult = []
    ss = ''
    for c in txt:
        if c == '(':
            if len(ss) != 0:
                lresult.append(lresult.pop() + ss.split())
                ss = ''
            lresult.append([])
        elif c == ')':
            last = lresult.pop()
            if len(ss) != 0:
                last += ss.split()
                ss = ''
            if len(lresult) > 0:
                lresult.append(lresult.pop() + [last])
            else:
                lresult.append(last)
        else:
            ss += c
    return lresult[0]

def xtag_parser(txt):
    """
    Get a TAGTreeSet

    :param txt is a string describing TAG trees, the form is defined in
    UPenn Xtag project
    """
    arglist = analyze_tree_5(analyze_tree_4(analyze_tree_3(analyze_tree_2(analyze_tree_1(txt)))))
    tagset = TAGTreeSet()       
    for element in arglist:
        new_tree = _parse_tree_list(element[2], element[4])
        tree_name = element[0]
        tagset[tree_name] = new_tree
    return tagset

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
        self._cframe = CanvasFrame(self._top)
        self._widgets = []
        treetok = Tree.parse('(A (walk C D) (E (F G) (H I)))')
        self._merge = TreeMerge([treetok], self)
        #self._merge = TreeMerge([trees], self)
        self._tset = self._merge.tree()
        self._ps = None
        self._os = None
        self.w['text'] = '    Input Sentence:    '
        self.highlight_button['text'] = '  Parse  '
        self.highlight_button['command'] = self.parse
        self.keep_button.pack_forget()
        self.remove_button.pack_forget()
        self._show_fs_button.pack_forget()
        self._sfs_button.pack_forget()
        self.notfl['text'] = ''
        self.nottl['text'] = ''
        self.tfcl.pack_forget()
        self.tcl.pack_forget()
        #self.parser = parser

    def parse(self):
        self.redraw()
        #words = word_tokenize(self._e.get())
        #print words
        #graph = self.parser.parse(words)
        #print graph


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
        #                     self._top, self, self.boxit)
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
        #    print trees[i]
            #if isinstance(trees[i], TAGTree):
            #    fs = trees[i].get_all_fs()
            #else:
            #    fs = None
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
            if i % width == 0:
                y = ymax
                x = 0
            widget.move(x-oldx, y-oldy)
            x = widget.bbox()[2] + 10
            ymax = max(ymax, widget.bbox()[3] + 10)

    def boxit(self, canvas, text):
        big = ('helvetica', -16, 'bold')
        return GraphElementWidget(canvas, TextWidget(canvas, text,
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


    #def ovalit(canvas, text):
    #    return OvalWidget(canvas, TextWidget(canvas, text),
                          #fill='cyan')
    #treetok = Tree.parse('(S (NP this tree) (VP (V is) (AdjP shapeable)))')
    #tc2 = GraphWidget(cf.canvas(), treetok, boxit, boxit)

class TAGTree(Tree):
    """
    A TAG Tree represents a lexicalized Tree Adjoining Grammar (TAG)
    formalism. The TAGTree is inherited from Tree Object, A Tree 
    represents a hierarchical grouping of leaves and subtrees. And 
    it contains a top feature structure and a bottom feature structure
    for every node. Some nodes are specified as head nodes, foot nodes,
    or substitution nodes.

    The TAG Tree can be lexicalized, which means we can attach a word
    to the substitution node and unify the feature structures in the 
    tree with the feature structures of the attachd node.
    """    
    def __init__(self, node_with_fs, children, attr=None):
        self.attr = attr
        self._lex = False
        if isinstance(node_with_fs, basestring):
            #(self.node, self.top_fs, self.bot_fs) = (node_with_fs, FeatStruct(), FeatStruct())
            self.node = node_with_fs
            self.top_fs = FeatStruct()
            self.bot_fs = FeatStruct()
            Tree.__init__(self, self.node, children)
        elif len(node_with_fs) == 3:
            (self.node, self.top_fs, self.bot_fs) = node_with_fs
            Tree.__init__(self, self.node, children)
        else:
            raise TypeError("%s: Expected a node value with feature"
                            "structures and child list " % type(self).__name__)
        if isinstance(children, basestring):
            raise TypeError("%s() argument 2 should be a list, not a "
                            "string" % type(self).__name__)

    def draw(self):
        """
        Display the TAGTree on canvas
        """
        draw_trees(self)

    def copy(self, deep=False):
        """
        Return a new copy of ``self``. 

        :param deep: If true, create a deep copy; if false, create
            a shallow copy.
        """
        if deep:
            return copy.deepcopy(self)
        else:
            clone = copy.copy(self)
            if clone._lex:
                clone._lex_fs = copy.deepcopy(self._lex_fs)
        return clone

    def _get_node(self, name_or_attr):
        nodes = []
        results = []
        nodes.append(self)
        while len(nodes) > 0:
            last = nodes.pop()
            if last.node == name_or_attr or last.attr == name_or_attr:
                results.append(last)
            else:
                for child in last:
                    if isinstance(child, TAGTree):
                        nodes.append(child)
        return results

    def get_head(self):
        """
        Get the head node of the TAG Tree
        """
        return self._get_node('head')

    def set_children(self, children):
        """
        Set the children of the current TAGTree
        """
        if isinstance(children, basestring):
            raise TypeError("%s() argument 2 should be a list, not a "
                            "string" % type(self).__name__)
        self.append(children)

    def init_lex(self, morph, fs1, fs2):
        """
        Prepare and initialization before lexicalization

        :param morph, the morphology to operate lexicalization
        :param fs1, the node feature structure to unify
        :param fs2, the tree feature structure to unify
        """
        self._morph = morph
        self._lex_fs = []
        for nf in fs1+fs2:
            for key in nf.keys():
                tf = FeatStruct()
                if key[-2:] not in ['.t', '.b']:
                    tf[_fs_name(morph[0][1], False)] = FeatStruct()
                    tf[_fs_name(morph[0][1], False)][key] = nf[key]
                else:
                    tf[key] = nf[key]
                self._lex_fs.append(tf)
        self._lex = True

    def lexicalize(self):
        """
        Do lexicalization operation, attach the lex
        to the substitution node, unify the feature
        structure defined in grammar files
        """
        morph = self._morph
        fs = self._lex_fs
        heads = self.get_head()
        for head in heads:
            for m in morph:
                if head.get_node_name().replace('_','') == m[1]:
                    lex = TAGTree(m[0], [], 'lex')
                    head.set_children(lex)
                    all_fs = self.get_all_fs()
                    for f in fs:
                        #all_fs = all_fs.unify(f)
                        temp = all_fs.unify(f)
                        if temp:
                            all_fs = temp
                        else:
                            keys = f.keys()[0]
                            key = f[keys]
                            for i in all_fs:
                                if i == keys:
                                    temp = all_fs[i]
                                    for j in key:
                                        result = []
                                        child = all_fs.items()
                                        self._find_value(all_fs, id(temp[j]), f[keys][j])
                    self.set_all_fs(all_fs)

    def unify(self, fs):
        all_fs = self.get_all_fs()
        temp = all_fs.unify(f)
        if temp:
            all_fs = temp
        else:
            raise NameError("Unify return None")
        self.set_all_fs(all_fs)

    def _find_value(self, fs, idn, cfs):
        for i in fs:
            if len(fs[i].keys()) > 0 and fs[i].keys()[0][0:5] == '__or_':
                if id(fs[i]) == idn:
                    fs[i] = cfs
            else:
                self._find_value(fs[i], idn, cfs)

    def get_node_name(self):
        return self.node

    def get_all_fs(self):
        """
        Get the overall feature structure of the TAGTree
        """
        stack = []
        all_feat = FeatStruct()
        stack.append(self)
        while len(stack) > 0:
            last = stack.pop()
            all_feat[last.node+'.'+'t'] = last.top_fs
            all_feat[last.node+'.'+'b'] = last.bot_fs
            for child in last:
                if isinstance(child, TAGTree):
                    stack.append(child)
        return all_feat

    def set_all_fs(self, all_fs):
        """
        Update the feature structure of the TAGTree
        """
        if not all_fs:
            return
        nodes = []
        nodes.append(self)
        while len(nodes) > 0:
            last = nodes.pop()
            if last.node+'.'+'t' not in all_fs:
                if last.node+'.'+'b' not in all_fs:
                    raise NameError('should contain feature structures')
            last.top_fs = all_fs[last.node+'.'+'t']
            last.bot_fs = all_fs[last.node+'.'+'b']
            for child in last:
                if isinstance(child, TAGTree):
                    nodes.append(child)

    def leaves(self):
        leaves = []
        if len(self) == 0:
            leaves.append(self)
        for child in self:
            leaves.extend(child.leaves())
        return leaves

    def cancel_substitution(self):
        if self.attr == 'subst':
            self.attr = None
        else:
            raise TypeError("n")

    def get_substitution_node(self):
        sub = []
        for leaf in self.leaves():
            if leaf.attr == 'subst':
                sub.append(leaf)
        return sub

    def at_anchor_left(self, tree):
        tree_name = tree.node
        self._leaves = self.leaves()
        sub_node = self.get_substitution_node()
        ind = self._leaves.index(sub_node)
        left_node = self._leaves[ind-1]
        if left_node.node == tree_name:
            return True
        else:
            return False

    def prefix_search(self, tree_name):
        trees = []
        name = self.node.split('_')
        if len(name) > 1:
            prefix = name[0]
        if prefix == prefix:
            trees.append(self)
        for child in self:
            trees.extend(child.search())
        return trees

    def delete_all_child(self):
        result = []
        while(len(self)) > 0:
            self.pop()

    def cancel_adjunction(self):
        if self.attr == 'foot':
            self.attr = None
        else:
            raise TypeError("n")

    def search(self, tree_name):
        if self.node == tree_name:
            return self
        else:
            for child in self:
                tree = child.search(tree_name)
                if tree != None:
                    return tree
        return None

    def get_child_node(self):
        return [child for child in self]

    def append_new_child(self, tree):
        self.append(tree)

    def get_top_feature(self):
        return self.top_fs

    def get_bottom_feature(self):
        return self.bot_fs

    def set_bottom_feature(self, fs):
        self.bot_fs[key]['__or_'+value] = value

    def get_foot_node(self):
        for leaf in self.leaves():
            if leaf.attr == 'foot':
                return leaf
        return None        

def _fs_name(node_name, top):
    try:
        node_name[-1].decode('ascii')
    except UnicodeDecodeError:
        node_name = node_name[:-3]
    if top:
        return node_name+'.'+'t'
    else:
        return node_name+'.'+'b'

def draw_trees(*trees):
    """
    Display the TAGTree in a single window.
    """
    TAGTreeView((False,None),*trees).mainloop()
    return

def _all_widget(feats, reentrances, reentrance_ids, c, name):

    segments = []
    prefix = ''
    suffix = ''

    if reentrances[id(feats)]:
        assert not reentrance_ids.has_key(id(feats))
        reentrance_ids[id(feats)] = repr(len(reentrance_ids)+1)

    namelist = [i for i, v in feats.items() if i == name]
    if len(namelist) > 1:
        raise TypeError('Error')

    for (fname, fval) in sorted(feats.items()):
        display = getattr(fname, 'display', None)
        if len(namelist) == 1:
            if name == fname:
                fval_repr = _fs_widget(fval, reentrances, reentrance_ids, c)
                return SequenceWidget(c, fval_repr, align='center')
        elif reentrance_ids.has_key(id(fval)):
            fs = '%s->(%s)' % (fname, reentrance_ids[id(fval)])
            tw = TextWidget(c, fs, justify='center')
            segments.append(tw)
        elif (display == 'prefix' and not prefix and
              isinstance(fval, (Variable, basestring))):
                prefix = '%s' % fval
        elif display == 'slash' and not suffix:
            if isinstance(fval, Variable):
                suffix = '/%s' % fval.name
            else:
                suffix = '/%r' % fval
        elif isinstance(fval, Variable):
            fs = '%s=%s' % (fname, fval.name)
            tw = TextWidget(c, fs, justify='center')
            segments.append(tw)
        elif fval is True:
            fs = '+%s' % fname
            tw = TextWidget(c, fs, justify='center')
            segments.append(tw)
        elif fval is False:
            fs = '-%s' % fname
            tw = TextWidget(c, fs, justify='center')
            segments.append(tw)
        elif isinstance(fval, Expression):
            fs = '%s=<%s>' % (fname, fval)
            tw = TextWidget(c, fs, justify='center')
            segments.append(tw)
        elif not isinstance(fval, FeatStruct):
            fs = '%s=%r' % (fname, fval)
            tw = TextWidget(c, fs, justify='center')
            segments.append(tw)
        else:
            fval_repr = _fs_widget(fval, reentrances, reentrance_ids, c)
            tw = TextWidget(c, '%s=' % fname, justify='center')
            sw = SequenceWidget(c, tw, fval_repr, align='center')
            segments.append(sw)
    if reentrances[id(feats)]:
        prefix = '(%s)%s' % (reentrance_ids[id(feats)], prefix)

    cstack = StackWidget(c, *segments)
    widgets = []
    if prefix:
        pw = TextWidget(c, prefix, justify='center')
        widgets.append(pw)
    bw = BracketWidget(c, cstack, color='black', width=1)
    widgets.append(bw)
    if suffix: 
        sw = TextWidget(c, suffix, justify='center')
        widgets.append(sw)
    return SequenceWidget(c, *widgets, align='center')

def _fs_widget(feats, c, name, **attribs):
    old_name = []
    for fname in feats:
        if ord(fname[0]) > 206:
            f_chr = ord(u'\u03af') + ord(fname[0])
            uname = f_chr + fname[1:]
            feats[uname] = feats[fname]
            old_name.append(fname)
    for name in old_name:
    #    print name
        del feats[name]

    #for name in feats:
        #print ord(name[0]), name[0]
        #print name

    fstr = feats.__repr__()
    #print fstr

    fstr = fstr.replace('__value__=','')
    fstr = fstr.replace("'",'')
    
    d = {}
    for (attr, value) in attribs.items(): 
        d[attr] = value
    reg = None
    if 'reg' in d:
        reg = d['reg']
    s = fstr.find(name)
    l = _find_left_bracket(fstr[s:])
    r = _match_bracket(fstr[s:])
    match_str = fstr[s+l+1:s+r]
    result = match_str

    if s+l+1 == s+r or not match_str:
        return TextWidget(c, '[ ]', justify='center')

    if reg and len(reg) > 0:
        if 'highlight' in d:
            match_list = re.split('(\[|\,|\])', match_str)
            result = ''
            for i in match_list:
                try:    
                    result += re.compile(r'((%s\s*)+)' % reg).sub(r'<h>\1<h>', i)
                except re.error, e:
                    #print e
                    widget = _parse_to_widget(match_str, c)
                    return BracketWidget(c, widget, color='black', width=1)
            widget = _parse_to_widget(result, c, True)
        elif 'keep' in d:
            fstr = match_feature(feats, reg, 0).__repr__()
            fstr = fstr.replace("'",'')
            fstr = fstr.replace('__value__=','')
            s = fstr.find(name)
            l = _find_left_bracket(fstr[s:])
            r = _match_bracket(fstr[s:])
            if l and r:
                result = fstr[s+l+1:s+r]
            else:
                return TextWidget(c, '[ ]', justify='center')
            widget = _parse_to_widget(result, c)
        elif 'remove' in d:
            fstr = match_feature(feats, reg, 1).__repr__()
            fstr = fstr.replace('__value__=','')
            fstr = fstr.replace("'",'')
            s = fstr.find(name)
            l = _find_left_bracket(fstr[s:])
            r = _match_bracket(fstr[s:])
            if l and r:
                result = fstr[s+l+1:s+r]
            else:
                result = match_str
            widget = _parse_to_widget(result, c)
    else:
        widget = _parse_to_widget(result, c)
    return BracketWidget(c, widget, color='black', width=1)

def _parse_to_widget(fstr, c, highlight=False):
    wl = []
    l = _find_left_bracket(fstr)
    if l:
        r = _match_bracket(fstr)
        lw = _parse_to_widget(fstr[l+1:r], c, highlight)
        tl = []
        strlist = fstr[:l].split(',')
        for item in strlist[:-1]:
            if len(item) > 0:
                if highlight and ('<h>' in item):
                    tl.append(BoxWidget(c, TextWidget(c, '%s' % item.replace('<h>',''), justify='center'), outline='white', fill='yellow'))
                else:
                    tl.append(TextWidget(c, '%s' % item, justify='center'))
        if highlight and ('<h>' in strlist[-1]):
            tw = BoxWidget(c, TextWidget(c, '%s' % strlist[-1].replace('<h>',''), justify='center'), outline='white', fill='yellow')
        else:
            tw = TextWidget(c, '%s' % strlist[-1], justify='center')
        if not isinstance(lw, TextWidget):
            lw = BracketWidget(c, lw, color='black', width=1)
        tl.append(SequenceWidget(c, tw, lw, align='center'))
        wl.append(StackWidget(c, *tl))
        if r+1 != len(fstr):
            wl.append(_parse_to_widget(fstr[r+1:len(fstr)], c, highlight))
    else:
        tl = []
        textl = fstr.split(',')
        textl = filter(None, textl)
        if len(textl) == 0:
            return TextWidget(c, '[ ]', justify='center')
        elif highlight:
            for item in textl:
                item = item.replace('__value__=','')
                item = item.replace("'",'')
                if '<h>' in item:
                    tl.append(BoxWidget(c, TextWidget(c, '%s' % item.replace('<h>',''), justify='center'), outline='white', fill='yellow'))
                else:
                    tl.append(TextWidget(c, '%s' % item, justify='center'))
            return StackWidget(c, *tl)
        elif len(textl) == 1:
            if '->(' in textl[0]:
                return TextWidget(c, '%s' % textl[0], justify='center')
            else:
                return TextWidget(c, '[ %s ]' % textl[0], justify='center')
        else:
            for item in textl:
                tl.append(TextWidget(c, '%s' % item, justify='center'))
            return StackWidget(c, *tl)
    cstack = StackWidget(c, *wl)
    return cstack


def _find_left_bracket(fstr):
    for i in range(0, len(fstr)):
        if fstr[i] == '[':
            return i

def _match_bracket(fstr):
    count = 0
    for i in range(0, len(fstr)):
        if fstr[i] == '[':
            count += 1
        elif count > 0 and fstr[i] == ']':
            count -= 1
            if count == 0:
                return i       

def fs_widget(fs, allfs, canvas, name, **attribs):
    """
    Get the widget of feature structure.

    param: fs, the current feature structure to display
    param: allfs, the overall feature structure of the
    tree
    param: canvas, the canvas the feature structure 
    widget to attach
    param: name, the node name of the feature structure
    param: attribs, the attribs of the widget
    """
    if fs:
        return _fs_widget(allfs, canvas, name, **attribs)
    else:
        return TextWidget(canvas, '[ ]', justify='center')

def parse_from_files(cata, files):
    """
    Get the TAGTreeSet from the gram file. The file format
    is defined in Upenn Xtag project.
    """
    if not isinstance(files, basestring):
        raise TypeError('input should be a base string')
    tree_list = get_file_list(cata, files)
    tagset = TAGTreeSet()
    tagset[files] = TAGTreeSet()

    file_names = tree_list[0]
    directory = tree_list[1]
    for fn in file_names:
        path = 'xtag_grammar' + os.sep + directory + os.sep + fn
        #print path
        text = nltk.data.find(path).open().read()
        #text = open(path).read()
        tagset[files][fn] = TAGTreeSet()
        tagset[files][fn] += xtag_parser(text)
 
    return tagset

def demo():
    from util import xtag_parser
    from util import parse_from_files

    cata_str = nltk.data.find('xtag_grammar/english.gram').open().read()
    cata = get_catalog(cata_str)
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    for i in t['family-files']['Tnx0ARBPnx1.trees']:
        tree = t['family-files']['Tnx0ARBPnx1.trees'][i]
    #print tree.get_substitution_node()
    A = TAGTree('P',[])
    #print tree.search('S_r').get_bottom_feature()
    #print tree.search('VP').get_top_feature()
    #print id(tree.search('VP').get_top_feature()['mode'])
    #print id(tree.search('S_r').get_bottom_feature()['mode'])
    #print tree.search('S_r').get_bottom_feature()
    #print tree.search('VP').get_top_feature()
    #print tree
    tree.draw()
    #print t['family-files']['Tnx0ARBPnx1.trees']['nx0ARBPnx1-PRO']#.view()
    #t.view()


if __name__ == '__main__':
    #demo()
    #load()
    install()
