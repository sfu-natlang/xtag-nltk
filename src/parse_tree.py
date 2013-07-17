
from next_token import get_next_token
from sys import *

def parse_tree(s,index):
    top = ["top",[]]
    current = 0   # used to track the top most value in the stack
    stack = [top]
    while True:
        token = get_next_token(s,index)
        index = token[1]
        if token[0] == None:
            break
        elif token[0] == '(':
            new_node = [None,[]]
            stack[current][1].append(new_node)
            stack.append(new_node)
            current += 1
        elif token[0] == ')':
            stack.pop()
            current -= 1
        elif stack[current][0] == None:
            stack[current][0] = token[0]
        else:
            stack[current][1].append([token[0],[]])
    if current != 0:
        raise TypeError("parse_tree: Brackets do not match.")

    return top

def print_tree(sub_tree,table):
    stdout.write('    ' * table)
    print sub_tree[0]
    if len(sub_tree[1]) == 0:
        return
    else:
        for t in sub_tree[1]:
            print_tree(t,table + 1)
    return

top = parse_tree('(S (NP (D the) (N dog)) (VP (V chased) (NP (D the) (N cat))))',0)
print top
print_tree(top,0)
