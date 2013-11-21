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
    alpha = alpha_lower + alpha_upper
    alpha_num = alpha + digit
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

class PatternBuilder:
    built_in = {
        'comma': Pattern([',']),
        'qmark': Pattern(['?']),
        'dash': Pattern(['-']),
        'alpha': Pattern(Pattern.alpha),
        'alnum': Pattern(Pattern.alpha_num),
        'digit': Pattern(Pattern.digit),
        'space': Pattern(Pattern.space),
        'lbracket': Pattern(['(']),
        'rbracket': Pattern([')']),
        'colon': Pattern([':']),
        'squot': Pattern(["'"]),
        'dquot': Pattern(['"']),
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
            raise ValueError('You should have seen this. Fatal Error!!')
    
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
            
    def __init__(self,lhs,rhs):
        # The name of this node. Will be returned in the parsing tree
        self.lhs = lhs
        # RHS is a list of lists. Each element in the nested list is either a
        # Pattern of LLGrammar
        self.rhs = rhs

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
                elif isinstance(j,LLGrammar.Star):
                    ret = j.parse(s,next_index)
                    # It always succeed
                    next_index = ret[1]
                    # Because Star() will return a list of objects
                    parse_result += ret[0]
                else:
                    raise TypeError('Unknown element in the LLGramar')
            # If we did not use a break and the loop terminates
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
    tree_options = LLGrammar('opt',[[LLGrammar.Star([opt_name,opt_value])]])
    tree = LLGrammar('tree',[[pb['lbracket'],tree_name,
                              tree_options,pb['rbracket']]])

fp = open('auxs.trees')
s = fp.read()
ret = TreeReader.tree.parse(s)
print ret
LLGrammar.print_tree(ret[0])
