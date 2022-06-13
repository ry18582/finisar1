#!/usr/bin/env python
# -*- coding: utf-8 -*-
from functools import reduce, wraps


def attr_reader(*attributes):
    """Publish private attributes (_attr) as read-only (attr)"""

    def _decorator(cls):
        # Define a function to avoid late binding inside loop
        def _add_reader(klass, attr):
            reader = property(lambda self: getattr(self, "_" + attr))
            setattr(klass, attr, reader)
            return klass

        return reduce(_add_reader, attributes, cls)

    return _decorator


def memoized(method):
    """Evaluate the method and memoize it's value in a _ prefixed attribute"""

    @wraps(method)
    def _memoized(self, *args, **kwargs):
        attr = "_" + method.__name__

        if hasattr(self, attr):
            return getattr(self, attr)

        value = method(self, *args, **kwargs)
        setattr(self, attr, value)

        return value

    return _memoized
