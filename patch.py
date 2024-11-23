# patch.py

import collections
import collections.abc

# Corrige o problema do graphene com a importação de Mapping
if not hasattr(collections, 'Mapping'):
    collections.Mapping = collections.abc.Mapping

# Corrige o problema do graphene com a importação de Iterable
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable