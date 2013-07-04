

def get_next_token(s,index,length=None):
    # state = 0: outside anything
    # state = 1: inside ""
    # state = 2: inside identifier
    # state = 3: inside comment (not for sure)
    state = 0
    start = 0
    end = 0
    # length is the length of s, just for speed up if the length can be
    # calculated outside of this function and doesn't change
    if length == None:
        l = len(s)
    else:
        l = length
        
    while True:
        if state == 0 and index >= l:
            return (None,index)
        elif state == 0 and s[index].isspace():
            index += 1
        elif state == 0 and (s[index] == '(' or s[index] == ')' or s[index] == ':'):
            return (s[index],index + 1)
        elif state == 0 and s[index] == '"':
            start = index
            state = 1
            index += 1
        elif state == 1 and s[index] == '"':
            end = index
            state = 0
            return (s[start:end + 1],index + 1)
        elif state == 0 and (s[index].isalnum() or s[index] == "'"):
            state = 2
            start = index
            index += 1
        elif state == 2 and (s[index].isspace() or s[index] == ')' or s[index] == '('):
            end = index - 1
            return (s[start:end + 1],index)
        elif state == 0 and (s[index] == ';' or s[index] == '#'):
            state = 3
            index += 1
        elif state == 3 and s[index] == '\n':
            state = 0
            index += 1
        else:
            index += 1

catalog_name = {}

def add_new_name(s,index):
    global catalog_name
    token_1 = get_next_token(s,index)
    index = token_1[1]
    token_2 = get_next_token(s,index)
    index = token_2[1]
    if catalog_name.has_key(token_1[0]):
        raise TypeError("add_new_name: Name already exist")
    if token_2[0][0] != '"' or token_2[0][-1] != '"':
        raise TypeError('add_new_name: Value must be wrapped with "')
    else:
        catalog_name[token_1[0]] = token_2[0][1:-1]
        
    return (token_2[0][1:-1],index)

def generate_string(s,index):
    global catalog_name
    token = get_next_token(s,index)
    index = token[1]
    string_value = ""
    if token[0] == "'string":
        while True:
            token = get_next_token(s,index)
            if token[0][0] == '"' and token[0][-1] == '"':
                index = token[1]
                string_value += token[0][1:-1]
            elif catalog_name.has_key(token[0]):
                index = token[1]
                string_value += catalog_name[token[0]]
            else:
                return (string_value,index)
    else:
        raise TypeError("generate_string: Don't support concatenate except \"'string\"")

def evaluate_expression(s,index):
    token = get_next_token(s,index)
    if token[0] != '(':
        raise TypeError("evaluate_expression: '(' expected.")
    index = token[1]
    token = get_next_token(s,index)
    index = token[1]
    if token[0] == 'setf':
        ret = add_new_name(s,index)
        index = ret[1]
    elif token[0] == 'concatenate':
        ret = generate_string(s,index)
        index = ret[1]
    else:
        raise TypeError("evaluate_expression: Unknown method")
    token = get_next_token(s,index)
    index = token[1]
    if token[0] != ')':
        raise TypeError("evaluate_expression: ')' expected")
    else:
        return (ret[0],index)

def parse_expression(s,index):
    values = []

    while True:
        token = get_next_token(s,index)
        
        if token[0][0] == '"' and token[0][-1] == '"':
            values.append(token[0][1:-1])
            index = token[1]
        elif token[0][0] == '(':
            token_1 = get_next_token(s,token[1])
            if token_1[0] == ':': # A nested option list (identified with '(:')
                return [("expr",values),index]
            else:
                exp_value = evaluate_expression(s,index) # index is still on '('
                values.append(exp_value[0]) # parse "(something)"
                index = exp_value[1]
        else:
            return [("expr",values),index]
        
        

        

def parse_option(s,index):
    token = get_next_token(s,index)
    if token[0] != ':':
        return (None,index)
    else:
        index = token[1]
        t = get_next_token(s,index)
        option_name = t[0]
        index = t[1]
        exp = parse_expression(s,index)
        index = exp[1]

    return [("optn",option_name,exp[0]),index]

def parse_option_set(s,index):
    token = get_next_token(s,index)
    if token[0] != '(':
        # push back the token just fetched by returning index
        return (None,index)

    options = []
    index = token[1]
    while True:
        opt = parse_option(s,index)
        index = opt[1]
        if opt[0] == None:
            opt = parse_option_set(s,index)
            index = opt[1]
            if opt[0] == None:
                break
            else:
                options.append(opt[0])
        else:
            options.append(opt[0])

    token = get_next_token(s,index)
    index = token[1]
    if token[0] != ')':
        raise TypeError("parse_option_set: ')' expected.")

    return [("opts",options),index]

def parse_language(s,index):
    token = get_next_token(s,index)
    if token[0] != '(':
        return (None,index)

    token = get_next_token(s,token[1])
    if token[0] != 'defgrammar':
        raise TypeError("parse_language: 'defgrammar' expected.")

    token = get_next_token(s,token[1])
    language_name = token[0]

    option_set = []
    index = token[1]
    while True:
        opt = parse_option_set(s,index)
        index = opt[1]
        if opt[0] == None:
            break
        else:
            option_set.append(opt[0])

    token = get_next_token(s,index)
    if token[0] != ')':
        raise TypeError("parse_language: ')' expected")
    else:
        return [("lang",language_name,option_set),token[1]]
    

def parse_catalog(s,index):
    top = []
    while True:
        lang = parse_language(s,index)
        if lang[0] == None:
            break
        else:
            top.append(lang[0])
            index = lang[1]
            
    return ("top",top)

def print_tree(node,table):
    if node[0] == "top":
        for lang in node[1]:
            print table * '    ' + "top"
            print_tree(lang,table + 1)
    elif node[0] == 'lang':
        print '    ' * table + node[1]
        for opts in node[2]:
            print_tree(opts,table + 1)
    elif node[0] == "opts":
        print '    ' * table + "opts"
        for optn in node[1]:
            print_tree(optn,table + 1)
    elif node[0] == 'optn':
        print '    ' * table + node[1]
        print_tree(node[2],table + 1)
    elif node[0] == 'expr':
        for value in node[1]:
            print '    ' * table + value
        

def debug(filename):
    fp = open(filename)
    s = fp.read()
    fp.close()

    cata = parse_catalog(s,0)

    print_tree(cata,0)
    
debug('english.gram')
