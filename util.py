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
import nltk.data
import pickle

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
from nltk.parse.dependencygraph import *

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
    obj = pickle.load(fp)
    return obj

def install():
    """
    Install pickle file of the TAG forest to speed up.
    """
    language = 'english'
    try:
        nltk.data.find('xtag_grammar/'+language+'/pickles/tagtreeset.pickle')
    except LookupError:
        update(language)

def update(language):
    """
    Update the TAG trees pickle file to speed up.
    """
    for path_item in nltk.data.path:
        d = 'xtag_grammar/'+language
        p = os.path.join(path_item, *d.split('/'))
        if os.path.exists(p):
            t = init_trees()
            pic_dir = os.path.join(p, 'pickles')
            if not os.path.exists(pic_dir):
                os.makedirs(pic_dir)
            tree_dir = os.path.join(pic_dir, 'tagtreeset.pickle')
            dump_to_disk(tree_dir, t)
            return

def init_trees():
    """
    Initialize the TAG tree Forests from tree files in xtag_grammar/grammar/
    :return: The forest of all TAG trees
    :rype: TAGTreeSet
    """
    language = 'english'
    cata_dir = 'xtag_grammar/'+language+'/english.gram'
    cata_str = nltk.data.find(cata_dir).open().read()
    cata = get_catalog(cata_str)
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    return t

def load():
    """
    Load the forest pickle to initilize the TAG forest, load the morphology
    files, lexicon files, template files, syntax files and mapping file
    :return: The forest of all TAG trees
    :rype: TAGTreeSet
    """
    xtag_dir = 'xtag_grammar'
    language = 'english'
    cata_dir = 'xtag_grammar/'+language+'/english.gram'
    pickle_dir = 'xtag_grammar/'+language+'/pickles/tagtreeset.pickle'
    cata_str = nltk.data.find(cata_dir).open().read()
    
    cata = get_catalog(cata_str)

    treefile = nltk.data.find(pickle_dir).open()
    treeset = restore_from_disk(treefile)
    morph = get_file_list(cata, 'morphology-files')
    syn = get_file_list(cata, 'lexicon-files')
    temp = get_file_list(cata, 'templates-files')
    default = get_file_list(cata, 'syntax-default')


    morph_path = os.sep.join([xtag_dir, language, morph[1], morph[0][0]])
    syn_path = os.sep.join([xtag_dir, language, syn[1], syn[0][0]])
    temp_path = os.sep.join([xtag_dir, language, temp[1], temp[0][0]])
    default_path = os.sep.join([xtag_dir, language,default[1], default[0][0]])
    mapping_path = os.sep.join([xtag_dir, language, 'syntax_morph.mapping'])

    morph_str = nltk.data.find(morph_path).open().read()
    syn_str = nltk.data.find(syn_path).open().read()
    temp_str = nltk.data.find(temp_path).open().read()
    default_str = nltk.data.find(default_path).open().read()
    mapping_str = nltk.data.find(mapping_path).open().read()

    init(morph_str, syn_str, temp_str, default_str, mapping_str)

    return treeset   

class TAGTreeView(TreeView):
    """
    A graphical diagram that displays a single TAG Tree, inherit from 
    ``TreeView``. ``TAGTreeView`` manages a group of ``TAGTreeWidget``
    that are used to display a TAG Tree. When read another
    tree to display, the ``TAGTreeWidget`` will be updated.

    """
    def __init__(self, trees, **kwargs):
        if "parent" in kwargs:
            self._top = kwargs["parent"]
        else:
            self._top = Tk()
            self._top.title('NLTK')
            self._top.bind('<Control-p>', lambda e: self.print_to_file())
            self._top.bind('<Control-x>', self.destroy)
            self._top.bind('<Control-q>', self.destroy)

        self._cframe = CanvasFrame(self._top)
        self._widgets = []
        self.treecomment = {}
        self.oldcomment = None
        self.show_fs = True
        self._trees = trees
        self.redraw(True, trees)


    def _init_menubar(self):
        """
        Hide menubar
        """
        pass

    def clear(self):
        """
        Clean canvas
        """
        self.redraw(False)

    def collapse_comment(self):
        """
        Show comment of selected TAG tree
        """
        self._cframe.add_widget(self.treecomment[id(self._trees[0])].widget(),
                                750, 0)

        trees = self._trees
        show = self.show_fs
        for i in self._widgets:
            self._cframe.destroy_widget(i)
        self._sizeco = IntVar(self._top)
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
                                **self.attribs)
            widget['yspace'] = 70
            widget['xspace'] = 70
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        
        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)

    def redraw(self, show, *trees, **attribs):
        """
        Update the current canvas to display another tree, set te feature
        sturctures to display or hidden.

        :param show: a boolean value for whether to show the feature
        sturcture on the canvas
        :type: bool
        :param trees: a list of tree segments
        :type: list
        """ 
        self.attribs = attribs
        if trees and isinstance(trees[0], TAGTree): 
            if self.oldcomment:
                self._cframe.destroy_widget(self.oldcomment.widget()) 
            self.treecomment[id(trees[0])] = CommentWidget(self._cframe.canvas(),
                                                           self,width=300)
            self.oldcomment = self.treecomment[id(trees[0])]
            self._cframe.add_widget(self.oldcomment.widget(), 750, 0)
        else:
            if self.oldcomment:
                self._cframe.destroy_widget(self.oldcomment.widget())
                self.oldcomment = None

        self._trees = trees
        self.show_fs = show
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
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        
        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)

    def pack(self, cnf={}, **kw):
        """
        Pack the canvas frame of ``TreeView``.  See the documentation 
        for ``Tkinter.Pack`` for more information.
        """
        self._cframe.pack(cnf, **kw)

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
        """
        Set start feature of all TAG trees.
        :param fs: start feature
        :type: FeatStruct
        """
        self.start_fs = fs 

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
        self._show_fs_button = Button(frame, text="Hide Features",
                                      command=self.show_fs)
        self._sfs_button = Button(frame, text="Add Start Features",
                                  command=self.start_feat)
        self.highlight_button = Button(frame, text="Highlight",
                                       command=self.highlight)
        self.remove_button = Button(frame, text="Remove",
                                    command=self.remove)
        self.keep_button = Button(frame, text="Keep",
                                  command=self.keep)
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
        self._tagview = ttk.Treeview(self._frame, columns=self.cols,
                            displaycolumns='',
                            yscrollcommand=lambda f, l:autoscroll(vsb, f, l),
                            xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
        ysb = ttk.Scrollbar(self._frame, orient=VERTICAL, 
                            command=self._tagview.yview)
        xsb = ttk.Scrollbar(self._frame, orient=HORIZONTAL,
                            command=self._tagview.xview)
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
        self._tw = TAGTreeView(None, parent=self._top)
        self._tw.pack(expand=1, fill='both', side = LEFT)
        self.sfs_tree ={}

    def return_pressed(self, event):
        """
        Short-cut for pressing return to show feature structures
        """
        words = self._e.get().split()
        if len(words) == 0:
            self._show_fs = False
            self.show_fs()
        return

    def start_feat(self):
        """
        Add or Remove start feature structure of TAG tree set
        """
        if self._trees.start_fs is None:
            raise TypeError("Should set start feature for TAG Trees First")
        node = self._tagview.focus()
        path = self._tagview.set(node, "fullpath").split('/')
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        if isinstance(tree, type(self._trees)):
            return
        print self.sfs_tree
        print tree, id(tree)
        if not tree.start_feat:
            self._sfs_button['text'] = 'Delete Start Features'
            self.add_start_fs(tree, self._trees.start_fs)
            tree.start_feat = True
        else:
            self._sfs_button['text'] = 'Add Start Features'
            self.del_start_fs(tree)
            tree.start_feat = False
        self._add_fs = not self._add_fs

    def add_start_fs(self, tree, start_fs):
        """
        Add start feature structure.
        :param tree: display tree
        :type: TAGTree
        :param start_fs: start feature structure
        :type: FeatStruct
        """
        root = tree.get_node_name() + '.t'
        all_fs = tree.get_all_fs()
        self._old_sfs = copy.deepcopy(all_fs[root])
        for i in start_fs:
            all_fs[root][i] = start_fs[i]
        tree.set_all_fs(all_fs)
        self._tw.redraw(self._show_fs, tree)

    def del_start_fs(self, tree):
        """
        Remove start feature structure.
        :param tree: display tree
        :type: TAGTree
        """
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

    def focus(self):
        """
        Get selected TAGTree
        :return: selected treeview
        :rtype: TAGTree
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
            return (tree, subpath)

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
        for t in sorted(trees.keys()):
            node = parent
            parent_path = self._tagview.set(parent, "fullpath")
            path = parent_path + '/' + t
            if ord(t[0]) < 10:
                f_chr = self.greek(t[0])
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
        self._sfs_button['text'] = 'Add Start Features'
        self._add_fs = True
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

    def greek(self, ascii):
        """
        Translate ASCII to greek letter
        """    
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
        self._show_fs_button['text'] = 'Show ALL Features'
        self._show_fs = False
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
            self._tw.redraw(self._show_fs, tree, 
                            highlight=True, reg=self._e.get())

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
            self._tw.redraw(self._show_fs, tree, 
                            remove=True, reg=self._e.get())
        self._show_fs_button['text'] = 'Show ALL Features'
        self._show_fs = False

class CommentWidget(object):
    """
    A canvas widget that displays a comment of a tree.
    Click to collapse or close the comment

    Attributes:

      - ``xposition``: the x cordinates of the widget on canvas
      - ``yposition``: the y cordinates of the widget on canvas
      - ``width``: width of comment width

    """
    def __init__(self, canvas, parent, **attribs):
        self._attr = {}
        for (i, j) in attribs.items():
            if i in ['xposition', 'yposition', 'width']:
                self._attr[i] = j
                del attribs[i]
        self.canvas = canvas
        self.attribs = attribs
        self.viewer = parent
        self.tri = TextWidget(canvas, u'\u25b6'.encode('utf-8')+'    COMMENTS')
        self.tri.bind_click(self.collapse)
        self.show = False
        self.stack = StackWidget(canvas, self.tri, **attribs)

    def widget(self):
        return self.stack

    def collapse(self, event):
        if self.show:
            self.viewer._cframe.destroy_widget(self.stack)
            self.tri = TextWidget(self.canvas, 
                                  u'\u25b6'.encode('utf-8') + '    COMMENTS')
            self.tri.bind_click(self.collapse)
            self.stack = StackWidget(self.canvas, self.tri, **self.attribs)
        else:
            self.viewer._cframe.destroy_widget(self.stack)
            self.tri = TextWidget(self.canvas, 
                                  u'\u25bc'.encode('utf-8') + '    COMMENTS')
            self.tri.bind_click(self.collapse)
            comment = TextWidget(self.canvas, self.viewer._trees[0].comment, 
                                  width=self._attr['width']-40)
            hspace1 = SpaceWidget(self.canvas, self._attr['width'], 0)
            hspace2 = SpaceWidget(self.canvas, self._attr['width'], 0)              
            tstack = StackWidget(self.canvas, hspace1, comment, hspace2)
            box = BoxWidget(self.canvas, tstack)
            self.stack = StackWidget(self.canvas, self.tri, box, align='left')
        self.show = not self.show
        self.viewer.collapse_comment()

class TAGTreeWidget(TreeWidget):
    """
    A canvas widget that displays a single TAG Tree, inherit from 
    ``TreeWidget``. ``TAGTreeWidget`` manages a group of ``TreeSegmentWidgets``
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
            node_name = self.get_node_name(t)
            bold = ('helvetica', -24, 'bold')
            node = make_node(canvas, node_name, font=bold,
                                color='#004080')

            if self._show_fs:
                top_fs = feat_widget(t.top_fs, self._all_fs, canvas, 
                               global_featname(node_name, True), **self._attr)
                bot_fs = feat_widget(t.bot_fs, self._all_fs, canvas,
                            global_featname(node_name, False), **self._attr)
                cstack = StackWidget(canvas, top_fs, bot_fs, align='left')
                node =  SequenceWidget(canvas, node, cstack, align='top')

            self._nodes.append(node)
            children = t
            subtrees = [self._make_expanded_tree(canvas, children[i], key+(i,))
                        for i in range(len(children))]
            top_name = global_featname(t.node, True)
            bot_name = global_featname(t.node, False)
            top_fs = FeatStruct()
            bot_fs = FeatStruct()
            if top_name in self._all_fs:
                top_fs = self._all_fs[top_name]
            if bot_name in self._all_fs:
                bot_fs = self._all_fs[bot_name]

            treeseg = TreeSegmentWidget(canvas, node, subtrees, 
                                        color=self._line_color,
                                        width=self._line_width)
            self._expanded_trees[key] = treeseg
            self._keys[treeseg] = key

            return treeseg
        else:
            leaf = make_leaf(canvas, t, **self._leafattribs)
            self._leaves.append(leaf)
            return leaf

    def get_node_name(self, t):    
        """
        Get the name of the current node, use specific symbols
        for substitution node, head node and foot node.
        :param t: Current node
        :type t: TAGTree
        :return: Node name
        :rtype: str
        """    
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

def lex_search(lex_list, count, alltrees):
    """
    Lexicalized current tree set
    :param lex_list: a list of lexicalized node
    :type: list
    :alltrees: TAG tree set to be lexicalized
    :type: TAGTreeSet
    """
    fset = TAGTreeSet()
    for morph in lex_list:
        index = ''
        for i in morph[0]:
            index = index + i[0] + '.' + i[1] + ' '
        for i in morph[5][1]:
            index = index + i + '_'
        index = index[:-1]
        if index not in fset:
            fset[index] = TAGTreeSet()
        sset = fset[index]
        if len(morph[2]) > 0:
            for tf in morph[2]:
                ckey = index+tf
                tf = tf + '.trees'
                if tf not in sset:
                    key = tf
                    count[ckey] = 0
                else:
                    key = tf[:-5] + '_' + str(count[ckey]) + '.trees'
                sset[key] = TAGTreeSet()
                index = None
                for sub in alltrees:
                    if tf in alltrees[sub]:
                        index = sub
                if not index:
                    raise NameError('No tree fmaily')
                sset[key] += alltrees[index][tf].copy(True)
                for t in sset[key]:
                    if sset[key][t]._lex:
                        sset[key][t]._lex_fs
                    sset[key][t].init_lex(morph[0], morph[3], morph[4])
                count[ckey] += 1
        else:
            for t in morph[1]:
                ckey = index+t
                if t not in sset:
                    key = t
                    count[ckey] = 0
                else:
                    key = t + '_' + str(count[ckey])

                for sub in alltrees:
                    for tr in alltrees[sub]:
                        if t in alltrees[sub][tr]:
                            sset[key] = alltrees[sub][tr][t].copy(True)
                count[ckey] += 1
                if not isinstance(sset[key], TAGTree):
                    raise TypeError('Not TAGTree')
                sset[key].init_lex(morph[0], morph[3], morph[4])
    fset.set_start_fs(alltrees.start_fs)
    return fset

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
        self.comment = None
        self.start_feat = False
        if isinstance(node_with_fs, basestring):
            self.node = node_with_fs
            self.top_fs = FeatStruct()
            self.bot_fs = FeatStruct()
            Tree.__init__(self, self.node, children)
        elif len(node_with_fs) == 3:
            (self.node, self.top_fs, self.bot_fs) = node_with_fs
            Tree.__init__(self, self.node, children)
        else:
            raise TypeError("%s: Expected a node value with feature"
                            "structures and child list" % type(self).__name__)
        if isinstance(children, basestring):
            raise TypeError("%s() argument 2 should be a list, not a "
                            "string" % type(self).__name__)

    def set_comment(self, comment):
        comment = comment.replace("\\\"","\"")
        self.comment = comment

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

    def __get_node(self, name_or_attr):
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
        return self.__get_node('head')

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
                    tf[global_featname(morph[0][1], False)] = FeatStruct()
                    tf[global_featname(morph[0][1], False)][key] = nf[key]
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
                        stack = []
                        for node in f:
                            for attr in f[node]:
                                if node in all_fs:
                                    all_fs[node][attr] = f[node][attr]
                                else:
                                    all_fs[node] = FeatStruct()
                                    all_fs[attr] = f[node][attr]
                        for node in f:
                            keys = f[node].keys()
                            stack = []
                            for key in keys:
                                stack.append([f[node], key])
                            while len(stack) > 0:
                                path = stack.pop()
                                feat = path[0]
                                for e in range(1, len(path)):
                                    feat = feat[path[e]]
                                first_key = feat.keys()[0]
                                if first_key[:5] == '__or_':
                                    mapping = feat[first_key].split(':')
                                    if len(mapping) == 2:
                                        m_node = mapping[0]
                                        m_attr = mapping[1][1:-1]
                                        if not m_attr in all_fs[m_node]:
                                            all_fs[m_node][m_attr]['__or_'] = ''
                                        m_key = all_fs[m_node][m_attr].keys()[0]
                                        c_feat = all_fs[node]
                                        for e in range(1, len(path)-1):
                                            c_feat = c_feat[path[e]]
                                        c_feat[path[-1]] = all_fs[m_node][m_attr]
                                    else:
                                        continue
                                else:
                                    feat_list = []
                                    for key in feat:
                                        items = copy.copy(path)
                                        items.append(key)
                                        feat_list.append(items)
                                    stack += feat_list
                        
                    self.set_all_fs(all_fs)

    def unify(self, fs):
        """
        Unify feature structure with TAG tree:
        :param: unified feature structure
        :type: FeatStruct
        """
        all_fs = self.get_all_fs()
        temp = all_fs.unify(f)
        if temp:
            all_fs = temp
        else:
            raise NameError("Unify return None")
        self.set_all_fs(all_fs)

    #def _find_value(self, fs, idn, cfs):
    #    for i in fs:
    #        if len(fs[i].keys()) > 0 and fs[i].keys()[0][0:5] == '__or_':
    #            if id(fs[i]) == idn:
    #                fs[i] = cfs
    #        else:
    #            self._find_value(fs[i], idn, cfs)

    def get_node_name(self):
        """
        Get node name of root node
        """
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
        """
        :return: leaves of this tree
        :rtype: list
        """
        leaves = []
        if len(self) == 0:
            leaves.append(self)
        for child in self:
            leaves.extend(child.leaves())
        return leaves

    def cancel_substitution(self):
        """
        Cancel substitution node of this tree
        """
        if self.attr == 'subst':
            self.attr = None
        else:
            raise TypeError("No substitution node for this tree")

    def get_substitution_node(self):
        """
        :return: substitution subtree
        :rtype: TAGTree
        """
        sub = []
        for leaf in self.leaves():
            if leaf.attr == 'subst':
                sub.append(leaf)
        return sub

    def prefix_search(self, tree_name):
        """
        Search node with prefix in the tree
        :return: subtree with tree_name as prefix
        :rtype: TAGTree
        """
        trees = []
        name = self.node.split('_')
        prefix = name[0]
        if prefix == tree_name:
            trees.append(self)
        for child in self:
            trees.extend(child.prefix_search(tree_name))
        return trees

    def delete_all_child(self):
        """
        Remove all child of this tree
        """
        result = []
        while(len(self)) > 0:
            self.pop()

    def cancel_adjunction(self):
        """
        Cancel adjunction node of this tree
        """
        if self.attr == 'foot':
            self.attr = None
        else:
            raise TypeError("No adjunction node")

    def search(self, tree_name):
        """
        Search node with name as tree_name in the tree
        :return: subtree with tree_name as root name
        :rtype: TAGTree
        """
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

    def correct_name(self):
        """
        Get a copied tree with no name collided node
        """
        tree = copy.deepcopy(self)
        tree.check_name([tree.node], 0)
        return tree       

    def check_name(self, names, count):
        """
        Check this tree for name collidec nodes 
        :return: name collided number
        :rtype: int
        """
        for child in self:
            if child.node in names:
                name = child.node.split("_")[0]
                child.node = name + '_' + str(count)
                count += 1
            names.append(child.node)
            for sub in child:
                count = child.check_name(names, count)
        return count

######################################################################
#{ Helper Functions
#{ Parse grammar file
######################################################################

def parse_tree_list(text, fs):
    tree_list = parse_brackets(text)
    t = build_tree(tree_list[0], fs)
    return t

def build_tree(tree_list, fs):
    node = parse_node(tree_list[0])
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
            sub_tree.append(build_tree(tree_list[i], fs))
        return TAGTree((node_name, top_fs, bot_fs), sub_tree, node_attr)
 
def parse_node(node_list):
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
 
def parse_brackets(text):
    text = '(' + text + ')'
    lresult = []
    ss = ''
    for c in text:
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


def find_left_bracket(fstr):
    for i in range(0, len(fstr)):
        if fstr[i] == '[':
            return i

def match_bracket(fstr):
    count = 0
    for i in range(0, len(fstr)):
        if fstr[i] == '[':
            count += 1
        elif count > 0 and fstr[i] == ']':
            count -= 1
            if count == 0:
                return i  
def global_featname(node_name, top):
    try:
        node_name[-1].decode('ascii')
    except UnicodeDecodeError:
        node_name = node_name[:-3]
    if top:
        return '.'.join([node_name, 't'])
    else:
        return '.'.join([node_name, 'b'])

def grammar_file_parse(text):
    """
    Get a TAGTreeSet from grammar files

    :param text is a string describing TAG trees, the form is defined in
    UPenn Xtag project
    """
    calist = analyze_tree_3(analyze_tree_2(analyze_tree_1(text)))
    arglist = analyze_tree_5(analyze_tree_4(calist))
    tagset = TAGTreeSet()      
    for element in arglist:
        new_tree = parse_tree_list(element[2], element[4])
        tree_name = element[0]
        new_tree.set_comment(element[5]['COMMENTS'])
        tagset[tree_name] = new_tree
    return tagset

def parse_from_files(cata, files):
    """
    Get the TAGTreeSet from the gram file. The file format
    is defined in Upenn Xtag project.
    """
    language = 'english'
    if not isinstance(files, basestring):
        raise TypeError('input should be a base string')
    tree_list = get_file_list(cata, files)
    tagset = TAGTreeSet()
    tagset[files] = TAGTreeSet()

    file_names = tree_list[0]
    directory = tree_list[1]
    for fn in file_names:
        path = os.sep.join(['xtag_grammar', language, directory, fn])
        text = nltk.data.find(path).open().read()
        tagset[files][fn] = TAGTreeSet()
        tagset[files][fn] += grammar_file_parse(text)
 
    return tagset

def draw_trees(*trees):
    """
    Display the TAGTree in a single window.
    """
    TAGTreeView(*trees).mainloop()
    return

def remove_or_tag(feat):
    """
    Remove "__or_" key in feature structure when display
    :type: FeatStruct
    """
    keys = feat.keys()
    length = len(keys)
    for key in keys:
        if key[:5] == '__or_' and length > 1:
            values = feat.values()
            value = ''
            for v in values:
                value = value + v + '/'
            feat['__value__'] = value[:-1]
            for key in keys:
                del feat[key]
            return
        elif key[:5] == '__or_':
            value = feat[key]
            feat['__value__'] = value
            del feat[key]
        elif key == '__value__':
            kvalue = feat[key]
        else:
            remove_or_tag(feat[key])

def feat_to_widget(f, c, name, **attribs):
    """
    Draw a widget of the feature structure
    :param f: feature struct
    :type: FeatStruct
    :param c: parent canvas
    :type: CanvasFrame

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
    feats = copy.deepcopy(f)
    old_name = []
    for fname in feats:
        if ord(fname[0]) > 206:
            f_chr = ord(u'\u03af') + ord(fname[0])
            uname = f_chr + fname[1:]
            feats[uname] = feats[fname]
            old_name.append(fname)
    for name in old_name:
        del feats[name]

    remove_or_tag(feats)

    fstr = feats.__repr__()
    fstr = fstr.replace('__value__=','')
    fstr = fstr.replace("'",'')
    
    d = {}
    for (attr, value) in attribs.items(): 
        d[attr] = value
    reg = None
    if 'reg' in d:
        reg = d['reg']
    s = fstr.find(name)
    l = find_left_bracket(fstr[s:])
    r = match_bracket(fstr[s:])
    match_str = fstr[s+l+1:s+r]
    result = match_str

    if s+l+1 == s+r or not match_str:
        return TextWidget(c, '[ ]', justify='center')

    if reg and len(reg) > 0:
        if 'highlight' in d:
            match_list = re.split('(\[|\,|\])', match_str)
            result = ''
            reg = reg.replace(',','')
            reg = reg.replace(']','')
            for i in match_list:
                try:    
                    result += re.compile(r'((%s\s*)+)' %
                              reg).sub(r'<h>\1<h>', i)
                except re.error, e:
                    widget = str_to_widget(match_str, c)
                    return BracketWidget(c, widget, color='black', width=1)
            widget = str_to_widget(result, c, True)
        elif 'keep' in d:
            fstr = match_feature(feats, reg, 0).__repr__()
            fstr = fstr.replace("'",'')
            fstr = fstr.replace('__value__=','')
            s = fstr.find(name)
            l = find_left_bracket(fstr[s:])
            r = match_bracket(fstr[s:])
            if l and r:
                result = fstr[s+l+1:s+r]
            else:
                return TextWidget(c, '[ ]', justify='center')
            widget = str_to_widget(result, c)
        elif 'remove' in d:
            fstr = match_feature(feats, reg, 1).__repr__()
            fstr = fstr.replace('__value__=','')
            fstr = fstr.replace("'",'')
            s = fstr.find(name)
            l = find_left_bracket(fstr[s:])
            r = match_bracket(fstr[s:])
            if l and r:
                result = fstr[s+l+1:s+r]
            else:
                result = match_str
            widget = str_to_widget(result, c)
    else:
        widget = str_to_widget(result, c)
    return BracketWidget(c, widget, color='black', width=1)

def str_to_widget(fstr, c, highlight=False):
    """
    Parse the string of feature structure into a canvas widget
    :param fstr: feat structure representation string
    :type: string
    :param c: parent canvas
    :type: CanvasFrame
    :param highlight: whether to highlight key words
    :type: bool
    """
    if fstr[:4] == '<h>,':
        fstr = fstr[4:]
    if fstr[-4:] == ']<h>':
        fstr = fstr[:-3]
    fstr = fstr.replace("<h><h>", "<h>")
    fstr = fstr.replace("<h>><h>", ">")
    fstr = fstr.replace("<h>-<h>>", "->")
    wl = []
    l = find_left_bracket(fstr)
    if l:
        r = match_bracket(fstr)
        lw = str_to_widget(fstr[l+1:r], c, highlight)
        tl = []
        strlist = fstr[:l].split(',')
        for item in strlist[:-1]:
            if len(item) > 0:
                if highlight and ('<h>' in item):
                    tl.append(BoxWidget(c, TextWidget(c, '%s' %
                              item.replace('<h>',''), justify='center'),
                              outline='white', fill='yellow'))
                else:
                    tl.append(TextWidget(c, '%s' % item, justify='center'))
        if highlight and ('<h>' in strlist[-1]):
            tw = BoxWidget(c, TextWidget(c, '%s' % 
                           strlist[-1].replace('<h>',''), justify='center'),
                           outline='white', fill='yellow')
        else:
            tw = TextWidget(c, '%s' % strlist[-1], justify='center')
        if not isinstance(lw, TextWidget):
            lw = BracketWidget(c, lw, color='black', width=1)
        tl.append(SequenceWidget(c, tw, lw, align='center'))
        wl.append(StackWidget(c, *tl))
        if r+1 != len(fstr):
            wl.append(str_to_widget(fstr[r+1:len(fstr)], c, highlight))
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
                    tl.append(BoxWidget(c, TextWidget(c, '%s' % 
                            item.replace('<h>',''), justify='center'),
                            outline='white', fill='yellow'))
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

def feat_widget(fs, allfs, canvas, name, **attribs):
    """
    Get the widget of feature structure.

    param: fs, the current feature structure to display
    param: allfs, the overall feature structure of the
    tree
    param: canvas, the canvas the feature structure 
    widget to attach
    param: name, the node name of the feature structure
    param: attribs, the attribs of the widget

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
    if fs:
        return feat_to_widget(allfs, canvas, name, **attribs)
    else:
        return TextWidget(canvas, '[ ]', justify='center')


def demo():
    gramfile = 'xtag_grammar/english/english.gram'
    cata_str = nltk.data.find(gramfile).open().read()
    cata = get_catalog(cata_str)
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    alph_tree = t['family-files']['TEnx1V.trees']['\x02Enx1V']


if __name__ == '__main__':
    install()
