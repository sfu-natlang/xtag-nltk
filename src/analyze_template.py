from nltk.featstruct import FeatStruct

# This function makes a feature structure using a list of lhs which are nested
# e.g. if lhs = ['a','b','c','d'] and rhs = 'wzq' then the
# fs shoule be [a = [b = [c = [d = 'wzq']]]]
def make_fs(lhs,rhs):
    new_fs = FeatStruct()
    if len(lhs) == 1:
        new_fs[lhs[0]] = rhs
    else:
        new_fs[lhs[0]] = make_fs(lhs[1:],rhs)
        
    return new_fs

def analyze_template(s):
    lines = s.splitlines()
    feature_list = {}
    for l in lines:
        l = l.strip()
        if l == '' or l[0] == ';':
            continue
        if l[0] == '@':
            if l[-1] != '!':
                raise TypeError("Each line should be terminated with a '!'")
            l = l[1:-1]
            # we only split the name and the other part
            temp = l.split(None,1)
            name = temp[0]
            l = l[len(name):].strip()
            features = l.split(',')

            fs = FeatStruct()
            for f in features:
                f = f.strip()
                index = f.find('=')
                if f[0] == '@' and feature_list.has_key(f[1:]):
                    fs = fs.unify(feature_list[f[1:]])    # unify() does not change in-place
                elif index != -1:
                    lhs = f[:index].strip()
                    rhs = f[index + 1:].strip()
                    if rhs[0] == '@':     # rhs can also be reference
                        rhs = feature_list[rhs[1:]]
                    if lhs[0] != '<' or lhs[-1] != '>':
                        raise TypeError('The left hand side of a feature structure must be wrapped with <>')
                    lhs = lhs[1:-1]
                    path = lhs.split()
                    #path.reverse()# This method is in-place
                    fs = fs.unify(make_fs(path,rhs))
            feature_list[name] = fs
            print name
            print fs,'\n'
        elif l[0] == '#':
            #print 'Not implemented yet'
            pass

        
def debug(filename):
    fp = open(filename)
    s = fp.read()
    fp.close()
    analyze_template(s)

if __name__ == '__main__':
    debug('templates.lex')
