'''Helper functions'''

def chunks(lst, n):
    """Yield successive n-sized chunks from lst, in order.

    >>> chunks(range(5), 2) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    <generator object chunks at 0x...>

    >>> num_chunks = chunks(range(10), 3)
    >>> num_chunks.next()
    [0, 1, 2]
    >>> num_chunks.next()
    [3, 4, 5]
    >>> num_chunks.next()
    [6, 7, 8]
    >>> num_chunks.next()
    [9]

    >>> blocks = ["brick", "cobblestone", "sandstone", "stone", "clay", "dirt"]
    >>> block_chunks = chunks(blocks, 2)
    >>> block_chunks.next()
    ['brick', 'cobblestone']
    """

    for i in xrange(0, len(lst), n):
        yield lst[i:i + n]
