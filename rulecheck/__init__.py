import sys

__version__ = '0.6.0'

if sys.version_info.major < 3:
    sys.exit('Python < 3.6 is unsupported.')
if sys.version_info.minor < 6:
    sys.exit('Python < 3.6 is unsupported.')
