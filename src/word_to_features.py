from analyze_morph import analyze_morph
from analyze_syntax import analyze_syntax
from analyze_template import analyze_template
from analyze_catalog import get_catalog,get_file_list

dicts = None
inited = False

def word_to_features(word):
    # This function will convert the word into the feature structures associated
    # with this word. The return value of this function is a list, each element
    # of which is a tuple. The element of the list is the morph of the word.
    # NOTICE: This function must be run after init() be called, or it will
    # throw the exception.
    """
    word_to_features(word) -> list

    Give a word of any form, e.g. take, took, taken, taking, this function will
    return a list of all possible features of this word. The return value is a
    list containing all possibilities.
    """
    if inited == False:
        raise KeyError("Initial file name not provided. Please run init() first.")

    global dicts
    result = []
    #print dicts[0][word]
    if not dicts[0].has_key(word):
        return None
    
    for entry in dicts[0][word]:
        temp_feature = dicts[1][entry[0]]
        #for f in entry[2]:
            #print dicts[2][0][f],'\n\n'
            #features.append(dicts[2][0][f])

        for i in temp_feature:
            if i[0][0][0] == entry[0] and i[0][0][1] == entry[1]:
                features = []
                features2 = []
                for j in i[3]:
                    features.append(dicts[2][1][j[1:]])
                for j in entry[2]:
                    features2.append(dicts[2][0][j])
                
                result.append((i[0],i[1],i[2],features,features2))
                #print features2,'\n'
    return result
        #print dicts[1][entry[0]]

def init(morph,syntax,temp):
    # This function will initiate the environment where the XTAG grammar
    # system will run.
    # morph is the path of trunc_morph.flat
    # syntax is the path of syntax-coded.flat
    # temp is the path of templates.lex (there are two of them, both are OK)
    # All path can be absolute path or relative path
    """
    init(morph,syntax,temp) -> None

    Given the three dictionary files, the init() will initialize the environment
    for word_to_features() and other support functions to function. This should
    be the first call before any other calls to word_to_features().
    """
    global dicts
    fp = open(morph)
    s = fp.read()
    morph_dict = analyze_morph(s)
    fp.close()

    fp = open(syntax)
    s = fp.read()
    syntax_dict = analyze_syntax(s)
    fp.close()

    fp = open(temp)
    s = fp.read()
    template_dict = analyze_template(s)
    fp.close()

    dicts = (morph_dict,syntax_dict,template_dict)
    inited = True
    return

#def demo():
#    init()
#    r = word_to_features('schedules')
#    for i in r:
#        print '---------------- new -------------------'
#        print '================ i[4] =================='
#        for j in i[4]:
#            print j
#        print '================ i[3] =================='
#        for j in i[3]:
#            print j
#        print '================ i[2] =================='
#        for j in i[2]:
#            print j
#        print '================ i[1] =================='
#        for j in i[1]:
#            print j
#        print '================ i[0] =================='
#        for j in i[0]:
#            print j

#if __name__ == '__main__':
#    demo()
#else:
#    pass
