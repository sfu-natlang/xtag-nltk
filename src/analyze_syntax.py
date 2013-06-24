
def check_index(index):
    if index == -1:
        raise TypeError('Invalid input line.')

# This function will extract next pair of <<XXXX>>OOOOO from the input string
# s with a starting index = start. The return value is a tuple (entry,value,index)
# The 3rd value is the next un-read position, could be -1 if there is no more
# input
def get_next_pair(s,start):
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
        index_start = len(s) - 1
    else:
        value = s[start:index_start]

    return (entry,value,index_start)

def analyze_syntax(s):
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
        name = 'noname'
        while True:
            next_pair = get_next_pair(s,start)
            start = next_pair[2]
            if start == -1:
                break
            entry = next_pair[0]
            value = next_pair[1]
            if entry == 'INDEX':
                name = value[:]
            elif entry == 'ENTRY':
                entry_name = value
                next_pair = get_next_pair(s,start)
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
                raise TypeError('Unknown type: %s' % (entry))

        temp = (entry_list,tree_list,family_list,feature_list)
        print name
        if tokens.has_key(name):
            tokens[name].append(temp)
        else:
            tokens[name] = [temp]
    return tokens


def debug(filename):
    fp = open(filename)
    s = fp.read()
    fp.close()
    print analyze_syntax(s)['Asian']
    

if __name__ == '__main__':
    debug('syntax-coded-test.flat')
    
