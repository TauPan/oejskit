import sys

def any_browser():
    res = ['firefox']
    if sys.platform == 'win32':
        res.append('iexplore')
    elif sys.platform == 'darwin':
        res.append('safari')
    return res
    
