# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#

import os
import copy

from util import *
from Tkinter import *
from parse import *

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

        self.frame = Frame(self._top)

        v = StringVar()
        self._e = Entry(self.frame, textvariable=v)
        self._e.bind("<Return>", self.return_pressed)
        all_button = Button(self.frame, text='Show All', command=self.show_all)
        button = Button(self.frame, text="Search", command=self.lex_search)
        self._e.pack(expand=1, fill='both', side=LEFT)

        self.phrases = StringVar()
        self.phrases.set("")
        update_button = Button(self.frame, text="Select", command=self.update_lex_tree)
        self._w = OptionMenu(self.frame, self.phrases, [])
        update_button.pack(side=RIGHT)
        self._w.pack(side=RIGHT)
        wl = Label(self.frame, text='Anchors:')
        wl.pack(side=RIGHT)
        
        all_button.pack(side=RIGHT)
        button.pack(side=RIGHT)
        self.frame.pack(fill='both')
        
        self._tagset = alltrees
        self._alltrees = alltrees
        self._treeview = TAGTreeSetView(self._tagset, (self._top, self.display))
        self._treeview.pack()
        self._dicword = {}
        self._count = {}

    def display(self, event=None):
        """
        Display the tag tree on the canvas when the tree
        is selected.
        """
        node = self._treeview._tagview.focus()
        path = self._treeview._tagview.set(node, "fullpath").split('/')
        tree = self._treeview._trees
        for subpath in path[1:]:
            if subpath in tree:
                if not isinstance(tree, type(self._treeview._trees)):
                    if tree._lex:
                        tree[subpath] = tree[subpath].copy(True)

                tree = tree[subpath]
            else:
                raise TypeError("%s: tree does not match"
                             % type(self).__name__)

        if not isinstance(tree, type(self._treeview._trees)):
            words = tree_to_words(subpath)
            if len(words) > 0:
                self.update_anchor(words)
            if tree.start_feat:
                self._treeview._sfs_button['text'] = 'Delete Start Features'
            else:
                self._treeview._sfs_button['text'] = 'Add Start Features'
            if tree._lex:
                tree.lexicalize()
                tree._lex = False
                self._treeview._tw.redraw(self._treeview._show_fs, tree)
            else:
                self._treeview._tw.redraw(self._treeview._show_fs, tree)
        else:
            for path in tree:
                if isinstance(tree[path], type(self._treeview._trees)):
                    return
            self.phrases.set("")
            if isinstance(tree, type(self._treeview._trees)) and subpath[-6:] == '.trees':
                tree_fam = tree[subpath]
                treename = subpath[:-6]
            else:
                treename = subpath

            words = tree_to_words(treename)
            if len(words) > 0:
                self.update_anchor(words)

    def update_anchor(self, words):
        """
        Update anchors with selected words
        :param: selected words
        :type: basestring
        """
        self.clean_anchor()
        for choice in words:
            phrase = ''
            for term in choice:
                phrase = phrase + term[0] + ' '
            if not phrase in self._dicword:
                self._dicword[phrase] = choice
            else:
                continue
            import Tkinter as tk
            self._w['menu'].add_command(label=phrase, command=tk._setit(self.phrases, phrase))

    def clean_anchor(self):
        """
        Clean anchors of this viewer
        """
        self._dicword = {}
        self._w['menu'].delete(0, 'end')        

    def update_lex_tree(self):
        """
        Update the viewer with selected words
        """
        words = self.phrases.get().split()
        if len(words) == 0:
            return
        self._tagset = TAGTreeSet()
        self._e.delete(0, END)
        self._treeview.clear()
        for word in words:
            self._tagset[word] = TAGTreeSet()
            fset = self._tagset[word]
            lex_list = word_to_features(word)
            self.lexicalize_tagset(lex_list, fset)
            for morph in lex_list:
                if len(morph[0]) > 1:
                    phrases = [v[0] for v in morph[0]]
                    if phrases == words:
                        index = ''
                        for i in phrases:
                            index = index + i + ' '
                        if not index in self._tagset:
                            self._tagset[index] = TAGTreeSet()
                        fset = self._tagset[index]
                        self.lexicalize_tagset([morph], fset)
        self._tagset.set_start_fs(self._alltrees.start_fs)
        self._treeview.update(self._tagset)
        self._count = {}

    def return_pressed(self, event):
        """
        Short-cut for pressing return to show feature structures
        """
        self.clean_anchor()
        words = self._e.get().split()
        if len(words) == 0:
            self.show_all()
            return
        self.lex_search()

    def resize(self, *e):
        """
        Resize the window
        """
        self._treeview(e)

    def show_all(self):
        """
        Show all the TAG Tree in window
        """
        self.clean_anchor()
        self._e.delete(0, END)
        self._tagset = self._alltrees
        self._treeview.clear()
        self._treeview.update(self._tagset)
        return
    
    def lex_search(self):
        """
        Update the viewer after lexicalization
        """
        words = self._e.get().split()
        if len(words) == 0:
            return
        self.clean_anchor()
        self._tagset = TAGTreeSet()
        self._treeview.clear()
        for word in words:
            self._tagset[word] = TAGTreeSet()
            fset = self._tagset[word]
            lex_list = word_to_features(word)
            self.lexicalize_tagset(lex_list, fset)
            for morph in lex_list:
                if len(morph[0]) > 1:
                    phrases = [v[0] for v in morph[0]]
                    if words == phrases:
                        index = ''
                        for i in phrases:
                            index = index + i + ' '
                        if not isinstance(self._tagset[index], TAGTreeSet):
                            self._tagset[index] = TAGTreeSet()
                        fset = self._tagset[index]
                        self.lexicalize_tagset([morph], fset)
        self._tagset.set_start_fs(self._alltrees.start_fs)
        self._treeview.update(self._tagset)
        self._count = {}

    def lexicalize_tagset(self, lex_list, fset):
        """
        Lexicalize all TAG tree set
        :param lex_list: a list of lexicalized node
        :type: list
        :alltrees: TAG tree set to be lexicalized
        :type: TAGTreeSet
        """
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
                    tf = tf + '.trees'
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
                    sset[key] += self._alltrees[index][tf].copy(True)
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


def demo():
    t = load()
    viewer = LexView(t)
    viewer.mainloop()

if __name__ == '__main__':
    demo()
