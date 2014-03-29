class Pattern:
    """
    A pattern is just a reduced version of regular expression.

    Please note that this module will not try to find the best matching, i.e.
    the longest matching. However, it does find the longest matching in each
    node. For example, in a concatenation node
    """

    def __init__(self,child_list,pattern_type=0):
        """
        Construct a new node for string recognition. The children of this node
        and the pattern type determines the language of this node.
        
        pattern_type == 0: Simple set of words (characters)
        pattern_type == 1: Concatenation
        pattern_type == 2: Disjunction
        pattern_type == 3: Star

        :param child_list: A list of nodes or a list of strings
        :type child_list: list
        """
        self.child = child_list
        self.type = pattern_type
        # This dictionary is used to dispatch different types to the proper
        # method, saving time when we get a new node to parse
        self.type_dict = {0: self.match_basic, 1: self.match_concatenation,
                          2: self.match_disjunction,
                          3: self.match_star, 4: self.match_add}
        return

    # Some static data for constructing more sophisticated languages
    # Lower case a-z
    alpha_lower = list('abcdefghijklmnopqrstuvwxyz')
    # Upper case A-Z
    alpha_upper = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    # Digits 0-9
    digit = list('0123456789')
    # Underline, may be used to recognioze a C-style identifier
    underline = list('_')
    # Alphabet a-zA-Z
    alpha = alpha_lower + alpha_upper
    # Alphabet and Digits a-zA-Z0-9
    alpha_num = alpha + digit
    # Alphabet and Digits and Underline a-zA-Z0-9_
    alpha_num_ul = alpha + digit + underline
    # Alphabet and Underline a-zA-Z_
    alpha_ul = alpha + underline
    # Space characters
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
        """
        Print out how the Pattern is structured using nodes.

        :param table: Number of spaces ('\t') preceding the text
        :type table: integer
        """
        ret = ' ' * table +  ('<Pattern Type %d>' % (self.type))
        if self.type == 0:
            ret += '\n' + ' ' * (table + 4) + str(self.child)
        else:
            for i in self.child:
                ret += '\n' + i.print_tree(table=table+4)
        return ret
    
    def __repr__(self):
        """
        Output the structure of the node.
        """
        return self.print_tree()

    def __and__(self,other):
        """
        Given two Pattern instances (the same type or different types) the
        '&' operator will return a new instance which is the concatenation
        of the language of the two nodes.

        :param other: Pattern instance that you want to do concatenation
        :type other: Pattern

        :return: The resulting instance
        :rtype: Pattern
        """
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
        """
        Return the disjunction of two nodes. In other words it is an 'OR'
        relationship.

        :param other: Pattern instance that you want to do disjunction
        :type other: Pattern

        :return: The resulting instance
        :rtype: Pattern
        """
        if self.type == 2 and other.type == 2:
            return Pattern(self.child + other.child,2)
        elif self.type == 2:
            return Pattern(self.child,2) + [other]
        elif other.type == 2:
            return Pattern(other.child,2) + [self]
        else:
            return Pattern([self,other],2)

    def star(self):
        """
        Return the star(*) of the node. This method do not need another
        argument. The resulting node can recognize 0 to any number of
        pattern repetitions of this node.
        """
        if self.type == 3:
            return self
        else:
            return Pattern([self],3)

    def add(self):
        """
        Return the add(+) of the node. The resulting node can recognize 1 to
        any number of pattern repetitions of this node.
        """
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
        """
        Match basic strings without any pattern from the input string. This
        is used for the bottommost nodes, whose children are all strings. And
        these strings are metched and the longest among them are returned.

        Please notice that the children list does not mean a concatenation of
        all these nodes, instead, it provides several choices, and we try our
        best to get the longest match and return it.

        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
        # Used to record whether there is a match and if there is the longest
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
        # If these has even been a match, then return it
        if max_length != -1:
            return (success_str,next_index + max_length)
        else:
            return (False,next_index)

    def match_concatenation(self,s,next_index=0):
        """
        Match the concatenation of all its child nodes. The child nodes can
        be a basic node (pattern_type = 0) or a complex node.

        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
        # If match fails just return this
        next_index_bak = next_index
        # This cannot be None since we need to do string concatenation
        success_str = ''
        # Iterate among all children and match them recursively. Return the
        # result if and only if all of them get matched
        for i in self.child:
            ret = i.get_match(s,next_index)
            if ret[0] == False:
                return (False,next_index_bak)
            else:
                next_index = ret[1]
                success_str += ret[0]
        return (success_str,next_index)

    def match_disjunction(self,s,next_index=0):
        """
        Match the disjunction of children nodes.

        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
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
        """
        Match the star of a node. Please notice that we also accept a non-match
        which means that this method will always return a result even if it
        fails. (According to definition a star also matches the empty string).

        Also the children nodes are treated like a type 1 (concatenation) node,
        instead of a type 2 (disjunction) node.

        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
        # Treat this as a concatenation
        self.type = 1
        success_str = ''
        # Match the node (type = 1) as long as possible
        while True:
            ret = self.get_match(s,next_index)
            # Match until there is a non-match. This can be the first one
            # or in the middle
            if ret[0] == False:
                break
            else:
                success_str += ret[0]
                next_index = ret[1]
        # Do not forget to restore the original type
        self.type = 3
        # This method always return the result, even if it recogniozes
        # the empty string
        return (success_str,next_index)

    def match_add(self,s,next_index=0):
        """
        Very similar to matching the star node, except that we need to make
        sure at least one string get matched before we return. If there is not
        even a single match then this method will return a fail instead of a
        success with an empty string.

        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
        next_index_bak = next_index
        success_str = ''
        self.type = 1
        # Do a match first
        ret = self.get_match(s,next_index)
        # Not even a single match, return fail
        if ret[0] == False:
            self.type = 4
            return (False,next_index_bak)
        else:
            next_index = ret[1]
            success_str += ret[0]
        # Then treat it like a star node.
        self.type = 3
        ret = self.get_match(s,next_index)
        # We can use this drirectly since type 3 node never fails
        success_str += ret[0]
        # Restore the type
        self.type = 4
        return (success_str,ret[1])

    def get_match(self,s,next_index=0):
        """
        A general one to match the string, regardless of the certain type.
        Use the jump table (a dictionary) in the static data area.

        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
        return self.type_dict[self.type](s,next_index)

    def parse(self,s,next_index=0):
        """
        The same as get_match(). This is an interface reserved for the Parser
        :param s: The input string
        :type s: str
        :param next_index: Current position for reading
        :type next_index: integer
        """
        return self.get_match(s,next_index)

class PatternBuilder:
    """
    Some general and useful patterns, a little bit more complex than the simple
    pattern. Essentially this is a diuctionary encapsulated in an instance.
    """
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
        """
        LL Grammar for the loop structure star(*)
        """
        def __init__(self,rhs,func=None):
            """
            :param rhs: A grammar element
            :type rhs: Grammar Element (various type)
            :param func: A function dealing with the result, the return 
            value of which will be appended to the end of the parsing result
            :type func: callable
            """
            self.rhs = rhs
            self.func = func
            return

        def __repr__(self):
            return 'LLGRammar Element: Star'
        
        def parse(self,s,next_index=0):
            """
            Parse the star by iterating through elements in rhs.

            If self.func is not None then we will first call func() to process
            the list parse_result, and then return it. If it is None then we
            will just return parse_result without any modification.

            :param s: The input string
            :type s: str
            :param next_index: Current position for reading
            :type next_index: integer

            :return: Parse result, the first element is the string or False,
            and the second element is the next_index
            :rtype: tuple(str/False,integer)
            """
            parse_result = []
            single_loop = LLGrammar('loop',[self.rhs])
            while True:
                ret = single_loop.parse(s,next_index)
                if ret[0] == False:
                    return (parse_result,next_index)
                else:
                    next_index = ret[1]
                    if self.func == None:
                        # The 'loop' label is reserved
                        parse_result += ret[0][1:]
                    else:
                        # If we have defined a function then call the func
                        # It should know the structure of the return value
                        parse_result += self.func(ret[0])
            raise ValueError('You should not have seen this. Fatal Error!!')

    class Add:
        """
        LL Grammar for the add(+) structure
        """
        def __init__(self,rhs,func=None):
            """
            Please refer to class Star
            """
            self.rhs = rhs
            self.func = func
            return
        
        def __repr__(self):
            return 'LLGrammar Element: Add'

        def parse(self,s,next_index):
            """
            Parse the add(+) structure. Nearly the same as the star(*), except
            that it requires at least 1 success parse, so if there is not even
            1 parse it will fail.

            :param s: The input string
            :type s: str
            :param next_index: Current position for reading
            :type next_index: integer

            :return: Parse result, the first element is the string or False,
            and the second element is the next_index
            :rtype: tuple(str/False,integer)
            """
            parse_result = []
            single_loop = LLGrammar('add',[self.rhs])
            # First we will ensure that there is at least 1 parse
            ret = single_loop.parse(s,next_index)
            # If there is not even 1 parse, then return fail
            if(ret[0] == False):
                return (False,next_index)
            else:
                next_index = ret[1]
                if self.func == None:
                    parse_result += ret[0][1:]
                else:
                    parse_result += self.func(ret[0])
                
            # Then this is the same as a start
            while True:
                ret = single_loop.parse(s,next_index)
                if ret[0] == False:
                    return (parse_result,next_index)
                else:
                    next_index = ret[1]
                    # If we have defined the function then just process the result
                    # using this function
                    if self.func == None:
                        parse_result += ret[0][1:]
                    else:
                        parse_result += self.func(ret[0])
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
            """
            :param start_symbol: The symbol that will cause the stack to
            push
            :type start_symbol: A grammar element
            :param end_symbol: The symbol that will cause the stack to pop
            :type end_symbol: A grammar element
            """
            self.start_symbol = start_symbol
            self.end_symbol = end_symbol
            return

        def __repr__(self):
            return 'LLGrammar Element: Nested'

        def parse(self,s,next_index):
            """
            Get the nested structure using a stack (for simplicity we only
            use the stack pointer instead of a real stack).

            :param s: The input string
            :type s: str
            :param next_index: Current position for reading
            :type next_index: integer

            :return: Parse result, the first element is the string or False,
            and the second element is the next_index
            :rtype: tuple(str/False,integer)
            """
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
                
    # Very important. Used to extract tokens from an input stream
    space_pattern = Pattern(Pattern.space).star()

    @staticmethod
    def print_tree(parse_result,table=0):
        """
        Print the internal structure of a grammar element

        :param table: The number of spaces ('\t') before the text
        :type table: integer
        """
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
    Reads in Korean Grammar (github version) and converts it to a recognizable
    format for grammar reader.

    Initialize the instance using the string read from the source syntax file
    (the whole file), then call the parse() method. After that the member
    self.features is a dictionary containing the templates, and self.entries
    is a list containing all lines in the target syntax file.

    If you want to dump these data to the disk, then you can call the dump()
    method after calling parse(). The default file names for the target syntax
    and template files are 'syntax_coded.flat' and 'templates.lex'
    respectively.
    """

    def __init__(self,s):
        """
        Initialize the reader using a string read from the Korean Grammar's
        syntax file.

        :param s: The string read from the source syntax file
        :type s: str
        """
        self.s = s
        self.features = {}
        self.entries = []
        return

    def parse_line(self,line):
        """
        Converts each line in the original syntax file into several lines in
        the target format, and also record these in-line feature structures
        in a dictionary, which can be further used to generate the template.

        This method also modifies the dictionary self.features
        
        :param line: A non-empty line from the source syntax file
        :type line: str
        :return: A list of lines in the target syntax file
        :rtype: list(str)
        """
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
        """
        Split the input string into lines, and parse them seperately using
        parse_line method. Also after calling parse_line it will collect the
        lines generated by that method for future dump.
        """
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
        """
        Print out all features (templates) in the form acceptable by grammar
        reader on stdout. This is also called a template.
        """
        for i in self.features.keys():
            print '#' + i + '\t' + self.features[i] + ' !'

    def dump(self,
             syntax_file='syntax_coded.flat',template_file='template.lex'):
        """
        Given the file name of the syntax file and the template file, dump
        these two files to the disk.

        :param syntax_file: File name for the syntax file
        :type syntax_file: str
        :param template_file: File name for the template file
        :type template_file: str
        """
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
print a.parsed_trees
#print fr.features
"""
