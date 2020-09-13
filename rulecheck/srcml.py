#################################################
##
## SrcML Management
##
#################################################


import os
import shlex
import string
import subprocess
import sys

# 3rd party imports
from lxml import etree as ET
from xxsubtype import bench

#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes

class Srcml:
    """ Class for managing srcml options and obtaining srcml output. """

    def __init__(self, binary:str, args:[str], verbose:bool):
        self._srcml_bin = binary
        self._srcml_args = args
        # These mappings align with
        # the default mappings of srcml
        # https://github.com/srcML/srcML/blob/master/src/libsrcml/language_extension_registry.cpp
        self._srcml_ext_mappings = {".c":"C",
                               ".h":"C",
                               ".i":"C",
                               ".cpp":"C++",
                               ".CPP":"C++",
                               ".cp":"C++",
                               ".hpp":"C++",
                               ".cxx":"C++",
                               ".hxx":"C++",
                               ".cc":"C++",
                               ".hh":"C++",
                               ".c++":"C++",
                               ".h++":"C++",
                               ".C":"C++",
                               ".H":"C++",
                               ".tcc":"C++",
                               ".ii":"C++",
                               ".java":"Java",
                               ".aj":"Java",
                               ".cs":"C#"
                              }
        self._verbose = verbose

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)

    def add_ext_mapping(self, ext:str, language:str):
        self._srcml_ext_mappings[ext] = language

    def can_read_extension(self, ext:str) -> bool:
        return ext in self._srcml_ext_mappings

    def get_ext_mappings(self):
        return self._srcml_ext_mappings.copy()

    def get_srcml(self, file_name:str) -> bytes:

        file_extension = os.path.splitext(file_name)[1]

        if not file_extension or not self.can_read_extension(file_extension):
            return None



        # Build up command and arguments. Use shell for posix (linux/mac), no shell for Windows.
        shell = False
        srcml_cmd = [self._srcml_bin]

        if os.name == 'posix':
            shell = True

            # Add quotes around filenames/paths with whitespace.
            if True in [c in file_name for c in string.whitespace]:
                if not (file_name.startswith(r'"') or file_name.startswith(r"'")):
                    file_name = r"'" + file_name + r"'"

            srcml_cmd = self._srcml_bin + " " + " ".join(self._srcml_args) + \
                        " --language " + self._srcml_ext_mappings[file_extension] + \
                        " " + file_name

            self.print_verbose("Calling srcml: " + srcml_cmd)
        elif os.name == 'nt':
            srcml_cmd.extend(self._srcml_args)
            srcml_cmd.extend(["--language", self._srcml_ext_mappings[file_extension]])
            srcml_cmd.append(file_name)
            self.print_verbose("Calling srcml: " + " ".join(srcml_cmd))
        else:
            raise ValueError('Unexpected or unsupported OS: ' + os.name)


        child = subprocess.Popen(srcml_cmd, shell=shell,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        stdout, stderr = child.communicate()

        if child.returncode != 0 or stderr:
            print("error calling srcml, return code: " + str(child.returncode) + " stderr: ")
            print(stderr.decode(sys.stderr.encoding))
            return None

        return stdout

    @staticmethod
    def get_pos_row_col(element : ET.Element, event:str):
        """Returns [row,col] from srcML position start attribute or [-1,-1] it the
        attribute is not present"""

        row_num = -1
        col_num = -1
        if event == "start" and "{http://www.srcML.org/srcML/position}start" in element.attrib:
            srcml_pos = element.attrib["{http://www.srcML.org/srcML/position}start"].split(':')
            row_num = int(srcml_pos[0])
            col_num = int(srcml_pos[1])
        elif event == "end" and "{http://www.srcML.org/srcML/position}end" in element.attrib:
            srcml_pos = element.attrib["{http://www.srcML.org/srcML/position}end"].split(':')
            row_num = int(srcml_pos[0])
            col_num = int(srcml_pos[1])

        return [row_num, col_num]

    @staticmethod
    def get_xml_line(element : ET.Element, event:str):
        """Returns line number within the xml stream where 'element' starts or ends"""

        line_num = -1
        content = "start"

        if event == "start":
            # Subtract one because first xml line in the srcml is the XML declaration
            line_num = element.sourceline - 1
        elif event == "end":
            # Based on https://stackoverflow.com/a/47903639, by RomanPerekhrest
            line_num = element.sourceline - 1
            content = ET.tostring(element, method="text",  with_tail=False)
            if content:
                # Using split("\n") because splitlines() will drop the last newline character
                line_num += (len(content.decode('utf8').split("\n")) - 1)

        return line_num
