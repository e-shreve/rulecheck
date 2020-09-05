import sys

__version__ = '0.5.5.0'

if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is unsupported.')
