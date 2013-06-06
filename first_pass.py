
def remove_comment(s):
    comment_start = '" :COMMENTS "'
    comment_end = '" :'
    
    while True:
        start = s.find(comment_start,0)
        
        if start == -1:
            return s
        
        end = s.find(comment_end,start + len(comment_start))

        if end == -1:
            raise "Unbalanced comment encountered"
            return None
        
        if len(s) == end + len(comment_end):
            s = s[:start]
        else:
           s = s[:start] + s[end + len(comment_end):]

    return None

def first_pass(filename):
    fp = open(filename)

    s = fp.read()

    fp.close()
    s = remove_comment(s)
    return s

def second_pass(s):
    i = 0
    last_time = 0
    stack = 0
    
    xtag_trees = []
    feature = None
    single_tree = None
    
    is_feature = True
    for i in range(0,len(s)):
        if s[i] == '(':
            stack += 1
        elif s[i] == ')':
            stack -= 1
            if stack == 0 and is_feature == True:
                feature = s[last_time:i + 1]
                last_time = i + 1
                is_feature = False
            elif stack == 0 and is_feature == False:
                single_tree = s[last_time:i + 1]
                last_time = i + 1
                is_feature = True

            if is_feature == True:
                xtag_trees.append([feature,single_tree])

    return xtag_trees

def third_pass(xtag_trees):
    for xtag_entry in xtag_trees:
        xtag_entry[0] = xtag_entry[0].splitlines()
        
        start = xtag_entry[0][0].find('"')
        end = xtag_entry[0][0].find('"',start + 1)
        xtag_entry[0][0] = xtag_entry[0][0][start + 1:end]

        xtag_features = []

        for i in xtag_entry[1:]:
            if i != '':
                xtag_features.append(i)
                
        xtag_entry[0] = xtag_features

    return xtag_trees
            
for i in third_pass(second_pass(first_pass('Ts0V.trees')))[0][0]:
    print i
