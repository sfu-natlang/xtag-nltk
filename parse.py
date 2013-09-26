from nltk.parse.nonprojectivedependencyparser import *
#help(ProbabilisticNonprojectiveParser)

def print_lable_dist(lable_dist,fp):
    d = lable_dist.freqdist()
    for i in d.keys():
        fp.write(i + ' ' + str(d[i]) + '\n')
    fp.write('?????\n')
    return

def print_feature_dist(feature_dist,fp):
    for i in feature_dist.keys():
        # For debugging
        if len(i) != 2:
            raise ValueError('Invalid tuple in feature_dist')
        
        fp.write(i[0] + ' ' + i[1] + ' ' + str(feature_dist[i]._bins) + '\n')
        d = feature_dist[i].freqdist()
        for j in d.keys():
            fp.write(str(j) + ' ' + str(d[j]) + '\n')
        fp.write(';;;;;\n')
    return
        

def print_train_data(lable_dist,feature_dist,filename="TAGParseData.dat"):
    fp = open(filename, 'w')
    print_lable_dist(lable_dist,fp)
    print_feature_dist(feature_dist,fp)
    fp.close()

def debug_print_train_data():
    print_train_data(None,None)

if __name__ == '__main__':
    debug_print_train_data()
