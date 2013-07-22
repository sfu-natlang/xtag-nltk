
def check_index(index):
    if index == -1:
        raise TypeError('Invalid input line.')

def get_next_pair(s,start):
    # This function will extract next pair of <<XXXX>>OOOOO from the input string
    # s with a starting index = start. The return value is a tuple (entry,value,index)
    # The 3rd value is the next un-read position, could be -1 if there is no more
    # input
    index_start = s.find('<<',start)
    if index_start == -1:
        return (None,None,-1)
    index_end = s.find('>>',index_start) 
    check_index(index_end)
    entry = s[index_start + 2:index_end]
    start = index_end + 2
    index_start = s.find('<<',start)
    if index_start == -1:
        value = s[start:]
        index_return = len(s) - 1
    else:
        value = s[start:index_start]
        index_return = index_start

    return (entry,value,index_return)

def analyze_syntax(s):
    # This function returns a dictionary, the index is exactly the <<INDEX>>
    # entry in the syntax file. Each keyword will fetch a list, the element of
    # which is just the lines with the same <<INDEX>>. Each list has four components
    # The first is called entry_list, the element of which is tuples with <<ENTRY>>
    # and <<POS>> being the 1st and 2nd element. The 2nd list is called tree_list
    # the element of which is tree name. The 3rd list is called family_list
    # the element of which is family name. The fourth list is called feature_list
    # the element of which is feature name.
    lines = s.splitlines()
    tokens = {}
    for l in lines:
        if l == '':
            continue
        start = 0
        entry_list = []
        tree_list = []
        family_list = []
        feature_list = []
        line_name = 'noname'
        while True:
            next_pair = get_next_pair(l,start)
            start = next_pair[2]
            entry = next_pair[0]
            value = next_pair[1]
            if start == -1:
                break
            elif entry == 'INDEX':
                line_name = value
            elif entry == 'ENTRY':
                entry_name = value
                next_pair = get_next_pair(l,start)
                start = next_pair[2]
                check_index(start)
                entry = next_pair[0]
                value = next_pair[1]
                if entry != 'POS':
                    raise TypeError('<<ENTRY>> must be followed by <<POS>>')
                else:
                    pos = value
                entry_list.append((entry_name,pos))
            elif entry == 'FAMILY':
                family_list = value.split()
            elif entry == 'TREES':
                tree_list = value.split()
            elif entry == 'FEATURES':
                feature_list = value.split()
            else:
                pass
                #raise TypeError('Unknown type: %s' % (entry))

        temp = (entry_list,tree_list,family_list,feature_list)
        if tokens.has_key(line_name):
            tokens[line_name].append(temp)
        else:
            tokens[line_name] = [temp]
    return tokens

#def debug(filename):
#    fp = open(filename)
#    s = fp.read()
#    fp.close()
#    print analyze_syntax(s)['Asian']
    

#if __name__ == '__main__':
#    debug('syntax-coded.flat')
    
