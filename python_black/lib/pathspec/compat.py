# encoding: utf-8
"""
This module provides compatibility between Python 2 and 3. Hardly
anything is used by this project to constitute including `six`_.

.. _`six`: http://pythonhosted.org/six
"""

unicode = str
string_types = (unicode,)

from collections.abc import Iterable
from itertools import zip_longest as izip_longest


def iterkeys(mapping):
    return mapping.keys()


from collections.abc import Collection

CollectionType = Collection
IterableType = Iterable
