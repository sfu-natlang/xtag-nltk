from nltk.tree import *
from nltk.featstruct import FeatStruct
from Tkinter import *
import ttk
import os
import re
import copy
from nltk.util import in_idle
from nltk.tree import Tree
from math import sqrt, ceil
from nltk.draw.tree import (TreeView, TreeWidget, TreeSegmentWidget)
from nltk.sem.logic import (Variable, Expression)
from nltk.draw.util import *

class TAGTreeSegmentWidget(TreeSegmentWidget):

    def __init__(self, canvas, node, subtrees, top_fs, bot_fs, **attribs):
        TreeSegmentWidget.__init__(self, canvas, node, 
                                      subtrees, **attribs)
        self._top_fs = top_fs
        self._bot_fs = bot_fs

    def top_fs(self):
        return self._top_fs

    def bot_fs(self):
        return self._bot_fs        

class TAGTreeWidget(TreeWidget):
    
    def __init__(self, canvas, t, fs, show, make_node=TextWidget,
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
        #print self._attr
        #print self._show_fs
        #print type(t)
        #print t
        #print fs
        #CanvasWidget.__init__(self, canvas, **attribs)    

    def _make_expanded_tree(self, canvas, t, key):
        make_node = self._make_node
        make_leaf = self._make_leaf

        if isinstance(t, TAGTree):
            #t.node = t.node + 'rrr'
            node_name = self._set_node_name(t)
            #node_name = t.node\
            bold = ('helvetica', -24, 'bold')
            #helv = ('helvetica', -22)
            node = make_node(canvas, node_name, font=bold,
                                color='#004080')
            #print t
            #print 1111111111111
            #print node
            
            #top_str = 'Top Feature Structure'
            #bot_str = '\n\nBottom Feature Structure'
            #print self.show
            if self._show_fs:
                top_fs = fs_widget(t.top_fs, self._all_fs, canvas, _fs_name(node_name, True), **self._attr)
                bot_fs = fs_widget(t.bot_fs, self._all_fs, canvas, _fs_name(node_name, False), **self._attr)
        #print top_fs
        #print bot_fs
            #top_text = TextWidget(canvas, top_str, justify='center')
            #bot_text = TextWidget(canvas, bot_str, justify='center')
        #print type(top_fs)
                cstack = StackWidget(canvas, top_fs, bot_fs, align='left')
            

                node =  SequenceWidget(canvas, node, cstack, align='top')
                #print node


            self._nodes.append(node)
            children = t
            subtrees = [self._make_expanded_tree(canvas, children[i], key+(i,))
                        for i in range(len(children))]
            #treeseg = TreeSegmentWidget(canvas, node, subtrees,
            #                            color=self._line_color,
            #                            width=self._line_width)
            #print subtrees
            top_name = _fs_name(t.node, True)
            bot_name = _fs_name(t.node, False)
            #print self._all_fs
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
            #print treeseg.top_fs()
            #print 22222222
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

    def toggle_collapsed(self, treeseg):
        self.show_fs(treeseg)

    def show_fs(self, treeseg):
        
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
        #print top_fs
        #print bot_fs
        top_text = TextWidget(c, top_str, justify='center')
        bot_text = TextWidget(c, bot_str, justify='center')
        #print type(top_fs)
        cstack = StackWidget(c, top_text, top_fs, bot_text, bot_fs, align='center')
        #zz = BracketWidget(c, ct2, color='black', width=3)
        cf.add_widget(cstack, 30, 30)
        cf.pack(expand=1, fill='both')
        self._fsw.mainloop()

    def set_parent_window(self, parent):
        self._top = parent

class TAGTreeView(TreeView):
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
        
        #print trees.node
        #print type(trees)
        self._trees = trees
        for i in self._widgets:
            self._cframe.destroy_widget(i)
        self._size = IntVar(self._top)
        self._size.set(12)
        #print -self._size.get()
        bold = ('helvetica', -self._size.get(), 'bold')
        helv = ('helvetica', -self._size.get())

        self._width = int(ceil(sqrt(len(trees))))
        self._widgets = []
        for i in range(len(trees)):
            if isinstance(trees[i], TAGTree):
                fs = trees[i].get_all_fs()
            else:
                fs = None
            #print trees[i]
            #print fs
            widget = TAGTreeWidget(self._cframe.canvas(), trees[i], fs, show,#, node_font=bold,
                                leaf_color='#008040', #node_color='#004080',
                                roof_color='#004040', roof_fill='white',
                                line_color='#004040',#)#, draggable=1,
                                leaf_font=helv, **attribs)
            #widget['xspace'] = xspace
            widget['yspace'] = 70
            widget['xspace'] = 70
            widget.set_parent_window(self._top)
            #widget.show_fs(show)
            #widget.bind_click_trees(widget.toggle_collapsed)
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)
        self._init_menubar()

    def pack(self, cnf={}, **kw):
        self._cframe.pack(cnf, **kw)

    #def keep_fs()

class TAGTreeSetView(object):

    def __init__(self, tagtrees, parent=None):

        self._trees = tagtrees

        if parent is None:
            self._top = Tk()
            self._top.title('NLTK')
            self._top.bind('<Control-p>', lambda e: self.print_to_file())
            self._top.bind('<Control-x>', self.destroy)
            self._top.bind('<Control-q>', self.destroy)
        else:
            self._top = parent

        frame = Frame(self._top)

        v = StringVar()
        w = Label(frame, text='Regexp:')
        self._e = Entry(frame, textvariable=v)
        self._show_fs = True
        show_fs_button = Button(frame, text="Show Features", command=self.show_fs)
        highlight_button = Button(frame, text="Highlight", command=self.okbutton)
        remove_button = Button(frame, text="Remove", command=self.okbutton)
        keep_button = Button(frame, text="Keep", command=self.keep)
        show_fs_button.pack(side = LEFT)
        w.pack(side = LEFT)
        self._e.pack(expand=1, fill='both', side = LEFT)
        highlight_button.pack(side = RIGHT)
        keep_button.pack(side = RIGHT)
        remove_button.pack(side = RIGHT)
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
        #xsb.pack(side=LEFT)

        self._tagview.heading('#0', text='Trees', anchor=W)
        self._tagview.column('#0', stretch=0, width=170)

        self._tagview.pack(expand=1, fill='both')
        #self.tree.pack()
        self._tw = TAGTreeView((True, self._top), None)
        self._tw.pack(expand=1, fill='both', side = LEFT)

    def pack(self):
        self._tagview.pack(expand=1, fill='both')
        self._frame.pack(fill='both', side = LEFT)
        self._tw.pack(expand=1, fill='both', side = LEFT)

    def tran_greek(self, ascii):
        #print ascii
        i = ord(u'\u03af') + ord(ascii)
        #print ord(ascii)
        return unichr(i)

    def display(self, event=None):
        node = self._tagview.focus()
        #print node
        path = self._tagview.set(node, "fullpath").split('/')
        #print path
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        #print type(tree)
        if not isinstance(tree, type(self._trees)):
            #print self._show_fs
            #if self._lex:
            #    tree.lexicalize(self.morph, self.fs):
            #    self._tw.redraw(self._show_fs, tree)
            #else:
            if tree._lex:
                lextree = copy.deepcopy(tree)
                lextree.lexicalize()
                self._tw.redraw(self._show_fs, lextree)
            else:
                self._tw.redraw(self._show_fs, tree)

    def populate_tree(self, parent, trees):
        # use current directory as root node         
        # insert current directory at top of tree
        # 'values' = column values: fullpath, type, size
        #            if a column value is omitted, assumed empty
        if not trees:
            return
        for t in trees:
            node = parent
            parent_path = self._tagview.set(parent, "fullpath")
            path = parent_path + '/' + t
            if ord(t[0]) < 10:
                f_chr = self.tran_greek(t[0])
            else:
                f_chr = t[0]
            if isinstance(trees[t], type(trees)):
                node = self._tagview.insert(parent, END, text=f_chr+t[1:],
                                      values=[path, 'directory'])
                self.populate_tree(node, trees[t])
            else:
                self._tagview.insert(parent, END, text=f_chr+t[1:],
                                      values=[path, 'file'])
        #print self._tagview.get_children()
    
    def clear(self):
        x = self._tagview.get_children()
        #print x
        for item in x: 
            self._tagview.delete(item)
        self._trees = TAGTreeSet()

    def update(self, trees):
        self._trees = trees
        self.populate_tree('', trees)

        #print 'after remove', self._tagview.get_children()


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
        self._show_fs = not self._show_fs
        self.display()
        return

    def keep(self):
        #self._show_fs = self._e.get()
        node = self._tagview.focus()
        #print node
        path = self._tagview.set(node, "fullpath").split('/')
        #print path
        tree = self._trees
        for subpath in path[1:]:
            if subpath in tree:
                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)
        #print type(tree)
        if not isinstance(tree, type(self._trees)):
            #print self._show_fs
            #self._tw.
            self._tw.redraw(self._show_fs, tree, keep=True, reg=self._e.get())
        return

    def okbutton(self):
        return
 
# first_pass(s) will split the options and trees into a list, the first and second
# element of which is None, the third being the tree, and the fourth being
# the list of oprion, which will be processed in later phases
class TAGTreeSet(dict):

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

    def count(self):
        return len(self)

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
    #@classmethod
    #def parse(cls, txt):
    #    return xtag_parser(txt)

def parse_from_files(file_names, directory=None):
    tagset = TAGTreeSet()
    if isinstance(file_names, basestring):
        raise TypeError('input should be a list of file names')
    for fn in file_names:
        text = open(fn).read()
        if directory:
            if len(fn) <= len(directory):
                raise NameError('directory or file names not correct')
            directory = directory.replace(os.sep, '')
            fn = fn[len(directory)+1:]
            #print fn
        indices = fn.split(os.sep)
        #print indices
        d = tagset
        for indice in indices[:-1]:
            if indice not in d:
                d[indice] = TAGTreeSet()
            d = d[indice]

        d[indices[-1]] = TAGTreeSet()
        d[indices[-1]] += xtag_parser(text) 
    return tagset

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
        features = {}
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

    def lexicalize(self):
        morph = self._morph
        fs = self._lex_fs
        print morph
        #new_fs = FeatStruct()
        heads = self.get_head()
        for head in heads:
            for m in morph:
                if head.get_node_name() == m[1]:
                    print m[1]
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

    #for i in feats.__repr__():
        
        #print reentrances
        # If this is the first time we've seen a reentrant structure,
        # then assign it a unique identifier.
    if reentrances[id(feats)]:
        assert not reentrance_ids.has_key(id(feats))
        reentrance_ids[id(feats)] = repr(len(reentrance_ids)+1)

    namelist = [i for i, v in feats.items() if i == name]
    if len(namelist) > 1:
        raise TypeError('Error')


        # sorting note: keys are unique strings, so we'll never fall
        # through to comparing values.
    for (fname, fval) in sorted(feats.items()):
        display = getattr(fname, 'display', None)
            #print fname, fval
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
                    #tw = TextWidget(c, prefix, justify='center')
                    #segments.append(tw)
        elif display == 'slash' and not suffix:
            if isinstance(fval, Variable):
                suffix = '/%s' % fval.name
            else:
                suffix = '/%r' % fval
                #tw = TextWidget(c, suffix, justify='center')
                #segments.append(tw)
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
                #bw = BracketWidget(c, fval_repr, color='black', width=3)
            sw = SequenceWidget(c, tw, fval_repr, align='center')
            segments.append(sw)
            #print 'loopend ', prefix, segments
        # If it's reentrant, then add on an identifier tag.
    if reentrances[id(feats)]:
        prefix = '(%s)%s' % (reentrance_ids[id(feats)], prefix)

        #print 'end ', prefix, segments, suffix
        #return
    cstack = StackWidget(c, *segments)
    widgets = []
    if prefix:
        pw = TextWidget(c, prefix, justify='center')
        widgets.append(pw)
        #for i in segments:
        #    print i
    bw = BracketWidget(c, cstack, color='black', width=1)
    widgets.append(bw)
    if suffix: 
        sw = TextWidget(c, suffix, justify='center')
        widgets.append(sw)
    return SequenceWidget(c, *widgets, align='center')

def _fs_widget(feats, c, name, **attribs):
    '''
    for i in range(0,120):
        BracketWidget(c, TextWidget(c, 'None', justify='center'), color='black', width=1)
    return BracketWidget(c, TextWidget(c, 'None', justify='center'), color='black', width=1)
    '''
    #if not name:
    #    return _all_widget(feats, reentrances, reentrance_ids, c, name=None)
    fstr = feats.__repr__()
    #print fstr
    d = {}
    for (attr, value) in attribs.items(): 
        d[attr] = value
    reg = None
    if 'reg' in d:
        reg = d['reg']
    #print fstr
    #for i in fstr.split(','):
    #    print i
    #print name
    s = fstr.find(name)
    l = find_left_bracket(fstr[s:])
    r = match_bracket(fstr[s:])
    match_str = fstr[s+l+1:s+r]
    if reg:
        bcount = 1
        rcount = 1
        #print reg
        p = re.compile(reg)
        iterator = p.finditer(match_str)
        match_str = '[' + match_str + ']'
        for match in iterator:
            (start, end) = match.span()

        '''
        for match in iterator:
            (start, end) = match.span()
            print start, end
            for i in range(0, start+1):
                if match_str[start-i] == '[':
                    lindex = start-i
                elif match_str[start-i] == ']':
                    break
            for i in range(end, len(match_str)):
                if match_str[i] == ']':
                    rcount -= 1
                elif match_str[i] == '[':
                    rcount += 1
                if match_str[i] == ']' and rcount == 0:
                    rindex = i
            print lindex
            print rindex
            print 111111
        '''
       #print "matchObj.group(1) : ", matchObj.group(1)
       #print "matchObj.group(2) : ", matchObj.group(2)
    #print fstr[s+l+1:s+r]
    #print fstr[s+l+1:s+r]
    #a= parse_to_widget(fstr[s+l+1:s+r], c)
    if s+l+1 == s+r:
        return BracketWidget(c, TextWidget(c, '', justify='center'), color='black', width=1)
    widget = parse_to_widget(fstr[s+l+1:s+r], c)
    #if not isinstance(widget, TextWidget):
    return BracketWidget(c, widget, color='black', width=1)
    #else:
    #    return widget
    #'''

def parse_to_widget(fstr, c, highlight=None):
    wl = []
    l = find_left_bracket(fstr)
    if l:
        r = match_bracket(fstr)
        lw = parse_to_widget(fstr[l+1:r], c)
        tl = []
        for item in fstr[:l].split(',')[:-1]:
            if len(item) > 0:
                tl.append(TextWidget(c, '%s' % item, justify='center'))
        tw = TextWidget(c, '%s' % fstr[:l].split(',')[-1], justify='center')
        if not isinstance(lw, TextWidget):
            #print 111111111
            lw = BracketWidget(c, lw, color='black', width=1)
        tl.append(SequenceWidget(c, tw, lw, align='center'))
        wl.append(StackWidget(c, *tl))
        if r+1 != len(fstr):
            wl.append(parse_to_widget(fstr[r+1:len(fstr)], c))
    else:
        tl = []
        textl = fstr.split(',')
        textl = filter(None, textl)
        if highlight:
            for item in textl:
                item = item.replace('__value__=','')
                item = item.replace("'",'')
                hightext = item.split('<h>')
                if len(hightext) > 1:
                    tl.append(BoxWidget(c, TextWidget(c, '%s' % item, justify='center'), outline='white', color='yellow'))
                else:
                    tl.append(TextWidget(c, '%s' % item, justify='center'))
            return StackWidget(c, *tl)
        if len(textl) == 1 and '__value__=' in textl[0]:
            item = textl[0]
            item = item.replace('__value__=','')
            item = item.replace("'",'')
            return TextWidget(c, '[ %s ]' % item, justify='center')
        elif len(textl) == 1:
            item = textl[0]
            item = item.replace("'",'')
            return TextWidget(c, '%s' % textl[0], justify='center')
        else:
            for item in textl:
                item = item.replace('__value__=','')
                item = item.replace("'",'')
                #item.split('<h>')
                tl.append(TextWidget(c, '%s' % item, justify='center'))
            return StackWidget(c, *tl)
    cstack = StackWidget(c, *wl)
    return cstack


def find_left_bracket(fstr):
    for i in range(0, len(fstr)):
        if fstr[i] == '[':
            return i
    return None

def match_bracket(fstr):
    count = 0
    for i in range(0, len(fstr)):
        if fstr[i] == '[':
            count += 1
        elif count > 0 and fstr[i] == ']':
            count -= 1
            if count == 0:
                return i
    raise None

       

def fs_widget(fs, allfs, canvas, name, **attribs):
    if fs:
        return _fs_widget(allfs, canvas, name, **attribs)
        #text = TextWidget(canvas, 'None', justify='center')
        #return BracketWidget(canvas, text, color='black', width=1)
    else:
        #text = TextWidget(canvas, '', justify='center')
        #return BracketWidget(canvas, text, color='black', width=1)
        return TextWidget(canvas, '[ ]', justify='center')

def demo():
    from util import xtag_parser
    from util import parse_from_files
    #files = os.listdir('grammar')
    #print files
    files = ['grammar/advs-adjs.trees']#, 'auxs.trees', 'comparatives.trees', 'conjunctions.trees', 'determiners.trees', 'lex.trees', 'modifiers.trees', 'neg.trees', 'prepositions.trees', 'punct.trees', 'TEnx1V.trees']    #files = [os.path.join('grammar',i) for i in files]
    #files = ['grammar/advs-adjs.trees']
    t = parse_from_files(files, 'grammar')
    #for i in t:
        #for j in t[i]:
            #print 'TREE!!!', t[i][j]
            #print t[i][j].get_all_fs()
            #for k in t[i][j]:
            #    print k
            #for k in t[i][j].get_node('foot'):
            #    k.node = 'changed'
            #print t[i][j]
    t.view()


if __name__ == '__main__':
    demo()
