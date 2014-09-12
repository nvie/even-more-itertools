from __future__ import absolute_import, print_function

import sys
from collections import Counter, deque
from heapq import heapify, heappop, heappushpop
from itertools import count, tee

from more_itertools import chunked, consume, peekable, take

PY2 = sys.version_info[0] == 2
if PY2:
    from itertools import imap as map  # pragma: no cover
    from itertools import izip as zip  # pragma: no cover


def invert(predicate):
    return lambda v: not predicate(v)


def icompact(iterable):
    """
    Lazily remove empty values from an iterable.

        >>> list(icompact(range(3)))
        [1, 2]
        >>> list(icompact(['thing', 1, 0, None, 'bar', {}]))
        ['thing', 1, 'bar']

    """
    return (item for item in iter(iterable) if item)


def compact(iterable):
    """
    Remove empty values from an iterable, returning a list.

        >>> compact(range(3))
        [1, 2]
        >>> compact(['thing', 1, 0, None, 'bar', {}])
        ['thing', 1, 'bar']

    """
    return list(icompact(iterable))


def compact_dict(data):
    """
    Remove empty values from a dictionary.

        >>> compact_dict({'a': None, 'b': 0, 'c': False, 'd': 'bananas'})
        {'d': 'bananas'}

    """
    return {k: v for k, v in data.items() if v}


def grouper(tuples, bare=False):
    """
    Groups lists of tuples by their first column.

        >>> list(grouper([(1, 2, 3), (1, 5, 7), (2, 5, 7)]))
        [(1, [(2, 3), (5, 7)]), (2, [(5, 7)])]

    A "bare" list is a list with only 2-tuples, and can be grouped more
    efficiently.  If this is desired, pass in the `bare` flag.

        >>> list(grouper([(1, 2), (1, 5), (2, 5)], bare=True))
        [(1, [2, 5]), (2, [5])]

    """
    if bare:
        tuples = ((value, rest) for value, rest in tuples)
    else:
        # tuples = ((value, rest) for value, *rest in tuples)  # identical, but Python 3 only
        tuples = ((tup[0], tup[1:]) for tup in tuples)

    last_id = object()  # dummy
    items = None
    for value, rest in tuples:
        if value != last_id:
            # Start new fresh list after returning the previous collection
            if items is not None:
                yield (last_id, items)
            last_id = value
            items = []

        items.append(rest)

    if items is not None:
        yield (last_id, items)


def sectionize(pred, iterable):
    """

    Define a function that, for each entry, can determine whether it's
    a section or a normal item:

        >>> is_section = lambda x: isinstance(x, str)

    Use it to sectionize an input stream:

        >>> data = ['A', 0, 1, 2, 'B', 3, 4]
        >>> [(sec, list(items)) for sec, items in sectionize(is_section, data)]
        [('A', [0, 1, 2]), ('B', [3, 4])]

        >>> data = ['A', 'B']
        >>> [(sec, list(items)) for sec, items in sectionize(is_section, data)]
        [('A', []), ('B', [])]

    Exception will be raised when the iterable does not start with a section:

        >>> from more_itertools import consume
        >>> data = [0, 'B', 3, 4]
        >>> consume(sectionize(is_section, [0, 'B', 3, 4]))
        Traceback (most recent call last):
            ...
        ValueError: expected a section, but found: 0

    The subiterators _must_ be consumed before the next section can be gotten.
    This is a "safety measure" so that you don't lose data if you don't
    consume the subiterators:

        >>> data = ['A', 0, 1, 2, 'B', 3, 4]
        >>> [sec for sec, _ in sectionize(is_section, data)]  # does NOT return ['A', 'B'] (!)
        Traceback (most recent call last):
            ...
        ValueError: expected a section, but found: 0

    """
    buf = deque(maxlen=1)
    it = iter(iterable)

    def iter_until_section():
        for item in it:
            if pred(item):
                buf.append(item)
                break
            else:
                yield item

    while True:
        if buf:
            item = buf.popleft()
        else:
            item = next(it)  # raise StopIteration when empty

        if pred(item):
            yield (item, iter_until_section())
        else:
            raise ValueError('expected a section, but found: {}'.format(item))


def side_effect(fn, iterable, chunk_size=None):
    """
    Passes through the iterable, but invokes a function for each item
    iterated over.

    Can be useful for lazy counting, logging, collecting data, or updating
    progress bars, anything un-pure.

    `fn` must be a function that takes a single argument.  Its return value
    will be discarded.

    Examples:

        >>> from more_itertools import take, consume
        >>> iterable = range(10)
        >>> iterable = side_effect(print, iterable)
        >>> consume(take(3, iterable))
        0
        1
        2

    Example for collecting data as it streams through:

        >>> iterable = range(10)
        >>> c = []
        >>> iterable = side_effect(c.append, iterable)
        >>> consume(take(3, iterable))
        >>> c
        [0, 1, 2]

    Collecting items in chunks:

        >>> iterable = range(10)
        >>> c, d = [], []
        >>> iterable = side_effect(lambda xs: c.append(sum(xs)), iterable, 2)
        >>> iterable = side_effect(lambda xs: d.append(sum(xs)), iterable, 3)
        >>> list(iterable)
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> c
        [1, 5, 9, 13, 17]
        >>> d
        [3, 12, 21, 9]

    Emit progress:

        >>> iterable = range(100)
        >>> iterable = side_effect(lambda xs: print('Processed ' + str(len(xs)) + ' items'), iterable, 30)
        >>> consume(iterable)
        Processed 30 items
        Processed 30 items
        Processed 30 items
        Processed 10 items

    """
    if chunk_size is None:
        for item in iterable:
            fn(item)
            yield item
    else:
        for chunk in chunked(iterable, chunk_size):
            fn(chunk)
            for item in chunk:
                yield item


def freq(iterable, key=None, min_freq=None):
    """
    Given an iterable and an optional key function, returns a frequency table
    for the values in the iterable.

    >>> freq(['foo', 'bar', 'baz', 'foo', 'bar']) == {'foo': 2, 'bar': 2, 'baz': 1}
    True
    >>> freq(['foo', 'bar', 'baz', 'foo', 'bar'], min_freq=2) == {'foo': 2, 'bar': 2}
    True
    >>> freq(['foo', 'bar', 'baz', 'foo', 'bar'], key=lambda s: s[0].upper()) == {'F': 2, 'B': 3}
    True
    """
    if key is not None:
        iterable = (key(item) for item in iterable)
    c = Counter(iterable)
    if min_freq is not None:
        return {k: count for k, count in c.items() if count >= min_freq}
    else:
        return {k: count for k, count in c.items()}


def isort(iterable, bufsize=1024, key=None):
    """
    Partially sorts a (potentially infinite) iterable in a best-effort way
    with fixed memory usage by maintaining a priority queue of `bufsize`,
    essentially acting as a "lookahead".

    In other words, will always yield the smallest value within the lookahead
    window next.

    Increasing the bufsize will lead to better results.

        >>> a = [1, 4, 9, 2, 5, 3, 7, 8, 0, 6]  # randomly ordered
        >>> list(isort(a, bufsize=3))
        [1, 2, 3, 4, 5, 0, 6, 7, 8, 9]

        >>> list(isort(a, bufsize=6))
        [1, 2, 0, 3, 4, 5, 6, 7, 8, 9]

        >>> list(isort(a, bufsize=8))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        >>> diff_from_three = lambda n: abs(3 - n)
        >>> list(isort(a, bufsize=5, key=diff_from_three))
        [3, 2, 4, 5, 1, 6, 0, 7, 8, 9]
    """
    it = iter(iterable)

    if key is None:
        buf = take(bufsize, it)
        heapify(buf)
        for item in it:
            yield heappushpop(buf, item)

        while buf:
            yield heappop(buf)
    else:
        i1, i2 = tee(it)
        it = zip(map(key, i1), count(0, -1), i2)  # decorate
        buf = take(bufsize, it)
        heapify(buf)
        for item in it:
            yield heappushpop(buf, item)[2]  # undecorate

        while buf:
            yield heappop(buf)[2]  # undecorate


class Scanner:
    def __init__(self, stream):
        self.stream = peekable(stream)

    def __iter__(self):
        return iter(self.stream)

    def __next__(self):
        return next(self.stream)

    if PY2:
        next = __next__  # pragma: no cover
        del __next__  # pragma: no cover

    def scan_until(self, pred):
        return self.scan_while(invert(pred))

    def skip_until(self, pred):
        consume(self.scan_until(pred))  # Scan and discard the results

    def scan_while(self, pred):
        while True:
            obj = self.stream.peek()
            if pred(obj):
                yield next(self.stream)
            else:
                break

    def skip_while(self, pred):
        consume(self.scan_while(pred))  # Scan and discard the results
