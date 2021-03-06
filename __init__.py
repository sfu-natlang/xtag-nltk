# Natural Language Toolkit: Tree-Adjoining Grammar
#
# Copyright (C) 2001-2013 NLTK Project
# Author: WANG Ziqi, Haotian Zhang <{zwa47,haotianz}@sfu.ca>
#
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT
#
import nltk.compat
try:
    import Tkinter
except ImportError:
    import warnings
    warnings.warn("nltk.xtag package not loaded "
                  "(please install Tkinter library).")
else:
    from .draw import LexView
    from .util import (TAGTreeSetView, TAGTree, load,
                      TAGTreeWidget, TAGTreeView, TAGTreeSet)
