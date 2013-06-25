from analyze_morph import analyze_morph
from analyze_syntax import analyze_syntax
from analyze_template import analyze_template

dicts = None

def word_to_features(word):
    global dicts
    result = []
    #print dicts[0][word]
    
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
                print features2,'\n'
    return result
        #print dicts[1][entry[0]]


def debug(dicts):
    print dicts[0][condom]

def init():
    global dicts
    fp = open('trunc_morph.flat')
    s = fp.read()
    morph_dict = analyze_morph(s)
    fp.close()

    fp = open('syntax-coded.flat')
    s = fp.read()
    syntax_dict = analyze_syntax(s)
    fp.close()

    fp = open('templates.lex')
    s = fp.read()
    template_dict = analyze_template(s)
    fp.close()

    dicts = (morph_dict,syntax_dict,template_dict)

if __name__ == '__main__':
    init()
    r = word_to_features('schedules')
    for i in r:
        print '---------------- new -------------------'
        print '================ i[4] =================='
        for j in i[4]:
            print j
        print '================ i[3] =================='
        for j in i[3]:
            print j
        print '================ i[2] =================='
        for j in i[2]:
            print j
        print '================ i[1] =================='
        for j in i[1]:
            print j
        print '================ i[0] =================='
        for j in i[0]:
            print j
