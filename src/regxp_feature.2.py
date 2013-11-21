
class RunOutOfChar:
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return self.value

class ParsingError:
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return self.value

class InvalidChar:
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return self.value

class Tokenizer:
    def __init__(self,s,next_index=0):
        self.s = s
        self.next_index = next_index
        self.text_len = len(s)
        return

class SimpleParser:

    def __init__(self,s,next_index=0):
        """
        The init function will bind a string and current position to a
        parser instance. So the user need not to maintain the state of
        parser.
        """
        self.s = s
        self.next_index = next_index
        self.text_len = len(s)
        return

    def has_finished(self):
        """
        Test whether the stream has come to an end using the current state
        variables, including next_index and text_len

        :return: If there is no more content in the input stream then return
        False, or return True
        :rtype: bool
        """
        if self.text_len <= self.next_index:
            return True
        else:
            return False

    def range_legal(self):
        """
        Test whether the current pointer is in the stream or just 1 character
        beyond the max index. This is useful when we are testing characters,
        if the length of the string is exactly the reamining length of the
        stream, then the next read will cause an IndexError.

        :return: False if next_index is beyond the range of [0,text_len]
        :rtype: bool
        """
        # This means next_index can be one character more than the string
        # _ _ _ _ _ _ . . . . .
        #             | --> Also OK
        if self.text_len < self.next_index:
            return False
        else:
            return True
        

    def try_next_string(self,length=1):
        """
        Test whether we can extract another string of length given in the
        parameter from the text. If we can then just return the string, or
        raise an error.

        This function will not jump over spaces.

        :param length: The length of the string that will be tested
        :type length: int
        :return: A substrong of length 'length' if the total length permits
        """
        start_index = self.next_index
        self.next_index += length
        if self.range_legal():
            return self.s[start_index,self.next_index]
        else:
            raise RunOutOfChar('We have no more characters')

    def next_available_string(self,max_length = -1):
        """
        Return a string of the maximum possible length
        """
    
    def jump_over_space(self):
        """
        Jump over s sequence of space character, including space '\x20',
        new line '\xA' and horizontal table.

        If an IndexError is thrown which means we have read all available
        characters then the flag 'has_finished' is set to True
        """
        try:
            while self.s[self.next_index].isspace():
                self.next_index += 1
        except IndexError:
            # Do not raise exception, since we do not know whether the work
            # has been done or not. Check this flag outside this method
            has_finished = True
            return
        else:
            return

    def check_symbol(self,symbol):
        """
        Check whether we have got a specified string in the grammar. Spaces will
        be automatically jumped through.
        """
        self.next_index = self.jump_over_space()
        # This function can not finish here, so we raise an error
        if self.has_finished == True:
            raise RunOutOfChar('Unexpected EOF before checking symbol')
        
        try:
            len_symbol = len(symbol)
            if s[self.next_index:self.next_index + len_symbol] == symbol:
                self.next_index += len_symbol # We must ignore the symbol
                return
            else:
                raise ParsingError('Checking symbol fail')
        except IndexError:
            raise RunOurOfChar('Unexpected EOF when checking symbol')

    def is_valid_string_component(self):
        """
        Read a character from the input stream, and if the char is a-z A-z 0-9
        or '-', '_', '?' then we will return without invoking any error.
        """
        if has_finished == True:
            raise RunOutOfChar('Unexpected EOF before fetching character')
        if ch.isalnum() or ch == '-' or ch == '_' or ch == '?':
            return
        else:
            return
        
def get_alnum_string(s,next_index):
    """
    Extract a string only contains alphabets and digits. If it EOF is met
    then the next_index in the tuple returned will be False
    """
    next_index = jump_over_space(s,next_index)
    start_index = next_index
    
    if next_index == False:
        return False

    try:
        # Only accept alpha and num as the string
        while is_valid_string_component(s[next_index]): 
            next_index += 1
    except IndexError:
        return (s[start_index:],False)
    else:
        return (s[start_index:next_index],next_index)

def get_tree_name(s,next_index):
    next_index = jump_over_space(s,next_index)

    if next_index == False:
        return (False,False)
    
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
    # From the first character to the one before '"'
    name_str = s[name_start:next_index] 
    return (name_str,next_index + 1)

def get_colon_string(s,next_index):
    next_index = jump_over_space(s,next_index)

    if next_index == False:
        return False
    
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

    if next_index == False:
        return (False,False)

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

    if next_index == False:
        return (False,False)
    
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
    print 'tree options....'
    overall_option = {}
    (tree_name,next_index) = get_tree_name(s,next_index)

    if tree_name == False and next_index == False:
        return (False,False)
    
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
        try:
            if s[next_index] == '(':
                stack += 1
            elif s[next_index] == ')':
                stack -= 1
                if stack == 0:
                    # Not an actual structure
                    return (None,next_index + 1)
        except IndexError:
            return (False,False)
        else:
            next_index += 1

        

def analyze_tree_complex(s,next_index):
    print 'tree_complex...'
    (opts,next_index) = analyze_tree_options(s,next_index)

    if opts == False and next_index == False:
        return (False,False)
    
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
    print 'Analyzing trees...'
    trees = []
    next_index = 0
    while True:
        (tree,next_index) = analyze_tree_complex(s,next_index)
        if tree == False and next_index == False:
            break
        else:
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
