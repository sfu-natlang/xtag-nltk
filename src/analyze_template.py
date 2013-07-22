from nltk.featstruct import FeatStruct

def make_fs(lhs,rhs):
    # This function makes a feature structure using a list of lhs which are nested
    # e.g. if lhs = ['a','b','c','d'] and rhs = 'wzq' then the
    # fs shoule be [a = [b = [c = [d = 'wzq']]]]
    new_fs = FeatStruct()
    
    if len(lhs) == 1:
        inner = FeatStruct()
        inner['__value__'] = rhs
        rhs = inner
        new_fs[lhs[0]] = rhs
    else:
        new_fs[lhs[0]] = make_fs(lhs[1:],rhs)
        
    return new_fs

def merge_fs(fs1,fs2):
    # This function merges fs2 into fs1, changing fs1 in-place
    # It's a cheaper and faster alternative of unify(), which will check
    # all the similarities and differences between fs1 and fs2. But this one
    # just assumes that fs2 and fs1 does not have any entries in common
    # NOTICE: In Templates.lex we cannot guarantee there is no overlap
    # so only use this function when it IS clear.
    for k in fs2.keys():
        fs1[k] = fs2[k]

def analyze_template(s):
    # The return value of this function is a tuple. The first element of the tuple is a dictionary
    # using identifiers from morph.flat, and the entries are feature structures
    # with proper values set. The second element is a dictionary using keys from
    # syntax-coded.flat, which will return a list containing all feature structures
    # from a given identifier.
    lines = s.splitlines()
    feature_list = {}
    feature_list2 = {}
    for l in lines:
        #print l
        l = l.strip()
        if l == '' or l[0] == ';':
            continue
        
        index = l.find(';')
        if index != -1:
            l = l[:index]
            l = l.strip()
        
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
                    if rhs[0] == '@':      # rhs can also be reference
                        rhs = feature_list[rhs[1:]]
                    if lhs[0] != '<' or lhs[-1] != '>':
                        raise TypeError('The left hand side of a feature structure must be wrapped with <>')
                    lhs = lhs[1:-1]
                    path = lhs.split()
                    #path.reverse()    # This method is in-place
                    fs = fs.unify(make_fs(path,rhs))
            feature_list[name] = fs
            #print name
            #print fs,'\n'
        elif l[0] == '#':
            if l[-1] != '!':
                raise TypeError('Invalid input line, must be terminated by "!"')
            l = l[1:-1]
            tokens = l.split(None,1)     # Split for once using space character
            word_pos = tokens[0].strip()

            features = tokens[1].split(',')
            new_fs = FeatStruct()
            for fs in features:
                tokens = fs.split(':',1)
                node_type = tokens[0].strip()
                tokens = tokens[1].split('=',1)
                lhs = tokens[0].strip()[1:-1]    # Remove <>
                rhs = tokens[1].strip()
                lhs = lhs.split()
                if new_fs.has_key(node_type):
                    new_fs[node_type] = new_fs[node_type].unify(make_fs(lhs,rhs))
                else:
                    new_fs[node_type] = make_fs(lhs,rhs)
            if feature_list2.has_key(word_pos) == False:
                feature_list2[word_pos] = new_fs
            else:
                #feature_list2[word_pos].append(new_fs)
                raise KeyError('Duplicate defitinion detected: %s.' % (word_pos))
        else:
            raise TypeError('Cannot recognize line: %s.' % (l))
    return (feature_list,feature_list2)
        
#def debug(filename):
#   fp = open(filename)
#    s = fp.read()
#    fp.close()
#    analyze_template(s)

#if __name__ == '__main__':
#    debug('templates.lex')
