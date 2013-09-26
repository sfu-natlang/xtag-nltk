from nltk.parse.nonprojectivedependencyparser import *
import pickle

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

def dump_to_disk(filename,obj):
    """
    Dump an object into the disk using pickle
    :param filename: The name of the dumping file
    :type filename: str
    :param obj: Any object you want to dump
    :type obj: Any object
    """
    fp = open(filename,'wb')
    pickle.dump(obj,fp)
    fp.close()

def restore_from_disk(filename):
    """
    Restore the dumped file using pickle to an obejct
    :param filename: The file you want to read from
    :type filename: str
    :return: The restored object
    :rtype: Any object
    """
    fp = open(filename,'rb')
    obj = pickle.load(fp)
    fp.close()
    return obj

def debug_print_train_data():
    print_train_data(None,None)

def debug_dump_and_restore():
    d = {'a': 1,'b': 2,'c':3,None:4}
    e = ['ed','ser','56','wertwert']
    f = {3:d,5:e,7:'dffdfdf'}
    dump_to_disk('dict.dat',f)
    rd = restore_from_disk('dict.dat')
    print rd

if __name__ == '__main__':
    debug_dump_and_restore()
