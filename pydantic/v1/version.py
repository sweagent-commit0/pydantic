__all__ = ('compiled', 'VERSION', 'version_info')
VERSION = '1.10.17'
try:
    import cython
except ImportError:
    compiled: bool = False
else:
    try:
        compiled = cython.compiled
    except AttributeError:
        compiled = False