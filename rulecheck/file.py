'''
Created on Sep 5, 2020

@author: Erik
'''
import io
# 3rd party imports
from lxml import etree as ET

class File():
    def __init__(self, file_name:str, lines, raw_srcml_bytes):
        self._lines = lines
        self._file_name = file_name
        self._raw_srcml_bytes = raw_srcml_bytes
        self._srcml_etree_root = None

        if self._raw_srcml_bytes is not None:
            self._srcml_etree_root = ET.parse(io.BytesIO(self._raw_srcml_bytes))

    def get_lines(self):
        return self._lines

    def get_name(self):
        return self._file_name

    def get_raw_srcml_bytes(self):
        return self._raw_srcml_bytes

    def get_srcml_etree_root(self):
        return self._srcml_etree_root
