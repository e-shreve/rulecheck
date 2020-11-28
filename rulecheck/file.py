"""
    File Module

    Contains the File class which wraps information and content about a source file to be checked.
"""

import io
# 3rd party imports
from lxml import etree as ET

class File():
    """Wraps source file contents and srcml bytes of those contents."""

    def __init__(self, file_name:str, lines, raw_srcml_bytes):
        self._lines = lines
        self._file_name = file_name
        self._raw_srcml_bytes = raw_srcml_bytes
        self._srcml_etree_root = None

        if self._raw_srcml_bytes:
            self._srcml_etree_root = ET.parse(io.BytesIO(self._raw_srcml_bytes))

    def get_lines(self):
        """Returns the source/text lines of the file."""
        return self._lines

    def get_name(self):
        """Returns the file name."""
        return self._file_name

    def get_raw_srcml_bytes(self):
        """Returns the raw srcml byte data."""
        return self._raw_srcml_bytes

    def get_srcml_etree_root(self):
        """Returns the etree root of the srcml xml."""
        return self._srcml_etree_root
