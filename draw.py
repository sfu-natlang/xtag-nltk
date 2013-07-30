import os
import copy

from util import *
from Tkinter import *
from parse import *
from util import *

class LexView(object):
    """
    A window that lexicalize a TAG Tree set. When type in
    word in the text entry, the TAG Tree Set will be lexicalized.
    Only TAG Trees that can be lexicalized with that word
    remain in the window. The word will be attached to the 
    substitution node of the tree, and feature structure
    will be updated to make the tree consistent with the word.

    """

    def __init__(self, alltrees):
        self._top = Tk()
        self._top.title('NLTK')
        self._top.bind('<Control-x>', self.destroy)
        self._top.bind('<Control-q>', self.destroy)
        self._top.geometry("1400x800")

        frame = Frame(self._top)

        v = StringVar()
        self._e = Entry(frame, textvariable=v)
        self._e.bind("<Return>", self.return_pressed)
        all_button = Button(frame, text='Show All', command=self.show_all)
        button = Button(frame, text="Search", command=self.search)
        self._e.pack(expand=1, fill='both', side=LEFT)

        phrases = StringVar()
        phrases.set("")
        w = OptionMenu(frame, phrases, "one", "two", "three")
        w.pack(side=RIGHT)
        wl = Label(frame, text='multi-word:')
        wl.pack(side=RIGHT)
        
        all_button.pack(side=RIGHT)
        button.pack(side=RIGHT)
        frame.pack(fill='both')
        
        self._tagset = alltrees
        self._alltrees = alltrees
        self._treeview = TAGTreeSetView(self._tagset, self._top)
        self._treeview.pack()
        self._count = {}

    def return_pressed(self, event):
        words = self._e.get().split()
        if len(words) == 0:
            self.show_all()
            return
        self.search()

    def resize(self, *e):
        """
        Resize the window
        """
        self._treeview(e)

    def show_all(self):
        """
        Show all the TAG Tree in window
        """
        self._e.delete(0, END)
        self._tagset = self._alltrees
        self._treeview.clear()
        self._treeview.update(self._tagset)
        return
    
    def search(self):
        words = self._e.get().split()
        if len(words) == 0:
        #    self.show_all()
            return
        self._tagset = TAGTreeSet()
        self._treeview.clear()
        for word in words:
            self._tagset[word] = TAGTreeSet()
            fset = self._tagset[word]
            lex_list = word_to_features(word)
            self._lex_tag_set(lex_list, fset)
            '''
            for morph in lex_list:
                #print morph
                index = ''
                for i in morph[0]:
                    index = index + i[0] + '.' + i[1] + ' '
                if index not in fset:
                    fset[index] = TAGTreeSet()
                sset = fset[index]
                if len(morph[2]) > 0:
                    for tf in morph[2]:
                        ckey = index+tf
                        tf = self._tree_family_key(tf)
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
                        sset[key] += self._alltrees[index][tf].copy(False)
                        for t in sset[key]:
                            if sset[key][t]._lex:
                                sset[key][t]._lex_fs
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
                        for sub in self._alltrees:
                            for tr in self._alltrees[sub]:
                                if t in self._alltrees[sub][tr]:
                                    sset[key] = self._alltrees[sub][tr][t].copy(True)
                        self._count[ckey] += 1
                        if not isinstance(sset[key], TAGTree):
                            raise TypeError('Not TAGTree')
                        sset[key].init_lex(morph[0], morph[3], morph[4])
                if len(morph[0]) > 1:
                    phrases = [v[0] for v in morph[0]]
                    if all(phrase in words for phrase in phrases):
                        index = ''
                        for i in phrases:
                            index = index + i + ' '
                        fset = self._tagset[index]
                '''
            for morph in lex_list:
                if len(morph[0]) > 1:
                    phrases = [v[0] for v in morph[0]]
                    if all(phrase in words for phrase in phrases):
                        index = ''
                        for i in phrases:
                            index = index + i + ' '
                        self._tagset[index] = TAGTreeSet()
                        fset = self._tagset[index]
                        self._lex_tag_set([morph], fset)
        self._treeview.update(self._tagset)
        self._count = {}

    def _lex_tag_set(self, lex_list, fset):
        for morph in lex_list:
            index = ''
            for i in morph[0]:
                index = index + i[0] + '.' + i[1] + ' '
            for i in morph[5][1]:
                index = index + i + '_'
            index = index[:-1]
            if index not in fset:
                fset[index] = TAGTreeSet()
            sset = fset[index]
            if len(morph[2]) > 0:
                for tf in morph[2]:
                    ckey = index+tf
                    tf = self._tree_family_key(tf)
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
                    sset[key] += self._alltrees[index][tf].copy(False)
                    for t in sset[key]:
                        if sset[key][t]._lex:
                            sset[key][t]._lex_fs
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
                    for sub in self._alltrees:
                        for tr in self._alltrees[sub]:
                            if t in self._alltrees[sub][tr]:
                                sset[key] = self._alltrees[sub][tr][t].copy(True)
                    self._count[ckey] += 1
                    if not isinstance(sset[key], TAGTree):
                        raise TypeError('Not TAGTree')
                    sset[key].init_lex(morph[0], morph[3], morph[4])

    def destroy(self, *e):
        if self._top is None: return
        self._top.destroy()
        self._top = None

    def mainloop(self, *args, **kwargs):
        if in_idle(): return
        self._top.mainloop(*args, **kwargs)

    def _tree_family_key(self, tree):
        return tree + '.trees'


def demo():
    cata = get_catalog('../xtag-english-grammar/english.gram')
    sfs = get_start_feature(cata)
    t = parse_from_files(cata, 'tree-files')
    t += parse_from_files(cata, 'family-files')
    t.set_start_fs(sfs)
    morph = get_file_list(cata, 'morphology-files')
    syn = get_file_list(cata, 'lexicon-files')
    temp = get_file_list(cata, 'templates-files')
    default = get_file_list(cata, 'syntax-default')
    morph_path = morph[1]+morph[0][0]
    syn_path = syn[1]+syn[0][0]
    temp_path = temp[1]+temp[0][0]
    default_path = default[1]+default[0][0]
    init(morph_path, syn_path, temp_path, default_path)
    viewer = LexView(t)
    viewer.mainloop()

if __name__ == '__main__':
    demo()
