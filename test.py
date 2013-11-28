class Pattern:
    """
    A pattern is just a reduced version of regular expression.

    Please note that this module will not try to find the best matching, i.e.
    the longest matching. However, it does find the longest matching in each
    node. For example, in a concatenation node
    """

    def __init__(self,child_list,pattern_type=0):
        """
        type == 0: Simple set of words (characters)
        type == 1: Concatenation
        type == 2: Disjunction
        type == 3: Star
        """
        self.child = child_list
        self.type = pattern_type
        self.type_dict = {0: self.match_basic, 1: self.match_concatenation,
                          2: self.match_disjunction,
                          3: self.match_star, 4: self.match_add}
        return

    alpha_lower = list('abcdefghijklmnopqrstuvwxyz')
    alpha_upper = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    digit = list('0123456789')
    underline = list('_')
    alpha = alpha_lower + alpha_upper
    alpha_num = alpha + digit
    alpha_num_ul = alpha + digit + underline
    alpha_ul = alpha + underline
    space = list(' \n\t')
    
    def __add__(self, rhs):
        """
        For two Pattern instances, addition makes sense only if they are of
        the same type. In this case the result is a new Pattern whose type
        is the type of the two operands, and the child is just a merge
        of the two operands.

        For one Pattern instance and another object, if the object is a list
        then just merge the list will child, and there is no check whether
        the resuting Pattern is a valid one. When the object is a string
        then just add the string into the child. Also we do not check about
        the validity of the resuting Pattern.
        """
        new_list = self.child[:] # Do a full copy
        if isinstance(rhs,Pattern):
            if self.type != rhs.type:
                raise TypeError(
                    'Only Patterns of the same type can do addition')
            add_list = rhs.child
        elif isinstance(rhs,list):
            add_list = rhs
        elif isinstance(rhs,str):
            add_list = [rhs]

        for i in add_list:
            #if i not in new_list:
            new_list.append(i)

        return Pattern(new_list,self.type)

    def print_tree(self,table=0):
        ret = ' ' * table +  ('<Pattern Type %d>' % (self.type))
        if self.type == 0:
            ret += '\n' + ' ' * (table + 4) + str(self.child)
        else:
            for i in self.child:
                ret += '\n' + i.print_tree(table=table+4)
        return ret
    
    def __repr__(self):
        return self.print_tree()

    def __and__(self,other):
        if self.type == 1 and other.type == 1:
            return Pattern(self.child + other.child,1)
        elif self.type == 1:
            # The new pattern is to add rhs into the child list of lhs
            return Pattern(self.child,1) + [other]
        elif other.type == 1:
            return Pattern(other.child,1) + [self]
        else:
            return Pattern([self,other],1)

    def __or__(self,other):
        if self.type == 2 and other.type == 2:
            return Pattern(self.child + other.child,2)
        elif self.type == 2:
            return Pattern(self.child,2) + [other]
        elif other.type == 2:
            return Pattern(other.child,2) + [self]
        else:
            return Pattern([self,other],2)

    def star(self):
        if self.type == 3:
            return self
        else:
            return Pattern([self],3)

    def add(self):
        if self.type == 4:
            return self
        else:
            return Pattern([self],4)
        
    @staticmethod
    def match_eof(s,next_index=0):
        """
        This method detects whether the string has come to an end. This is
        necessary sometimes, since both 'Not Match' and 'EOF' will cause
        the get_match() to return a False in the first component. It is hard
        to distinguish these two. So we provide this additional method to
        detect such a situation.

        :return: A tuple, the first component is True if next_index is out of
        bound, and False if it is not. The second component is always the
        parameter next_index, not changed.
        :rtype: tuple(bool,int)
        """
        try:
            s[next_index]
        except IndexError:
            return (True,next_index)
        else:
            return (False,next_index)

    def match_basic(self,s,next_index=0):
        max_length = -1
        success_str = None
        for i in self.child:
            # Only accept string
            if not isinstance(i,str):
                raise ValueError('Child in a type 0 pattern must be string')
            length = len(i)
            try:
                test_str = s[next_index:next_index + length]
            except IndexError:
                continue
            # If we find a match then just record it
            if test_str == i and max_length < length:
                max_length = length
                success_str = i
        if max_length != -1:
            return (success_str,next_index + max_length)
        else:
            return (False,next_index)

    def match_concatenation(self,s,next_index=0):
        # If match fails just return this
        next_index_bak = next_index
        success_str = ''
        for i in self.child:
            ret = i.get_match(s,next_index)
            if ret[0] == False:
                return (False,next_index_bak)
            else:
                next_index = ret[1]
                success_str += ret[0]
        return (success_str,next_index)

    def match_disjunction(self,s,next_index=0):
        max_length = -1
        success_str = None
        for i in self.child:
            
            ret = i.get_match(s,next_index)
            if ret[0] != False and len(ret[0]) > max_length:
                max_length = len(ret[0])
                success_str = ret[0]
                
        if max_length != -1:
            return (success_str,next_index + max_length)
        else:
            return (False,next_index)
            

    def match_star(self,s,next_index=0):
        self.type = 1
        success_str = ''
        while True:
            ret = self.get_match(s,next_index)
            if ret[0] == False:
                break
            else:
                success_str += ret[0]
                next_index = ret[1]
                    
        self.type = 3
        return (success_str,next_index)

    def match_add(self,s,next_index=0):
        next_index_bak = next_index
        success_str = ''
        self.type = 1
        ret = self.get_match(s,next_index)
        if ret[0] == False:
            self.type = 4
            return (False,next_index_bak)
        else:
            next_index = ret[1]
            success_str += ret[0]
        self.type = 3
        ret = self.get_match(s,next_index)
        success_str += ret[0]
        self.type = 4
        return (success_str,ret[1])

    def get_match(self,s,next_index=0):
        return self.type_dict[self.type](s,next_index)

    def parse(self,s,next_index=0):
        return self.get_match(s,next_index)

class PatternBuilder:
    built_in = {
        'point': Pattern(['.']),
        'comma': Pattern([',']),
        'qmark': Pattern(['?']),
        'dash': Pattern(['-']),
        'alpha': Pattern(Pattern.alpha),
        'alnum': Pattern(Pattern.alpha_num),
        'digit': Pattern(Pattern.digit),
        'space': Pattern(Pattern.space),
        'lbracket': Pattern(['(']),
        'rbracket': Pattern([')']),
        'clbracket': Pattern(['{']),
        'crbracket': Pattern(['}']),
        'semicolon': Pattern([';']),
        'colon': Pattern([':']),
        'slash': Pattern(['/']),
        'bslash': Pattern(['\\']),
        'squot': Pattern(["'"]),
        'dquot': Pattern(['"']),
        'lt': Pattern(['<']),
        'gt': Pattern(['>']),
        'eq': Pattern(['=']),
        'ident': (Pattern(Pattern.alpha_ul) &
                  Pattern(Pattern.alpha_num_ul).star()),
        'char': Pattern(list('~!@#$%^&*()_+=-][{};:/?.>,<\\`')
                       + Pattern.alpha_num + Pattern.space) + [r'\'',r"\""],
    }

    def __getitem__(self,key):
        return self.built_in[key]

    def __init__(self):
        self.built_in['sqstring'] = (self.built_in['squot'] &
                                     (self.built_in['char']
                                      + Pattern('"')).star() &
                                     self.built_in['squot'])
        self.built_in['dqstring'] = (self.built_in['dquot'] &
                                     (self.built_in['char']
                                      + Pattern("'")).star() &
                                     self.built_in['dquot'])
        self.built_in['qstring'] = (self.built_in['sqstring'] |
                                    self.built_in['dqstring'])
        self.built_in['string'] = ( self.built_in['alnum'] +
                                   Pattern(list('?_-')) ).add()

class LLGrammar:
    """
    LL Grammar for the parser
    """

    class Star:
        def __init__(self,rhs):
            self.rhs = rhs
            return

        def __repr__(self):
            return 'LLGRammar Element: Star'
        
        def parse(self,s,next_index):
            parse_result = []
            single_loop = LLGrammar('loop',[self.rhs])
            while True:
                ret = single_loop.parse(s,next_index)
                if ret[0] == False:
                    return (parse_result,next_index)
                else:
                    next_index = ret[1]
                    parse_result += ret[0][1:]
            raise ValueError('You should not have seen this. Fatal Error!!')

    class Add:
        def __init__(self,rhs):
            self.rhs = rhs
            return
        
        def __repr__(self):
            return 'LLGrammar Element: Add'

        def parse(self,s,next_index):
            parse_result = []
            single_loop = LLGrammar('add',[self.rhs])
            ret = single_loop.parse(s,next_index)
            if ret[0] == False:
                return (parse_result,next_index)
            else:
                next_index = ret[1]
                parse_result += ret[0][1:]
                return (parse_result,next_index)
            raise ValueError('You should not have seen this. Fatal Error!!')

    class Nested:
        """
        This is used to parse a nested structure, usually a very long expression
        like string which is nested with multiple levels of brackets or quote
        marks. For example:

        ( S ( NP I ) ( VP ( V  like ) ( NP ( N fish ) ) ) )

        Basically the parser will not try to recognize the internal structure
        of the nested structure. It only uses a stack to count the balance
        of the string. And once the stack is balanced for the first time it will
        stop and return the result as well as the next_index.
        """
        def __init__(self,start_symbol,end_symbol):
            self.start_symbol = start_symbol
            self.end_symbol = end_symbol
            return

        def __repr__(self):
            return 'LLGrammar Element: Nested'

        def parse(self,s,next_index):
            next_index_bak = next_index
            start_pattern = self.start_symbol
            end_pattern = self.end_symbol
            stack = 0
            while True:
                ret = start_pattern.parse(s,next_index)
                if ret[0] != False:
                    stack += 1
                    next_index = ret[1]
                else:
                    ret = end_pattern.parse(s,next_index)
                    if ret[0] != False:
                        stack -= 1
                        next_index = ret[1]
                        # If stack balanced then accept
                        if stack == 0:
                            return (s[next_index_bak:next_index],next_index)
                    else:
                        if Pattern.match_eof(s,next_index)[0] == True:
                            # EOF encountered and stack is balanced
                            if stack == 0:
                                return (s[next_index_bak:next_index],
                                        next_index)
                            # Stack not balanced, just go back and reject
                            else:
                                return (False,next_index_bak)
                        # If we cannot find both a start symbol and end symbol
                        # then just step one character further and check again
                        else:
                            next_index += 1
            raise ValueError('You shuold not have seen this.')
                
    
    space_pattern = Pattern(Pattern.space).star()

    @staticmethod
    def print_tree(parse_result,table=0):
        line = table * ' '
        if isinstance(parse_result,str):
            line += parse_result
            print line
            return
        line += parse_result[0]
        print line
        for i in parse_result[1:]:
            LLGrammar.print_tree(i,table + 4)
            
    def __init__(self,lhs,rhs,funcs=None):
        # The name of this node. Will be returned in the parsing tree
        self.lhs = lhs
        # RHS is a list of lists. Each element in the nested list is either a
        # Pattern of LLGrammar
        self.rhs = rhs
        self.funcs = None

    @staticmethod
    # Not finish yet
    def make_grammar(grammar,grammar_dict={}):
        lines = grammar.splitlines()
        grammar_dict = {}
        for i in lines:
            assign = i.find('->')
            if assign == -1:
                raise ValueError("Each line must have a -> mark")
            lhs = i[:assign]
            rhs = i[assign + 2:]
            rhs = rhs.split()
            lhs = lhs.strip()
            if grammar_dict.has_key(lhs):
                grammar_dict[lhs] = []
            #grammar_dict[lhs]
        
    
    def parse(self,s,next_index=0):
        next_index_bak = next_index
        parse_result = [self.lhs]
        for i in self.rhs:
            for j in i:
                ret = LLGrammar.space_pattern.get_match(s,next_index)
                # It must succeed so we just use the new next_index without
                # testing 
                next_index = ret[1]
                if isinstance(j,Pattern):
                    ret = j.get_match(s,next_index)
                    if ret[0] != False:
                        next_index = ret[1]
                        parse_result.append(ret[0])
                    else:
                        # Cannot match one token in the grammar, just backtrack
                        # to the initial state
                        parse_result = [self.lhs]
                        next_index = next_index_bak
                        # Try next grammar, index also reset
                        break
                elif isinstance(j,LLGrammar):
                    ret = j.parse(s,next_index)
                    if ret[0] != False:
                        next_index = ret[1]
                        parse_result.append(ret[0])
                    else:
                        parse_result = [self.lhs]
                        next_index = next_index_bak
                        break
                elif (isinstance(j,LLGrammar.Star) or
                      isinstance(j,LLGrammar.Add)):
                    ret = j.parse(s,next_index)
                    # It always succeed
                    next_index = ret[1]
                    # Because Star() will return a list of objects
                    parse_result += ret[0]
                elif isinstance(j,LLGrammar.Nested):
                    ret = j.parse(s,next_index)
                    if ret[0] != False:
                        next_index = ret[1]
                        # The nested will be represented as a tuple
                        parse_result.append( ('nested',ret[0]) )
                    else:
                        parse_result = [self.lhs]
                        next_index = next_index_bak
                        break
                else:
                    raise TypeError('Unknown element in the LLGramar')
            # If we didn't jump out using break, which means the loop
            # terminates normally, then we know that all grammars has been
            # parsed
            else:
                return (parse_result,next_index)
        # If we cannot find a possible rule then exit with a False
        return (False,next_index_bak)


comma = Pattern([','])
lbracket = Pattern(['('])
rbracket = Pattern([')'])
var = Pattern(Pattern.alpha_num)
loop = LLGrammar.Star([comma,var])
root = LLGrammar('root',[[lbracket,var,loop,rbracket]])
#print root.parse('(a,b,c,d)')[0]

"""
lbracket = Pattern(['('])
rbracket = Pattern([')'])
mul = Pattern(['*','/'])
plus = Pattern(['+','-'])
var = Pattern(Pattern.alpha_lower + Pattern.alpha_upper).add()
digit = Pattern(Pattern.digit).add()
token = LLGrammar('var',[[var],[digit]])
e1 = LLGrammar('e1',[[token]])
e2 = LLGrammar('e2',[[e1]])
e2.rhs.append([e1,mul,e2])
e3 = LLGrammar('e3',[[e2]])
e3.rhs.append([e2,plus,e3])
e1.rhs.append([lbracket,e3,rbracket])
e3.rhs.reverse()
e2.rhs.reverse()
#e1.rhs.reverse()
print ( e3.parse('aa + bD * cE * ( d + e * (cCCSDFD - 123456) )')[0])
"""
class TreeReader:
    """
    Parser built for xtag trees. The grammar is like this:

    forest -> tree*
    tree -> '(' tree_name tree_options ')'
    tree_options -> (opt_name opt_value)*
    opt_name -> :string
    opt_value -> string | '(' opt_name* ')' | "\"" string "\"" | opt_name
    string -> ...(See PatternBuilder)
    
    """
    pb = PatternBuilder()
    tree_name = LLGrammar('tree_name',[[pb['qstring']]])
    opt_name = LLGrammar('opt_name',[[pb['colon'],pb['string']]])
    opt_value = LLGrammar('opt_value',
                          [
                              [ pb['string'] ],
                              [ pb['lbracket'],LLGrammar.Star([opt_name]),pb['rbracket'] ],
                              [ pb['qstring'] ],
                              [ opt_name ]
                          ]
                         )
    tree_options = LLGrammar('opts',[[LLGrammar.Star([opt_name,opt_value])]])
    tree = LLGrammar('tree',[[pb['lbracket'],tree_name,
                              tree_options,pb['rbracket']
                              ,LLGrammar.Nested(pb['lbracket'],pb['rbracket'])]])
    forest = LLGrammar('forest',[[LLGrammar.Star([tree])]])

    def __init__(self,s):
        self.s = s.strip()
    
    def parse(self,next_index=0):
        length = len(self.s)
        ret = TreeReader.forest.parse(self.s,next_index)
        if ret[1] != length:
            raise ValueError('The file is not parsed completely')
        else:
            self.parsed_trees = ret[0]
        return

    def make_dict(self):
        self.tree_dict = {}
        for i in self.parsed_trees[1:]:
            if not self.tree_dict.has_key(i[2][1][1:-1]):
                self.tree_dict[i[2][1][1:-1]] = {}
                tree = self.tree_dict[i[2][1][1:-1]]
                for j in range(0,len(i[3][1:])):
                    opt = i[3][j]
                    val = i[3][j + 1]
                    j += 1
                    if len(val) == 2:
                        tree[opt[2]] = val[1]

    def get_feature(self,tree_name):
        return self.tree_dict[tree_name]['UNIFICATION-EQUATIONS']

    def get_comment(self,tree_name):
        return self.tree_dict[tree_name]['COMMENTS']

    def get_names(self):
        return self.tree_dict.keys()

class FeatureReader:
    """
    This class is used to parse feature structures.

    root -> entry*
    entry -> lhs '=' rhs
    rhs -> lhs
    rhs -> string
    lhs -> ident '.' ident ':' '<' ident* '>' |
           ident ':' '<' ident* '>'
    """
    pb = PatternBuilder()
    rhs_pattern = pb['alnum'] + Pattern(list('-_+<>'))
    rhs_separator = Pattern(['/'])
    lhs_pattern = pb['alnum'] + Pattern(list('-_'))
    lhs = LLGrammar('lhs',[ [pb['ident'],pb['point'],pb['ident'],pb['colon'],
                       pb['lt'], LLGrammar.Star([lhs_pattern.add()]),
                       pb['gt']],
                      [pb['ident'],pb['colon'],
                       pb['lt'], LLGrammar.Star([lhs_pattern.add()]),
                       pb['gt']]
                    ])
    rhs = LLGrammar('rhs',[ [
                                lhs
                            ],
                            [
                                rhs_pattern.add(),
                                LLGrammar.Star([rhs_separator,
                                                rhs_pattern.add()])
                            ]
                          ]
                    )
    entry = LLGrammar('entry',[[ lhs,pb['eq'],rhs ]])
    root = LLGrammar('root',[[LLGrammar.Star([entry])]])

    def __init__(self,s):
        self.s = s.strip()
    def parse(self):
        ret = self.root.parse(self.s)
        if ret[1] != len(self.s):
            raise ValueError('Features not parsed completely')
        self.parsed_features = ret[0]
        return
    def make_list(self):
        self.features = []
        for i in self.parsed_features[1:]:
            lhs = i[1][1:]
            rhs = i[3][1:]
            path = []
            for j in lhs:
                if j != '<' and j != '>' and j != '.' and j != ':':
                    path.append(j)
                    
            value = []
            for k in rhs:
                if isinstance(k,list):
                    for m in k:
                        if m != '<' and m != '>' and m != '.' and m != ':':
                            value.append(m)
                    break
                else:
                    if k != '/':
                        value.append(k)
            else:
                value = tuple(value)
                
            self.features.append({'path': path, 'value': value})
    

class KoreanSyntaxReader:
    """
    pb = PatternBuilder()
    index = pb['bslash'] & pb['alnum'] & pb['bslash']
    pos = pb['alnum']
    tree_name = pb['alnum'] + Pattern(list('\x02\x03'))\
    comment_string = (pb['char'] + Pattern(list(' \t\r\v'))).star()
    feature_entry = 
    tree_entry = LLGrammar([[tree_name,LLGrammar.Add([])]])
`   """

    def __init__(self,s):
        self.s = s
        self.features = {}
        self.entries = []

    def parse_line(self,line):
        if line[0] != '\\':
            raise ValueError('A line must start with a back slash')
        next_bslash = line.find('\\',1)
        if next_bslash == -1:
            raise ValueError('Another back slash expected after the first one')
        index = line[1:next_bslash].strip()
        comma = line.find(',',next_bslash)
        if comma == -1:
            raise ValueError('Comma expected after the index')
        colon = line.find(':',comma)
        if colon == -1:
            raise ValueError('Colon expected after the POS')
        pos = line[comma + 1:colon].strip()
        period = line.find('.',colon)
        if period == -1:
            raise ValueError('Period expected after feature')
        comment_index = line.find(';;',period + 1)
        if comment_index == -1:
            comment_text = ''
            trees = line[colon + 1:].strip()[:-1]
        else:
            comment_text = line[comment_index + 2:].strip()
            trees = line[colon + 1:comment_index].strip()[:-1]

        ret = []

        in_feature = False
        trees_list = []
        last_index = 0
        for i in range(0,len(trees)):
            if trees[i] == ',' and in_feature == False:
                trees_list.append(trees[last_index:i].strip())
                last_index = i + 1
            elif trees[i] == '{':
                in_feature = True
            elif trees[i] == '}':
                in_feature = False
        trees_list.append(trees[last_index:].strip())
                
        for i in trees_list:
            i = i.strip()
            fs = i.find('{')
            if fs == -1 and (i[0] == '\x02' or i[0] == '\x03'):
                ret.append('<<INDEX>>%s<<POS>>%s<<TREES>>%s' %
                           (index,pos,i))
            elif fs == -1:
                ret.append('<<INDEX>>%s<<POS>>%s<<FAMILY>>%s' %
                            (index,pos,i))
            else:
                fs_end_index = i.find('}',fs + 1)
                if fs_end_index == -1:
                    raise ValueError('} Expected on %s' % (index))
                tree_name = i[:fs]
                fs_index = index + '_' + tree_name
                fs_content = i[fs + 1:fs_end_index]
                self.features[fs_index] = fs_content
                if i[0] == '\x02' or i[0] == '\x03':
                    ret.append('<<INDEX>>%s<<POS>>%s<<TREES>>%s<<FEATURES>>%s' %
                               (index,pos,tree_name,fs_index))
                else:
                    ret.append('<<INDEX>>%s<<POS>>%s<<FAMILY>>%s<<FEATURES>>%s' %
                               (index,pos,tree_name,fs_index))
        return ret
                

    def parse(self):
        lines = self.s.splitlines()
        for i in lines:
            i = i.strip()
            if i == '':
                continue
            else:
                ret = self.parse_line(i)
                self.entries += ret
        return

    def print_feature(self):
        for i in self.features.keys():
            print '#' + i + '\t' + self.features[i] + ' !'

    def dump(self,syntax_file,template_file):
        tf = open(template_file,'w')
        for i in self.features.keys():
            tf.write('#' + i + '\t' + self.features[i] + ' !\r\n')
        tf.close()

        sf = open(syntax_file,'w')
        for i in self.entries:
            sf.write(i + '\r\n')
        sf.close()
        return

fp = open('lexicon.syntax')
s = fp.read()
a = KoreanSyntaxReader(s)
a.parse()
a.dump('syntax_coded.flat','templates.lex')
    
"""
fp = open('Tnx0VAN1Pnx2.trees')
s = fp.read().strip()
a = TreeReader(s)
a.parse()
#print ret
#LLGrammar.print_tree(a.parsed_trees)
a.make_dict()
#for i in a.get_names():
#    print a.get_comment(i)
#print a.tree_dict['Xnx0Vs1']['UNIFICATION-EQUATIONS']
for i in a.parsed_trees[1:]:
    for j in i[3][1:]:
        #print j[2]
        pass
c = a.get_feature('nx0VAN1Pnx2-PRO')
fr = FeatureReader(c[1:-1])
fr.parse()
fr.make_list()
print fr.features
"""
