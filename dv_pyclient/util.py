'''Assorted utility methods for dealing with python'''

def to_str_none(val):
    '''
    Converts val to a string via str, returns None if val is None

    :param s: Any - Value to convert
    :return: String?
    '''
    if val is None:
        return None
    return str(val)
