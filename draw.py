from util import *
from Tkinter import *
from word_to_features import *
import os
import copy

class LexView(object):

    def __init__(self, alltrees, tagtrees=None):
        self._top = Tk()
        self._top.title('NLTK')
        self._top.bind('<Control-x>', self.destroy)
        self._top.bind('<Control-q>', self.destroy)

        frame = Frame(self._top)
        #frame.pack(expand=1, fill='both', side = LEFT)

        v = StringVar()
        self._e = Entry(frame, textvariable=v)
        button = Button(frame, text="OK", command=self.okbutton)
        self._e.pack(expand=1, fill='both', side = LEFT)
        button.pack(side = RIGHT)
        frame.pack(fill='both')
        
        self._tagset = tagtrees
        self._alltrees = alltrees
        self._treeview = TAGTreeSetView(self._tagset, self._top)
        self._treeview.pack()
        self._count = {}
        init()
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
                index = ''
                for i in morph[0]:
                    index = index + i[0] + '.' + i[1] + ' '
                if index not in fset:
                    fset[index] = TAGTreeSet()
                sset = fset[index]
                if len(morph[2]) > 0:
                    for tf in morph[2]:
                        ckey = index+tf
                        if tf not in sset:
                            key = tf
                            self._count[ckey] = 0
                        else:
                            key = tf + '_' + str(self._count[ckey])
                        #if tf == 'Tnx0Vplnx1':
                        #    continue
                        sset[key] = TAGTreeSet()
                        if self.tree_family_key(tf) not in self._alltrees:
                            raise NameError('No tree fmaily')
                        sset[key] += copy.deepcopy(self._alltrees[self.tree_family_key(tf)])
                        for t in sset[key]:
                            #sset[key][t].get_all_fs()
                            sset[key][t].init_lex(morph[0], morph[3], morph[4])
                        self._count[ckey] += 1
                else:
                    for t in morph[1]:
                        ckey = index+t
                        if t not in sset:
                            key = t
                            self._count[ckey] = 0
                        else:
                            key = t + '_' + str(self._count[ckey])
                        for tr in self._alltrees:
                            if t in self._alltrees[tr]:
                                sset[key] = copy.deepcopy(self._alltrees[tr][t])
                                #print tr, t
                            self._count[ckey] += 1
                        if not isinstance(sset[key], TAGTree):
                            raise TypeError('Not TAGTree')
                        sset[key].init_lex(morph[0], morph[3], morph[4])
                        #print headlist
        self._treeview.update(self._tagset)
        self._count = {}
        #self._treeview.populate_tree('', self._tagset)

    def destroy(self, *e):
        if self._top is None: return
        self._top.destroy()
        self._top = None

    def mainloop(self, *args, **kwargs):
        if in_idle(): return
        self._top.mainloop(*args, **kwargs)

    def tree_family_key(self, tree):
        return tree + '.trees'

    #def draw(self):

#def lex_draw(trees):
#    LexView(trees).mainloop()
#    return

def demo():
    from util import xtag_parser
    from util import parse_from_files
    
    files = ['grammar/advs-adjs.trees']
    directory = 'grammar'
    allfiles = [os.path.join(directory, i) for i in os.listdir(directory)]
    #print len(allfiles)#[44]
    #t = parse_from_files(files, directory)
    alltrees = parse_from_files(allfiles, directory)
    viewer = LexView(alltrees, alltrees)
    viewer.mainloop()

if __name__ == '__main__':
    demo()
