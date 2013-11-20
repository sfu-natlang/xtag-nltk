
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
            if i not in new_list:
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
            print ret[0]
                
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
            return (False,next_index_bak)
        else:
            next_index = ret[1]
            success_str += ret[0]
        self.type = 3
        ret = self.get_match(s,next_index)
        success_str += ret[0]
        return (success_str,ret[1])

    def get_match(self,s,next_index=0):
        return self.type_dict[self.type](s,next_index)


def jump_over_space(s,next_index):
    """
    From a given position in a string, return the position of the next
    character which is not a space. If there is no such a character in the end
    then return False.

    :param s: A string
    :type s: str
    :param next_index: The position in the string
    :type index: int
    :return: The next index which is not a space, or a False if no such char
    :rtype: int/False
    """
    try:
        while s[next_index].isspace():
            next_index += 1
    except IndexError:
        return False
    else:
        return next_index

def check_symbol(s,next_index,symbol):
    """
    Check whether we have got a defined symbol in the grammar. Return False if
    not, or return the next_index after this symbol.

    :param s: The string need to be checked
    :type s: str
    :param next_index: Index on the string
    :type next_index: integer
    :param symbol: The symbol to be checked against
    :type symbol: str
    """
    try:
        next_index = jump_over_space(s,next_index)
        if s[next_index:next_index + len(symbol)] == symbol:
            return next_index + len(symbol) # We must ignore the symbol
    except IndexError:
        return False
    else:
        return False

def print_context(s,next_index):
    """
    Used to print out the context in debugging.

    :param s: The string we are parsing
    :type s: str
    :param next_index: The index of the position
    :type next_index: int
    """
    print s[next_index - 20:next_index + 20]

def is_valid_string_component(ch):
    """
    Determine if a character is a vaild character in a string. We define valid
    as if the character is any alnum or '-' or '_' or '?'. Used in multiple
    functions, don't change this.

    :param ch: The character you want to check
    :type ch: str (of length 1)
    """
    if ch.isalnum() or ch == '-' or ch == '_' or ch == '?':
        return True
    else:
        return False

def get_alnum_string(s,next_index):
    """
    Extract a string only contains alphabets and digits. If it EOF is met
    then the next_index in the tuple returned will be False
    """
    next_index = jump_over_space(s,next_index)
    start_index = next_index
    try:
        while is_valid_string_component(s[next_index]): # Only accept alpha and num as the string
            next_index += 1
    except IndexError:
        return (s[start_index:],False)
    else:
        return (s[start_index:next_index],next_index)

def get_tree_name(s,next_index):
    next_index = jump_over_space(s,next_index)
    if not s[next_index] == '(':
        print_context(s,next_index)
        raise ValueError('A tree option must start with a (')
    next_index += 1
    next_index = jump_over_space(s,next_index)
    if not s[next_index] == '"':
        raise ValueError('A tree name must start with a "')
    next_index += 1
    name_start = next_index
    while s[next_index] != '"':
        next_index += 1
    name_str = s[name_start:next_index] # From the first character to the one before '"'
    return (name_str,next_index + 1)

def get_colon_string(s,next_index):
    next_index = jump_over_space(s,next_index)
    if s[next_index] != ':':
        return (None,next_index)
    next_index += 1
    (option_name,next_index) = get_alnum_string(s,next_index)
    if option_name == '':
        return (None,next_index)
    else:
        return (option_name,next_index)

def get_quote_string(s,next_index):
    next_index = jump_over_space(s,next_index)
    if s[next_index] != '"':
        return (None,next_index)
    next_index += 1
    start_index = next_index
    while True:
        ch = s[next_index]
        if ch == '\\' and s[next_index + 1] == '"':
            next_index += 2
        elif ch == '"':
            break
        else:
            next_index += 1
    return (s[start_index:next_index],next_index + 1)

def get_tree_option_name(s,next_index):
    return get_colon_string(s,next_index)

def get_tree_option_value(s,next_index):
    next_index = jump_over_space(s,next_index)
    if s[next_index] == ':':
        return get_colon_string(s,next_index)
    elif s[next_index] == '(':
        next_index += 1
        option_values = []
        while True:
            (val,next_index) = get_colon_string(s,next_index)
            if val == None:
                break
            else:
                option_values.append(val)
        if s[next_index] == ')':
            return (option_values,next_index + 1)
        else:
            raise ValueError('Expect a ")"')
    elif s[next_index] == '"':
        return get_quote_string(s,next_index)
    else:
        return get_alnum_string(s,next_index)

def analyze_tree_options(s,next_index):
    overall_option = {}
    (tree_name,next_index) = get_tree_name(s,next_index)
    while True:
        (option_name,next_index) = get_tree_option_name(s,next_index)
        if option_name == None:
            break
        else:
            (option_value,next_index) = get_tree_option_value(s,next_index)
            if not overall_option.has_key(option_name):
                overall_option[option_name] = option_value
            else:
                raise KeyError("The option %s already exists" % (option_name))
    return ((tree_name,overall_option),next_index)

def analyze_tree_structure(s,next_index):
    stack = 0
    while True:
        if s[next_index] == '(':
            stack += 1
        elif s[next_index] == ')':
            stack -= 1
            if stack == 0:
                return (None,next_index + 1)
        next_index += 1

        

def analyze_tree_complex(s,next_index):
    (opts,next_index) = analyze_tree_options(s,next_index)
    if s[next_index] != ')':
        raise ValueError('Expect a ), context = %s' % (s[next_index - 5:next_index + 5]))
    next_index += 1
    (struct,next_index) = analyze_tree_structure(s,next_index)
    return ((opts,struct),next_index)

def analyze_tree_file(s):
    # trees: A set of trees, list
    # trees[i][0]: tree options, tuple
    # trees[i][0][0]: tree name, str
    # trees[i][0][1]: tree options, dict
    # trees[i][1]: tree structure, str
    # trees[i][0][1]['COMMENTS']: comment, str
    # trees[i][0][1]['UNIFICATION-EQUATIONS']: feature structure, str
    trees = []
    next_index = 0
    while True:
        try:
            (tree,next_index) = analyze_tree_complex(s,next_index)
        except IndexError:
            break

        trees.append(tree)
    return trees

def debug_jump_over_space():
    print jump_over_space('   \t\r\n\n\n   wangziqi2013',0)

def debug_get_tree_name():
    print get_tree_name('   (   "wangziqi2013"   ',0)

def debug_get_alnum_string():
    print get_alnum_string('    "wangziqi2013)',0)

def debug_get_tree_option_name():
    print get_tree_option_name('      :this_is_option ',2)

def debug_get_tree_option_value():
    print get_tree_option_value('"sdsdsdwerrf sdf ssfd sdfs f" ',0)

def debug_analyze_tree_file():
    fp = open('advs-adjs.trees')
    print analyze_tree_file(fp.read())[0][0][1]['COMMENTS']
    fp.close()

if __name__ == '__main__':
    #debug_jump_over_space()
    #debug_get_tree_name()
    #debug_get_alnum_string()
    #debug_get_tree_option_name()
    #debug_get_tree_option_value().
    debug_analyze_tree_file()
