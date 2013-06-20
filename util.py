from nltk.tree import *
from nltk.featstruct import FeatStruct
from Tkinter import *
import ttk
import os
from nltk.util import in_idle
#from TAGTree import TAGTreeSet
from nltk.tree import Tree
from math import sqrt, ceil
from nltk.draw.tree import (TreeView, TreeWidget, TreeSegmentWidget)
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
    
    def __init__(self, canvas, t, make_node=TextWidget,
                 make_leaf=TextWidget, **attribs):
        TreeWidget.__init__(self, canvas, t, make_node,
                            make_leaf, **attribs)
        #CanvasWidget.__init__(self, canvas, **attribs)    

    def _make_expanded_tree(self, canvas, t, key):
        make_node = self._make_node
        make_leaf = self._make_leaf

        if isinstance(t, Tree):
            #t.node = t.node + 'rrr'
            node_name = self._set_node_name(t)
            #node_name = t.node
            node = make_node(canvas, node_name, **self._nodeattribs)
            self._nodes.append(node)
            children = t
            subtrees = [self._make_expanded_tree(canvas, children[i], key+(i,))
                        for i in range(len(children))]
            #treeseg = TreeSegmentWidget(canvas, node, subtrees,
            #                            color=self._line_color,
            #                            width=self._line_width)
            
            treeseg = TAGTreeSegmentWidget(canvas, node, subtrees, 
                                        t.top_fs, t.bot_fs,
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
        else:
            raise TypeError("%s: Expected an attribute with value"
                            "substp, head or foot ")

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
        self._fsw.title('Feature Structure')
        self._fsw.bind('<Control-p>', lambda e: self.print_to_file())
        self._fsw.bind('<Control-x>', self.destroy)
        self._fsw.bind('<Control-q>', self.destroy)

        fs = 'Top Feature Structure\n' + str(treeseg.top_fs()) + '\n\n'
        fs += 'Bottom Feature Structure\n' + str(treeseg.bot_fs())

        cf = CanvasFrame(self._fsw, closeenough=10, width=400, height=300)
        c = cf.canvas()
        ct2 = TextWidget(c, fs, draggable=1, justify='center')
        space = SpaceWidget(c, 0, 30)
        cstack = StackWidget(c, ct2, align='center')
        cs = SequenceWidget(c, cstack)
        zz = BracketWidget(c, cs, color='green4', width=3)
        cf.add_widget(zz, 30, 30)
        cf.pack()
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
        self.redraw(trees)

    def redraw(self, *trees):

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
            widget = TAGTreeWidget(self._cframe.canvas(), trees[i], node_font=bold,
                                leaf_color='#008040', node_color='#004080',
                                roof_color='#004040', roof_fill='white',
                                line_color='#004040', draggable=1,
                                leaf_font=helv)
            widget.set_parent_window(self._top)
            widget.bind_click_trees(widget.toggle_collapsed)
            self._widgets.append(widget)
            self._cframe.add_widget(widget, 0, 0)

        self._layout()
        self._cframe.pack(expand=1, fill='both', side = LEFT)
        self._init_menubar()

    def pack(self, cnf={}, **kw):
        self._cframe.pack(cnf, **kw)

class TAGTreeSetView(TreeView):

    def __init__(self, tagtrees):

        self._trees = tagtrees

        self._top = Tk()
        self._top.title('NLTK')
        self._top.bind('<Control-x>', self.destroy)
        self._top.bind('<Control-q>', self.destroy)

        frame = Frame(self._top)
        frame.pack(expand=1, fill='both', side = LEFT)
        
        self.cols = ('fullpath', 'type') 
        self._tagview = ttk.Treeview(frame, columns=self.cols, displaycolumns='',
                                     yscrollcommand=lambda f, l:autoscroll(vsb, f, l),
                                     xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
        ysb = ttk.Scrollbar(frame, orient=VERTICAL, command= self._tagview.yview)
        xsb = ttk.Scrollbar(frame, orient=HORIZONTAL, command= self._tagview.xview)
        self._tagview['yscroll'] = ysb.set
        self._tagview['xscroll'] = xsb.set
        self._tagview.bind('<Double-Button-1>', self.display)
        self.populate_tree('', self._trees)
        self._tagview.configure(xscrollcommand=xsb.set,
                                yscrollcommand=ysb.set)
        ysb.pack(fill='y', side='right')
        xsb.pack(fill='x', side='bottom')
        #xsb.pack(side=LEFT)

        self._tagview.heading('#0', text='Trees', anchor=W)
        self._tagview.column('#0', stretch=0, width=170)

        self._tagview.pack(expand=1, fill='both', side = LEFT)
        #self.tree.pack()
        self._tw = TAGTreeView((True, self._top), None)
        self._tw.pack(expand=1, fill='both', side = LEFT)

    def tran_greek(self, ascii):
        i = ord(u'\u03af') + ord(ascii)
        return unichr(i)

    def display(self, event):
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
            self._tw.redraw(tree)

    def populate_tree(self, parent, trees):
        # use current directory as root node         
        # insert current directory at top of tree
        # 'values' = column values: fullpath, type, size
        #            if a column value is omitted, assumed empty
        for t in trees:
            node = parent
            parent_path = self._tagview.set(parent, "fullpath")
            path = parent_path + '/' + t
            if isinstance(trees[t], type(trees)):
                node = self._tagview.insert(parent, END, text=t,
                                      values=[path, 'directory'])
                self.populate_tree(node, trees[t])
            else:
                if ord(t[0]) < 10:
                    f_chr = self.tran_greek(t[0])
                else:
                    f_chr = t[0]
                self._tagview.insert(parent, END, text=f_chr+t[1:],
                                      values=[path, 'file'])

 
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

def parse_from_files(file_names):
    tagset = TAGTreeSet()
    if isinstance(file_names, basestring):
        raise TypeError('input should be a list of file names')
    for fn in file_names:
        text = open(fn).read()
        tagset[fn] = TAGTreeSet()
        tagset[fn] += xtag_parser(text)
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
    top_fs = None
    bot_fs = None
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
    
    def __init__(self, node_with_fs, children=None, attr=None):
        self.attr = attr
        if isinstance(node_with_fs, basestring):
            (self.node, self.top_fs, self.bot_fs) = (node_with_fs, None, None)
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

def draw_trees(*trees):
    print trees
    TAGTreeView((False,None),*trees).mainloop()
    return

def demo():
    from util import xtag_parser
    from util import parse_from_files
    #files = os.listdir('grammar')
    #print files
    files = ['Tnx0VN1.trees', 'lex.trees']
    #files = ['advs-adjs.trees', 'auxs.trees', 'comparatives.trees', 'conjunctions.trees', 'determiners.trees', 'lex.trees', 'modifiers.trees', 'neg.trees', 'prepositions.trees', 'punct.trees', 'TEnx1V.trees']    #files = [os.path.join('grammar',i) for i in files]
    t = parse_from_files(files)
    t.view()

if __name__ == '__main__':
    demo()
