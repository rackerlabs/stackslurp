def chunks(lst, n):
    """ Yield successive n-sized chunks from lst.
    """
    for i in xrange(0, len(lst), n):
        yield lst[i:i + n]
