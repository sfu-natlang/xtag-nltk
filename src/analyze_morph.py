
# The return value is a dictionaru using words in the sentence as index. The
# entry is a list, the element of which is a tuple. The first element of the
# tuple is the lexicon, the second element of the tuple is the type of this lex,
# and the third element of the tuple is again a list 
# the entries of which are strings indicating the features.
def analyze_morph(s):
    """

    analyze_morph(string) -> dictionary
    
    This function accepts input as a string read form file 'morph_english.flat'
    which contains the morphology information of XTAG system. The output is a
    dictionary using a single word as index and returns the morphology entry.
    
    """
    morph = {}
    lines = s.splitlines()
    for l in lines:
        if l == '':
            continue

        sub_line = []
        start = 0
        while True:
            index = l.find('#',start)
            if index == -1:
                sub_line.append(l[start:].split())
                break
            else:
                sub_line.append(l[start:index].split())
                start = index + 1
        #print sub_line
        morph_list = []
        for i in range(0,len(sub_line)):
            m = sub_line[i]
            if i == 0:
                morph_list.append((m[1],m[2],m[3:]))
            else:
                morph_list.append((m[0],m[1],m[2:]))
                
        morph[sub_line[0][0]] = morph_list
        
    return morph

def debug(filename):
    fp = open(filename)
    s = fp.read()
    fp.close()
    dic = analyze_morph(s)
    print dic

if __name__ == '__main__':
    debug('trunc_morph_test.flat')
