
def bracket_matching(tree_str):
    stack = [] # First find all matches of brackets
    paren_pair = {}
    
    i = 0
    
    for ch in tree_str:
        if ch == '(':
            stack.append(i)
        elif ch == ')':
            paren_pair[stack[-1]] = i

        i += 1

    return paren_pair

def parse_tree(tree_str,paren_pair,start,end):
    while paren_pair[start] < end:
        
