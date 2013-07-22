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
from parse import *
from nltk.draw.tree import (TreeView, TreeWidget, TreeSegmentWidget)
from nltk.sem.logic import (Variable, Expression)
from nltk.draw.util import *
#from src.analyze_catalog import *

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
            self._top = parent

        frame = Frame(self._top)

        v = StringVar()
        w = Label(frame, text='Regexp:')
        self._e = Entry(frame, textvariable=v)
        self._show_fs = True
        show_fs_button = Button(frame, text="Show Features", command=self.show_fs)
        highlight_button = Button(frame, text="Highlight", command=self.highlight)
        remove_button = Button(frame, text="Remove", command=self.remove)
        keep_button = Button(frame, text="Keep", command=self.keep)
        show_fs_button.pack(side = LEFT)
        w.pack(side = LEFT)
        self._e.pack(expand=1, fill='both', side = LEFT)
        highlight_button.pack(side = RIGHT)
        keep_button.pack(side = RIGHT)
        remove_button.pack(side = RIGHT)
        

        statframe = Frame(self._top)
        notfl = Label(statframe, text='Tree Framilies:')
        self.notf = StringVar()
        self.nott = StringVar()
        tfcl = Label(statframe, textvariable=self.notf)
        nottl = Label(statframe, text='Trees:')
        tcl = Label(statframe, textvariable=self.nott)

        self.notf.set(str(self._trees.tree_family_count()))
        self.nott.set(str(self._trees.tree_count()))

        statframe.pack(side = BOTTOM, fill='both')
        notfl.pack(side = LEFT)
        tfcl.pack(side = LEFT)
        nottl.pack(side = LEFT)
        tcl.pack(side = LEFT)

        frame.pack(side = BOTTOM, fill='both')

        self._frame = Frame(self._top)
        self._frame.pack(fill='both', side = LEFT)
        
        self.cols = ('fullpath', 'type') 
        self._tagview = ttk.Treeview(self._frame, columns=self.cols, displaycolumns='',
                                     yscrollcommand=lambda f, l:autoscroll(vsb, f, l),
                                     xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
        ysb = ttk.Scrollbar(self._frame, orient=VERTICAL, command= self._tagview.yview)
        xsb = ttk.Scrollbar(self._frame, orient=HORIZONTAL, command= self._tagview.xview)
        self._tagview['yscroll'] = ysb.set
        self._tagview['xscroll'] = xsb.set
        self._tagview.bind('<<TreeviewSelect>>', self.display)
        self.populate_tree('', self._trees)
        self._tagview.configure(xscrollcommand=xsb.set,
                                yscrollcommand=ysb.set)
        ysb.pack(fill='y', side='right')
        xsb.pack(fill='x', side='bottom')

        self._tagview.heading('#0', text='Trees', anchor=W)
        self._tagview.column('#0', stretch=0, width=170)

        self._tagview.pack(expand=1, fill='both')
        self._tw = TAGTreeView((True, self._top), None)
        self._tw.pack(expand=1, fill='both', side = LEFT)

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
        for t in trees:
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
    A 
    """
    def __init__(self, trees=None):
        dict.__init__(self)
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
        return self.keys()

    def copy(self):
        return self.__class__(self)

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
        TAGTreeSetView(self).mainloop()

    def tree_count(self):
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

def parse_tree_list(txt, fs):
    tree_list = parse_brackets(txt)
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
 
def parse_brackets(txt):
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
    arglist = fifth_pass(fourth_pass(third_pass(second_pass(first_pass(txt)))))
    tagset = TAGTreeSet()       
    for element in arglist:
        new_tree = parse_tree_list(element[2], element[4])
        #print new_tree
        tree_name = element[0]
        tagset[tree_name] = new_tree
    return tagset

class TAGTree(Tree):
    
    def __init__(self, node_with_fs, children, attr=None):
        self.attr = attr
        self._lex = False
        if isinstance(node_with_fs, basestring):
            (self.node, self.top_fs, self.bot_fs) = (node_with_fs, FeatStruct(), FeatStruct())
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
        draw_trees(self)

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        else:
            clone = copy.copy(self)
            if clone._lex:
                clone._lex_fs = copy.deepcopy(self._lex_fs)
        return clone

    def get_node(self, name_or_attr):
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
        return self.get_node('head')

    def set_children(self, children):
        if isinstance(children, basestring):
            raise TypeError("%s() argument 2 should be a list, not a "
                            "string" % type(self).__name__)
        self.append(children)

    def init_lex(self, morph, fs1, fs2):
        #print fs2
        self._morph = morph
        #self._lex_fs = fs1
        self._lex_fs = []
        #lf = FeatStruct()
        for nf in fs1+fs2:
            #rint nf
            #print 111111
            for key in nf.keys():
                tf = FeatStruct()
                if key[-2:] not in ['.t', '.b']:
                    tf[_fs_name(morph[0][1], False)] = FeatStruct()
                    tf[_fs_name(morph[0][1], False)][key] = nf[key]
                    #print _fs_name(morph[0][1], False)
                else:
                    tf[key] = nf[key]
                self._lex_fs.append(tf)
        #print fs1
        #print type(fs1)
        #print fs2
        #print type(fs2)
        #self._lex_fs = fs1.unify(node_fs)
        #raise NameError('Two keys')
        #dict[_fs_name(last.node, False)] = dict[old_key]
        #del dict[old_key]
        self._lex = True
        #print self._lex_fs

    def lexicalize(self):
        morph = self._morph
        fs = self._lex_fs
        #new_fs = FeatStruct()
        heads = self.get_head()
        for head in heads:
            for m in morph:
                if head.get_node_name() == m[1]:
                    lex = TAGTree(m[0], [], 'lex')
                    head.set_children(lex)
                    all_fs = self.get_all_fs()
                    for f in fs:
                        all_fs = all_fs.unify(f)
                    self.set_all_fs(all_fs)
                    #print all_fs


    def get_node_name(self):
        return self.node

    def get_all_fs(self):
        stack = []
        all_feat = FeatStruct()
        stack.append(self)
        while len(stack) > 0:
            last = stack.pop()
            all_feat[_fs_name(last.node, True)] = last.top_fs
            all_feat[_fs_name(last.node, False)] = last.bot_fs
            for child in last:
                if isinstance(child, TAGTree):
                    stack.append(child)
        return all_feat

    def set_all_fs(self, all_fs):
        if not all_fs:
            return
        nodes = []
        nodes.append(self)
        while len(nodes) > 0:
            last = nodes.pop()
            if _fs_name(last.node, True) not in all_fs and _fs_name(last.node, False) not in all_fs:
                raise NameError('should contain feature structures')
            last.top_fs = all_fs[_fs_name(last.node, True)]
            last.bot_fs = all_fs[_fs_name(last.node, False)]
            for child in last:
                if isinstance(child, TAGTree):
                    nodes.append(child)

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
    #print trees
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
            for i in match_list:
                try:    
                    result += re.compile(r'((%s\s*)+)' % reg).sub(r'<h>\1<h>', i)
                except re.error, e:
                    print e
                    widget = parse_to_widget(match_str, c)
                    return BracketWidget(c, widget, color='black', width=1)
            widget = parse_to_widget(result, c, True)
        elif 'keep' in d:
            fstr = match_feature(feats, reg, 0).__repr__()
            fstr = fstr.replace("'",'')
            fstr = fstr.replace('__value__=','')
            print fstr
            s = fstr.find(name)
            l = find_left_bracket(fstr[s:])
            r = match_bracket(fstr[s:])
            if l and r:
                result = fstr[s+l+1:s+r]
            else:
                return TextWidget(c, '[ ]', justify='center')
            widget = parse_to_widget(result, c)
            print widget
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
            widget = parse_to_widget(result, c)
    else:
        widget = parse_to_widget(result, c)
    return BracketWidget(c, widget, color='black', width=1)

def parse_to_widget(fstr, c, highlight=False):
    wl = []
    l = find_left_bracket(fstr)
    if l:
        r = match_bracket(fstr)
        lw = parse_to_widget(fstr[l+1:r], c, highlight)
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
            wl.append(parse_to_widget(fstr[r+1:len(fstr)], c, highlight))
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

def fs_widget(fs, allfs, canvas, name, **attribs):
    if fs:
        return _fs_widget(allfs, canvas, name, **attribs)
    else:
        return TextWidget(canvas, '[ ]', justify='center')

def parse_from_files(cata, files):

    if not isinstance(files, basestring):
        raise TypeError('input should be a base string')
    tree_list = get_file_list(cata, files)
    #family_list = get_file_list(cata, 'family-files')
    tagset = TAGTreeSet()
    tagset[files] = TAGTreeSet()
    #tagset['families'] = TAGTreeSet()

    file_names = tree_list[0]
    directory = tree_list[1]
    for fn in file_names:
        path = directory + os.sep + fn
        text = open(path).read()
        tagset[files][fn] = TAGTreeSet()
        tagset[files][fn] += xtag_parser(text)

#    file_names = family_list[0]
#    directory = family_list[1]
#    for fn in file_names:
#        path = directory + os.sep + fn
#        text = open(path).read()
#        tagset['families'][fn] = TAGTreeSet()
#        tagset['families'][fn] += xtag_parser(text)
 
    return tagset

def demo():
    from util import xtag_parser
    from util import parse_from_files

    cata = get_catalog('../xtag-english-grammar/english.gram')
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.view()


if __name__ == '__main__':
    demo()
