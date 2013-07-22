
from nltk.featstruct import FeatStruct
import re

def remove_value_tag(feature):
    new_feature = FeatStruct()
    for i in feature.keys():
        if feature[i].has_key('__value__'):
            new_feature[i] = feature[i]['__value__']
        else:
            new_feature[i] = remove_value_tag(feature[i])
    return new_feature

# This function acceps a normalized feature structure (which uses __value__
# as the last level of indexing) and a regular expression, and returns
# a new feature structure that match the regexp or do not match.
def match_feature(feature,regexp,operation=0):
    """
    match_feature(feature,regexp,operation=0) -> FeatStruct

    This function is used to filter a feature structure with a regular exression.
    The regular expression should be written in the form that XTAG system uses,
    which has a '__value__' entry at the last level of indexing.

    feature: The feature that you would like to filter

    regexp: An acceptable regular expression by module re

    operation: 0 if positive filtering will be done, 1 if negative filtering.
    positive filtering means that all RHS values that match the regexp will be
    retained, while negative filtering means that all RHS values that doesn't
    match will be retained.
    """
    new_feature = FeatStruct()
    count = 0
    for i in feature.keys():
        val = feature[i]
        if val.has_key('__value__'):
            #search_ret = re.search(regexp,val['__value__'])
            search_ret = re.search(regexp,i)
            if operation == 0 and search_ret != None:
                new_feature[i] = val
                count += 1
            elif operation == 1 and search_ret == None:
                new_feature[i] = val
                count += 1
        else:
            search_ret = re.search(regexp,i)
            if operation == 0 and search_ret != None:
                new_feature[i] = val
                count += 1
            elif operation == 1 and search_ret == None:
                new_feature[i] = val
                count += 1
            else:
                ret = match_feature(val,regexp,operation)
                #print ret,'\n'
                if ret != None:
                    new_feature[i] = ret
                    count += 1


    #print new_feature,'\n'
    if count == 0:
        return None
    else:
        return new_feature

def debug():
    a = FeatStruct()
    b = FeatStruct()
    c = FeatStruct()
    d = FeatStruct()
    a['__value__'] = 'OKWANGZiqi'
    b['__value__'] = 'WANGYunpeng'
    c['__value__'] = "WWA!!!"
    d['__value__'] = 'WZQ(*&YTG'
    e = FeatStruct()
    e['first'] = a
    e['second'] = b
    e['third'] = c
    e['fourth'] = d
    f = FeatStruct()
    f['nested'] = e
    g = FeatStruct()
    g['__value__'] = "WAAAAAAAAH!"
    f['single'] = g    
    print remove_value_tag(match_feature(f,'i',0))

if __name__ == "__main__":
    debug()
