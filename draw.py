from util import *
from Tkinter import *
from parse import *
#from src.word_to_features import *
#from word_to_features import *
import os
import copy

class LexView(object):

    def __init__(self, alltrees):
        self._top = Tk()
        self._top.title('NLTK')
        self._top.bind('<Control-x>', self.destroy)
        self._top.bind('<Control-q>', self.destroy)
        self._top.geometry("1400x800")

        frame = Frame(self._top)
        #frame.pack(expand=1, fill='both', side = LEFT)

        v = StringVar()
        self._e = Entry(frame, textvariable=v)
        button = Button(frame, text="OK", command=self.okbutton)
        self._e.pack(expand=1, fill='both', side = LEFT)
        button.pack(side = RIGHT)
        frame.pack(fill='both')
        
        self._tagset = alltrees
        self._alltrees = alltrees
        self._treeview = TAGTreeSetView(self._tagset, self._top)
        self._treeview.pack()
        self._count = {}
        #init()
        #self._treeview.destroy()

    def resize(self, *e):
        self._treeview(e)
    
    def okbutton(self):
        self._tagset = TAGTreeSet()
        self._treeview.clear()
        words = self._e.get().split()
        for word in words:
            self._tagset[word] = TAGTreeSet()
            fset = self._tagset[word]
            lex_list = word_to_features(word)
            for morph in lex_list:
                print morph
                index = ''
                for i in morph[0]:
                    index = index + i[0] + '.' + i[1] + ' '
                if index not in fset:
                    fset[index] = TAGTreeSet()
                sset = fset[index]
                if len(morph[2]) > 0:
                    for tf in morph[2]:
                        ckey = index+tf
                        tf = self.tree_family_key(tf)
                        if tf not in sset:
                            key = tf
                            self._count[ckey] = 0
                        else:
                            key = tf[:-5] + '_' + str(self._count[ckey]) + '.trees'
                        sset[key] = TAGTreeSet()
                        index = None
                        for sub in self._alltrees:
                            if tf in self._alltrees[sub]:
                                index = sub
                        if not index:
                            raise NameError('No tree fmaily')
                        #sset[key] += copy.deepcopy(self._alltrees[tf])
                        sset[key] += self._alltrees[index][tf].copy(False)
                        #print 21112
                        for t in sset[key]:
                            if sset[key][t]._lex:
                                sset[key][t]._lex_fs
                            sset[key][t].init_lex(morph[0], morph[3], morph[4])
                            #print key
                            #print t
                            #print sset[key][t]._lex_fs
                        self._count[ckey] += 1
                else:
                    for t in morph[1]:
                        ckey = index+t
                        if t not in sset:
                            key = t
                            self._count[ckey] = 0
                        else:
                            key = t + '_' + str(self._count[ckey])
                        #key = self.tree_family_key(key)
                        for sub in self._alltrees:
                            for tr in self._alltrees[sub]:
                                if t in self._alltrees[sub][tr]:
                                #sset[key] = copy.deepcopy(self._alltrees[tr][t])
                                    sset[key] = self._alltrees[sub][tr][t].copy(True)
                                #print tr, t
                                self._count[ckey] += 1
                        if not isinstance(sset[key], TAGTree):
                            print key
                            raise TypeError('Not TAGTree')
                        sset[key].init_lex(morph[0], morph[3], morph[4])
                        #print headlist
        self._treeview.update(self._tagset)
        self._count = {}
        #print self._tagset.tree_count()
        #for i in self._tagset:
        #    for j in self._tagset[i]:
        #        print self._tagset[i][j].tree_count()
        #self._treeview.populate_tree('', self._tagset)

    def destroy(self, *e):
        if self._top is None: return
        self._top.destroy()
        self._top = None

    def mainloop(self, *args, **kwargs):
        if in_idle(): return
        self._top.mainloop(*args, **kwargs)

    def tree_family_key(self, tree):
        #print tree
        return tree + '.trees'

    #def draw(self):

#def lex_draw(trees):
#    LexView(trees).mainloop()
#    return

def demo():
    from util import *
    
    #files = ['grammar/advs-adjs.trees']
    #directory = 'grammar'
    #allfiles = [os.path.join(directory, i) for i in os.listdir(directory)]
    #print len(allfiles)#[44]
    #t = parse_from_files(files, directory)
    #alltrees = parse_from_files(allfiles, directory)
    cata = get_catalog('../xtag-english-grammar/english.gram')
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    morph = get_file_list(cata, 'morphology-files')
    syn = get_file_list(cata, 'lexicon-files')
    temp = get_file_list(cata, 'templates-files')
    morph_path = morph[1]+morph[0][0]
    syn_path = syn[1]+syn[0][0]
    temp_path = temp[1]+temp[0][0]
    init(morph_path, syn_path, temp_path)
    viewer = LexView(t)
    viewer.mainloop()

if __name__ == '__main__':
    demo()
