#!/usr/bin/env python

"""
A set of classes used to dynamically wrap FAUST DSP programs in Python.

This package defines three types:
- PythonUI is an implementation of the UIGlue C struct.
- PythonMeta is an implementation of the MetaGlue C struct.
- PythonDSP wraps the DSP struct.
- FAUST integrates the other two, sets up the CFFI environment (defines the
  data types and API) and compiles the FAUST program.  This is the class you
  most likely want to use.
"""

from . wrapper import FAUST
from . python_ui import PythonUI, Param
from . python_meta import PythonMeta
from . python_dsp import PythonDSP

# TODO: see which meta-data is still relevant. pydoc definitely uses "author",
# "credits" and "version" (and "date"), should the rest be removed?
__author__ = "Marc Joliet"
__copyright__ = "Copyright 2013, Marc Joliet"
__credits__ = "Marc Joliet"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Marc Joliet"
__email__ = "marcec@gmx.de"
__status__ = "Prototype"

__all__ = ["FAUST", "PythonUI", "PythonMeta", "PythonDSP", "Param", "wrapper"]
