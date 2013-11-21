def jump_over_space(s,next_index):
    while s[next_index].isspace():
        next_index += 1
    return next_index

def print_context(s,next_index):
    print s[next_index - 20:next_index + 20]

def is_valid_string_component(ch):
    if ch.isalnum() or ch == '-' or ch == '_' or ch == '?':
        return True
    else:
        return False

def get_alnum_string(s,next_index):
    next_index = jump_over_space(s,next_index)
    start_index = next_index
    while is_valid_string_component(s[next_index]): # Only accept alpha and num as the string
        next_index += 1
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
