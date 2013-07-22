
from nltk.featstruct import FeatStruct

# first_pass(s) will split the options and trees into a list, the first and second
# element of which is None, the third being the tree, and the fourth being
# the list of oprion, which will be processed in later phases
def first_pass(s):
    """
    first_pass() -> list

    Given the raw string read from a grammar document, this
    function will split the options and TAG trees into a list.  
    """
    i = 0
    last_time = 0    # To record the position since the latest ')'
    stack = 0  # We use a simple stack to match brackets

    # Store final result, it is a list of list
    xtag_trees = []    
    options = None
    single_tree = None
    
    is_option = True
    for i in range(0,len(s)):
        if s[i] == '(':
            stack += 1
        elif s[i] == ')':
            stack -= 1
            if stack == 0 and is_option == True:
                option = s[last_time:i + 1]
                last_time = i + 1
                is_option = False
            elif stack == 0 and is_option == False:
                single_tree = s[last_time:i + 1]
                last_time = i + 1
                is_option = True
                # None is a placeholder for those added in later phases
                xtag_trees.append([None,None,single_tree.strip(),option.strip(),None]) #None here is a placeholder

    return xtag_trees

def second_pass(xtag_trees):
    """
    second_pass() -> list

    Given the result of first_pass(), this function will further
    split the options string into several small strings, each is started by
    a ':' and ended by the start of another option or by the end of the string.
    """
    for entry in xtag_trees:
        options_str = entry[3]
        name_start = options_str.find('"',0)
        name_end = options_str.find('"',name_start + 1)
        entry[0] = options_str[name_start + 1:name_end]

        option_length = len(options_str)
        option_start = name_end + 1
        option_end = option_start
        options_list = []

        # state = 0: outside any structure
        # state = 1: in an option
        # state = 2: in brackets
        # state = 3: in quotes
        state = 0
        
        # One character less, because we need to pre-fetch a character
        for i in range(name_end + 1,option_length - 1):
            ch = options_str[i]
            ch_forward = options_str[i + 1] # pre-fetch
            ch_backward = options_str[i - 1] # back_fetch
            
            if state == 0 and (ch == '\n' or ch == ' '):
                continue
            elif state == 0 and ch == ':':
                state = 1
                option_start = i + 1
            # We should avoid "(:" being considered as an ending symbol
            elif state == 1 and ch != '"' and ch != '(' and ch_forward == ':':
                state = 0
                option_end = i
                options_list.append(options_str[option_start:option_end])
            # This must happen as the last state transition
            elif state == 1 and ch_forward == ')': 
                options_list.append(options_str[option_start:i + 1])
            # skip everything between '(' and ')'
            elif state == 1 and ch == '(':
                state = 2
            elif state == 2 and ch == ')':
                state = 1
            # skip everything between '"' and '"', except '\"'
            elif state == 1 and ch == '"':
                state = 3
            elif state == 3 and ch == '"': # We must distinguish between '\"' and '"'
                if ch_backward != '\\':
                    state = 1
                    
        entry[3] = options_list
        
    return xtag_trees

def third_pass(xtag_trees):
    """
    third_pass() -> list

    Given the result of second_pass(), this function will extract
    the feature structure specifications into a separate list, and then extract
    RHS as well as LHS for further use.  
    """
    pattern = "UNIFICATION-EQUATIONS"
    pattern_len = len(pattern)

    for entry in xtag_trees:
        features = []
        f_temp = None
        
        for option in entry[3]:
            if option[0:pattern_len] == pattern:
                quote_start = option.find('"')
                quote_end = option.find('"',quote_start + 1)
                f_temp = option[quote_start + 1:quote_end]
                break
        else:
            raise NameError("Cannot find unification specification.")

        f_temp = f_temp.splitlines()
        for i in f_temp:
            if i != '':
                exp = i.split('=')
                exp[0] = exp[0].strip()
                exp[1] = exp[1].strip()
                features.append(exp)
                
        entry[1] = features
    return xtag_trees

###########################################################
# second_pass accpets the list generate by the first pass, and then extract options
# from the 3rd element in each list. Each option will be treated as a string and stored
# in a list, which is also the 3rd element of the list
#def second_pass_old(trees):
#    for entry in trees:
#        options_str = entry[3]
#        name_start = options_str.find('"',0)
#        name_end = options_str.find('"',name_start + 1)
#        entry[0] = options_str[name_start + 1:name_end]
#
#        option_length = len(options_str)
#        option_start = name_end + 1
#        option_end = option_start
#        options_list = []
#        
#        while option_end < option_length - 1:
#            option_start = options_str.find(':',option_end)
#            option_end = options_str.find(':',option_start + 1)
#            
#            bracket_start = options_str.find('(',option_start)
#            bracket_end = options_str.find(')',bracket_start + 1)
#            colon_start = options_str.find('"',option_start)
#            colon_end = options_str.find('"',colon_start + 1)

#            if bracket_start == -1:
#                bracket_start = option_length
#            if bracket_end == -1:
#                bracket_end = option_length
#            if colon_start == -1:
#                colon_start = option_length
#            if colon_end == -1:
#                colon_end = option_length

#            if bracket_start < option_end and bracket_end > option_end:
#                option_end = options_str.find(':',bracket_end + 1) # When there is a (:... :...) structure

#            if colon_start < option_end and colon_end > option_end:
#                option_end = options_str.find(':',colon_end + 1)
            
#            if option_end == -1:
#                #option_end = options_str.find(')',option_start)
#                option_end = option_length - 1 # option_end points the last character, ')'
#            options_list.append(options_str[option_start + 1:option_end])
#
#        entry[3] = options_list
#        
#    return trees
############################################################

def add_two_feature(features,l_id,rhs,l_feature1,l_feature2 = None):
    if l_feature2 == None:
        if features.has_key(l_id):
            features[l_id][l_feature1] = rhs
        else:
            features[l_id] = FeatStruct()
            features[l_id][l_feature1] = rhs
    else:
        if features.has_key(l_id):
            if features[l_id].has_key(l_feature1):
                features[l_id][l_feature1][l_feature2] = rhs
            else:
                features[l_id][l_feature1] = FeatStruct()
                features[l_id][l_feature1][l_feature2] = rhs
        else:
            features[l_id] = FeatStruct()
            features[l_id][l_feature1] = FeatStruct()
            features[l_id][l_feature1][l_feature2] = rhs
    return
    
def fourth_pass(xtag_trees):
    """
    fourth_pass() -> list

    Given the result of third_pass(), this function will make
    use of FeatStruct, and build a feature structure dictionary.  
    """
    for xtag_entry in xtag_trees:
        features =  {}
        for feature_entry in xtag_entry[1]:
            lhs = feature_entry[0]
            rhs = feature_entry[1]
            l_separator = lhs.find(':')
            r_separator = rhs.find(':')

            if r_separator == -1:
                l_id = lhs[:l_separator]
                l_space = lhs.find(' ')

                feat_rhs = FeatStruct()
                feat_rhs["__value__"] = rhs
                #feat_rhs = rhs                
                
                if(l_space == -1):
                    l_feature = lhs[l_separator + 2:-1]
                    add_two_feature(features,l_id,feat_rhs,l_feature)
                else:
                    l_feature1 = lhs[l_separator + 2:l_space]
                    l_feature2 = lhs[l_space + 1:-1]
                    add_two_feature(features,l_id,feat_rhs,l_feature1,l_feature2)

        xtag_entry[4] = features
    
    return xtag_trees

def fifth_pass(xtag_trees):
    """
    fifth_pass() -> list

    Given the result of fourth_pass(), this function will continue
    to build the feature structure, and in this phase we must add all values
    even if they are not defined by the tree grammar.  
    """
    for xtag_entry in xtag_trees:
        features = xtag_entry[4]
        for feature_entry in xtag_entry[1]:
            lhs = feature_entry[0]
            rhs = feature_entry[1]
            l_separator = lhs.find(':')
            r_separator = rhs.find(':')   

            if r_separator != -1:
                l_id = lhs[:l_separator]
                r_id = rhs[:r_separator]
                r_feature = rhs[r_separator + 2:-1]
                print r_feature
                l_space = lhs.find(' ')

                if not features.has_key(r_id): # Make sure features[r_id] exists
                    features[r_id] = FeatStruct()
                    features[r_id][r_feature] = FeatStruct(__value__ = '')
                elif not features[r_id].has_key(r_feature): # Make sure features[r_id][r_feature] exists
                    features[r_id][r_feature] = FeatStruct(__value__ = '')

                if(l_space == -1):
                    l_feature = lhs[l_separator + 2:-1]
                    add_two_feature(features,l_id,features[r_id][r_feature],l_feature)
                else:
                    l_feature1 = lhs[l_separator + 2:l_space]
                    l_feature2 = lhs[l_space + 1:-1]
                    add_two_feature(features,l_id,features[r_id][r_feature],l_feature1,l_feature2)

    return xtag_trees

def parse_feature(filename):
    """
    parse_feature() -> list

    Given the name of the file which contains the definition
    of several TAG trees, this function will return a data structure that
    describes those trees as well as options including feature structures.  
    """
    fp = open(filename)
    s = fp.read()
    fp.close()

    return fifth_pass(fourth_pass(third_pass(second_pass(first_pass))))

#def debug(filename):
#    fp = open(filename)
#    s = fp.read()
#    fp.close()
#    t = fifth_pass(fourth_pass(third_pass(second_pass(first_pass(s)))))

#    l = len(t)
#    t[l - 3][4]['D.t']['wh']['__value__'] = 'wangziqi'
    
#    for i in t:
#        for j in i[4].keys():
#            print j
#            print i[4][j]
#            print "-----------------"
#        print "================="

#if __name__ == '__main__':
#    debug('lex.trees')
#else:
#    pass
