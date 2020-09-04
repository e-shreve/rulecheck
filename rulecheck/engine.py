import argparse
import copy
from decimal import Decimal
import glob
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import string
import subprocess
import sys
import traceback
import typing

# 3rd party imports
from lxml import etree as ET

# Local imports
from rulecheck.rule import Rule
from rulecheck.rule import LogType
from rulecheck.rule import LogFilePosition
from rulecheck import __version__

#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes

#################################################
##
## Logging Related Code
##
#################################################


class IgnoreFileEntry:
    """ Parses a line (string) into the members of an ignore entry from an ignore file.
        Always check is_valid() before using any of the getters on the object.
    """
    def __init__(self, line:str):
        self._valid = False
        self._line_num = -1
        self._col_num = -1
        self._hash = "NOHASH"

        parts = line.split(sep=': ')

        if len(parts) < 4:
            return

        # First value on line must be hash
        hash_part = parts[0].strip()
        if len(hash_part) == 32 and all(c in string.hexdigits for c in hash_part):
            self._hash = hash_part
        else:
            return

        # Second value on line must be the filename with optional line and col information
        file_info = parts[1]
        file_info_parts = file_info.rsplit(':',2)
        self._set_file_info(file_info_parts)

        if not self._set_log_type(parts[2]):
            return

        self._rule_name = parts[3]

        if len(parts) - 1 == 4:
            self._message = parts[4]
        else:
            self._message = ': '.join(parts[4:])

        self._valid = True

    def _set_file_info(self, file_info_parts) -> bool:
        if len(file_info_parts) >= 3:
            if file_info_parts[1].isdigit():
                if file_info_parts[2].isdigit():
                    self._col_num = int(file_info_parts[2])
                    self._line_num = int(file_info_parts[1])
                    self._file_name = file_info_parts[0]
            elif file_info_parts[2].isdigit():
                self._line_num = int(file_info_parts[2])
                self._file_name = file_info_parts[0] + ":" + file_info_parts[1]
            else:
                self._file_name = file_info_parts[0] + ":" + file_info_parts[1] + ":" + \
                                  file_info_parts[2]
        elif len(file_info_parts) == 2:
            if file_info_parts[1].isdigit():
                self._line_num = int(file_info_parts[1])
                self._file_name = file_info_parts[0]
            else:
                self._file_name = file_info_parts[0] + ":" + file_info_parts[1]
        else:
            self._file_name = file_info_parts[0]

        return True

    def _set_log_type(self, part:str) -> bool:
        if part == "ERROR":
            self._log_type = LogType.ERROR
            return True
        if part == "WARNING":
            self._log_type = LogType.WARNING
            return True

        return False

    def print(self):
        """Print string representation of the ignore file entry."""
        print("h: " + self.get_hash() + " f: " + self.get_file_name()
              + " l,c: "
              + str(self.get_line_num()) + ","
              + str(self.get_col_num()) + " t: "
              + str(self.get_log_level()) + " r: "
              + self.get_rule_name()
              + " m: " + self.get_message())

    def get_hash(self) -> str:
        return self._hash

    def get_file_name(self):
        return self._file_name

    def get_line_num(self) -> int:
        return self._line_num

    def get_col_num(self):
        return self._col_num

    def get_rule_name(self):
        return self._rule_name

    def get_log_level(self):
        return self._log_type

    def get_message(self):
        return self._message

    def is_valid(self) -> bool:
        return self._valid



class IgnoreFilter:
    """ Used to filter log messages. """
    def __init__(self, ignore_list_file_handle:typing.TextIO, verbose:bool):
        self._ignore_list_file_handle = ignore_list_file_handle
        self._rule_ignores = {}
        self._verbose = verbose

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)


    def init_filter(self, file_name:str):
        self._rule_ignores.clear()

        try:
            if self._ignore_list_file_handle:
                self._ignore_list_file_handle.seek(0)
                for line in self._ignore_list_file_handle:
                    entry = IgnoreFileEntry(line)

                    if entry.is_valid() and \
                       str( pathlib.Path(entry.get_file_name()).as_posix() ) == \
                       str(pathlib.Path(file_name).as_posix()):
                        rule_name = entry.get_rule_name()
                        if rule_name not in self._rule_ignores:
                            self._rule_ignores[rule_name] = []

                        self._rule_ignores[rule_name].append(IgnoreEntry(entry.get_hash(),
                                                                         entry.get_line_num(),
                                                                         entry.get_line_num()))

        except Exception as exc:  #pylint: disable=broad-except
            print("Failure while checking ignore list. Run with verbose mode for more information.")
            self.print_verbose("Exception on parsing ignore list: " + str(exc))
            self.print_verbose(traceback.format_exc())

    def disable(self, rule_name:str, line_num:int):
        if rule_name not in self._rule_ignores:
            self._rule_ignores[rule_name] = []

        self._rule_ignores[rule_name].append(IgnoreEntry('*', line_num, line_num))

    def is_filtered(self, rule_name:str, line_num:int, line_hash:hashlib.md5) -> bool:
        """ Returns True if the violation should not be logged """

        if '*' in self._rule_ignores:
            for ignore in self._rule_ignores['*']:
                if ignore.is_active():
                    if ignore.get_first() <= line_num <= ignore.get_last():
                        if ignore.get_hash() == '*' or ignore.get_hash() == str(line_hash):
                            ignore.mark_use()
                            return True

        if rule_name in self._rule_ignores:
            for ignore in self._rule_ignores[rule_name]:
                if ignore.is_active():
                    if ignore.get_first() <= line_num <= ignore.get_last():
                        if ignore.get_hash() == '*' or ignore.get_hash() == str(line_hash):
                            ignore.mark_use()
                            return True
        return False

class IgnoreEntry:
    """ IgnoreEntries are like ranges, except that:
        * The end value is inclusive, and thus called 'last'
        * The last value can be 'Inf' for infinite
        * They hold a hash value

        Also, the start value is referred to as start.

        The various comparison operators are overridden in ways that support the use of
        IgnoreEntries for the purpose of disabling logging of rules over certain line ranges.
        Their operation may not be directly intuitive.
    """
    def __init__(self, line_hash:str, first, last):
        self._first = Decimal(first)
        self._last = Decimal(last)
        self._hash = line_hash
        self._is_active = True


    def get_first(self) -> Decimal:
        return self._first

    def get_last(self) -> Decimal:
        return self._last

    def get_hash(self) -> str:
        return self._hash

    def is_active(self) -> bool:
        return self._is_active

    def mark_use(self):
        if self.get_hash() != '*':
            self._is_active = False

    def __lt__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() < key.get_first()
        return self.get_first() < key

    def __le__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() <= key.get_first()
        return self.get_first() <= key

    def __gt__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() > key.get_first()
        return self.get_first() > key

    def __ge__(self, key):
        """ Compare is done against the first value of the set only. """
        if isinstance(key, IgnoreEntry):
            return self.get_first() >= key.get_first()
        return self.get_first() >= key

    def __eq__(self, key):
        """ To be equal, the first, last, and hash value must all be equal """
        if isinstance(key, IgnoreEntry):
            return self.get_first() == key.get_first() and self.get_last() == key.get_last() and \
                self.get_hash() == key.get_hash()
        return False

    def __ne__(self, key):
        return not self.__eq__(key)

class Logger:
    """ Class used to perform the logging.

    Holds logging settings and implements the logging function.

    """

    def __init__(self, tab_size:int, show_hash:bool, warnings_are_errors:bool,
                 ignore_filter:IgnoreFilter, verbose:bool):
        self._tabsize= tab_size
        self._show_hash = show_hash
        self._warnings_are_errors = warnings_are_errors
        self._ignore_filter = ignore_filter
        self._verbose = verbose
        self._total_warnings = 0
        self._total_errors = 0
        self._total_ignored_warnings = 0
        self._total_ignored_errors = 0

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)

    def get_tab_size(self) -> int:
        """ Tab size in spaces count. """
        return self._tabsize

    def warnings_are_errors(self) -> bool:
        """ If True, all warnings should be promoted to errors """
        return self._warnings_are_errors

    def show_hash(self) -> bool:
        """ If True, the hash of the line should be included in the log output """
        return self._show_hash

    def set_tab_size(self, tab_size:int):
        self._tabsize = tab_size

    def set_warnings_are_errors(self, warnings_are_errors:bool):
        self._warnings_are_errors = warnings_are_errors

    def set_show_hash(self, show_hash:bool):
        self._show_hash = show_hash

    def increment_warnings(self):
        if self.warnings_are_errors():
            self.increment_errors()
        else:
            self._total_warnings += 1

    def increment_errors(self):
        self._total_errors += 1

    def increment_ignored_warnings(self):
        if self.warnings_are_errors():
            self.increment_ignored_errors()
        else:
            self._total_ignored_warnings += 1

    def increment_ignored_errors(self):
        self._total_ignored_errors += 1

    def get_warning_count(self) -> int:
        return self._total_warnings

    def get_error_count(self) -> int:
        return self._total_errors

    def get_ignored_warning_count(self) -> int:
        return self._total_ignored_warnings

    def get_ignored_error_count(self) -> int:
        return self._total_ignored_errors

    def log_violation(self, log_type:LogType, pos:LogFilePosition, msg:str,
                      include_indentation:bool, file_name:str, rule_name:str, source_lines:[str]):
        """Log function for violations

        Each violation is logged as follows (with items in [] optional based on logging settings:
        [hash of line]:filename:[line]:[col]:LogType:Rule Name:Log Message

        Each element is separated by a colon, ':'. If an optional part is not printed then the
        separator for that part is also not printed.

        The filename is the filename as opened, and thus may include a relative path.
        The position information, line and column number are provided if the values provided via the
          'pos' parameter are greater than zero.
        The LogType is either the string "ERROR" or "WARNING".
        The Rule Name is the same name of a rule as specified in a rule config file.
            Note that rules can be instantiated more than once and will have the same name.

        """

        # Adjust log type if user specified all warnings to be errors
        # But keep original log type for use in hash.
        adjusted_log_type = log_type

        if log_type == LogType.WARNING and self.warnings_are_errors():
            adjusted_log_type = LogType.ERROR

        log_msg = ""

        # Use posix form for hash calculation for consistency across OSes.
        file_name_posix = str(pathlib.Path(file_name).as_posix())
        log_hash = -1
        if pos.line > 0 and pos.line < len(source_lines):
            line_text = source_lines[pos.line-1]
            #print ("log against line text: " + line_text)
            if not include_indentation:
                line_text = line_text.lstrip()
            hash_input = file_name_posix + rule_name + log_type.name + line_text
            log_hash = hashlib.md5((hash_input).encode('utf-8')).hexdigest()
        else:
            hash_input = file_name_posix + rule_name + log_type.name
            log_hash = hashlib.md5((hash_input).encode('utf-8')).hexdigest()

        if not self._ignore_filter or not \
           self._ignore_filter.is_filtered(rule_name, pos.line, log_hash):

            if self.show_hash():
                log_msg = log_msg + log_hash + ": "

            log_msg = log_msg + file_name + ":"

            if pos.line > 0:
                log_msg = log_msg + str(pos.line) + ":"
            if pos.col > 0:
                log_msg = log_msg + str(pos.col) + ":"

            log_msg = log_msg + " "

            log_msg = log_msg + adjusted_log_type.name + ": " + rule_name + ": " + \
                      msg.expandtabs(self.get_tab_size())
            print(log_msg)

            if adjusted_log_type == LogType.ERROR:
                self.increment_errors()
            else:
                self.increment_warnings()
        else:
            if adjusted_log_type == LogType.ERROR:
                self.increment_ignored_errors()
            else:
                self.increment_ignored_warnings()

#################################################
##
## SrcML Management
##
#################################################

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

        srcml_cmd = [self._srcml_bin]
        srcml_cmd.extend(self._srcml_args)

        srcml_cmd.extend(["--language", self._srcml_ext_mappings[file_extension]])
        srcml_cmd.append(file_name)

        self.print_verbose("Calling srcml: " + " ".join(srcml_cmd))

        child = subprocess.Popen(srcml_cmd, shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        stdout, stderr = child.communicate()

        if child.returncode != 0:
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

class RuleManager:

    def __init__(self, logger:Logger, ignore_filter:IgnoreFilter, verbose:bool):
        self._rules_dict = {}
        self.current_rule_name = "rulecheck"
        self._verbose = verbose
        self._logger_ref = logger
        self._ignore_filter = ignore_filter

    def print_verbose(self, message:str):
        if self._verbose:
            print(message)

    def enable_verbose(self):
        self._verbose = True

    def _add_rule_paths(self, rule_paths):
        if rule_paths:
            for rule_path in rule_paths:
                rule_path = str(pathlib.Path(rule_path).absolute())
                if os.path.isdir(rule_path):
                    try:
                        sys.path.index(rule_path)
                    except ValueError:
                        # Only add if it wasn't already in the path
                        self.print_verbose("Adding to sys.path: " + rule_path)
                        sys.path.append(rule_path)
                else:
                    print("Rule path not found: " + rule_path)

    def _load_rule_set(self, rule_set):
        rules_loaded = list()

        for rule in rule_set['rules']:
            try:
                rule_full_name = rule['name']
                # The class name must be the same as the last part of the module name
                rule_class_name = rule_full_name.rpartition(".")[-1]

                if rule['name'] not in sys.modules:
                    __import__(rule_full_name)

                settings = {}
                if 'settings' in rule:
                    settings = rule['settings']

                rule_object = getattr(sys.modules[rule_full_name], rule_class_name)(settings)

                if rule_full_name not in self._rules_dict:
                    self._rules_dict[rule_full_name] = []
                    self._rules_dict[rule_full_name].append(rule_object)
                else:
                    identical_rule_exists = False
                    for loaded_rule in self._rules_dict[rule_full_name]:
                        if loaded_rule.get_settings() == rule_object.get_settings():
                            identical_rule_exists = True

                    if not identical_rule_exists:
                        self._rules_dict[rule_full_name].append(rule_object)

                rule_location = os.path.abspath(rule_full_name)

                rules_loaded.append(rule_location)

            except Exception as exc:  #pylint: disable=broad-except
                print("Could not load rule: " + rule_full_name)
                print("Exception on attempt to load rule: " + str(exc))

        return rules_loaded

    def load_rules(self, config_files, rule_paths):
        """Loads all rules specified in the json configuration files."""

        self._add_rule_paths(rule_paths)

        for config_file in config_files:
            try:
                with open(config_file) as file_stream:
                    rule_set = json.load(file_stream)

                rules_loaded = self._load_rule_set(rule_set)

                seperator = '\n  '
                self.print_verbose("From " + config_file + " loaded rules: " + seperator + \
                            seperator.join(rules_loaded))
            except Exception:  #pylint: disable=broad-except
                print("Could not open config file: " + config_file)

    def activate_all_rules(self):
        for name, rule_array in self._rules_dict.items():
            for rule in rule_array:
                try:
                    rule.set_active()
                except Exception as exc:  #pylint: disable=broad-except
                    log_rule_exception("Exception thrown while activating rule. See stderr.",
                                       exc, name)

    def visit_file_open_all_active_rules(self, file_name:str):
        for name, rule_array in self._rules_dict.items():
            self.current_rule_name = name
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_file_open(rule, file_name)
                except Exception as exc:  #pylint: disable=broad-except
                    log_rule_exception("Exception thrown while calling is_active(). See stderr.",
                                       exc, name)

    def visit_file_open(self, rule:Rule, file_name:str):
        """Calls visit_file_open(pos, file_name) on any rule providing that method."""

        meth = getattr(rule, 'visit_file_open', None)
        if meth is not None:
            try:
                meth(LogFilePosition(-1, -1), file_name)
            except Exception as exc:  #pylint: disable=broad-except
                log_rule_exception("Exception thrown while calling visit_file_open. See stderr.",
                    exc, self.current_rule_name)

    def visit_file_close_all_active_rules(self, file_name:str):
        for name, rule_array in self._rules_dict.items():
            self.current_rule_name = name
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_file_close(rule, file_name)
                except Exception as exc:  #pylint: disable=broad-except
                    log_rule_exception("Exception thrown while calling is_active(). See stderr.",
                                       exc, name)

    def visit_file_close(self, rule:Rule, file_name:str):
        """Calls visit_file_close(pos, file_name) on any rule providing that method."""

        meth = getattr(rule, 'visit_file_close', None)
        if meth is not None:
            try:
                meth(LogFilePosition(-1, -1), file_name)
            except Exception as exc:  #pylint: disable=broad-except
                log_rule_exception("Exception thrown while calling visit_file_close. See stderr.",
                    exc, self.current_rule_name)

    def visit_file_line_all_active_rules(self, line_num:int, line:str):
        for name, rule_array in self._rules_dict.items():
            self.current_rule_name = name
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_file_line(rule, line_num, line)
                except Exception as exc:  #pylint: disable=broad-except
                    log_rule_exception("Exception thrown while calling is_active(). See stderr.",
                                       exc, name)

    def visit_file_line(self, rule:Rule, line_num:int, line:str):
        """Calls visit_file_line(pos, line) on any rule providing that method."""

        try:
            meth = getattr(rule, 'visit_file_line', None)
            if meth is not None:
                meth(LogFilePosition(line_num, -1), line)
        except Exception as exc:  #pylint: disable=broad-except
            log_rule_exception("Exception thrown while calling visit_file_line. See stderr.",
                exc, self.current_rule_name)

    def check_for_rule_disable(self, line_num:int, line:str):
        match = re.search(r'(NORCNEXTLINE|NORC)\(([^)]+)', line)
        if match:
            if match.group(1) == 'NORCNEXTLINE':
                line_num += 1

            rules = match.group(2).split(',')

            for rule in rules:
                self._ignore_filter.disable(rule.strip(), line_num)

    def visit_file_lines(self, from_line:int, to_line:int, source_lines):
        """Calls visit_file_line(pos, line) once for each line from 'from_line' to
           'to_line' (inclusive) on any rule providing the visit_file_line method.
        """

        # Guard against going beyond end of source_lines array is needed to handle a bug in srcml.
        # See rulecheck's defect #22 (github) for details.
        for line_num in range(from_line, min(to_line+1, len(source_lines)+1)):
            # -1 to line_num to convert to array's 0 based index.
            self.check_for_rule_disable(line_num, source_lines[line_num-1])
            self.visit_file_line_all_active_rules(line_num, source_lines[line_num-1])

    @staticmethod
    def strip_namespace(full_tag_name:str) -> str:
        """Removes namespace portion of xml tag name"""
        return re.sub('{.*}', '', full_tag_name)

    def visit_xml_all_active_rules(self, pos:LogFilePosition, node: ET.Element, event):
        tag_name = RuleManager.strip_namespace(node.tag)

        for name, rule_array in self._rules_dict.items():
            self.current_rule_name = name
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_xml(rule, pos, node, tag_name, event)
                except Exception as exc:  #pylint: disable=broad-except
                    log_rule_exception("Exception thrown while calling is_active(). See stderr.",
                                       exc, name)

    def visit_xml(self, rule:Rule, pos:LogFilePosition, node: ET.Element, tag_name:str, event):
        # First look for visit methods that include the tag name
        # Note: parsing xml, the visit methods must be named
        # visit_xml_nodename_start|end.
        # The use of xml_ at the start avoids collisions with visit_file_open and
        # visit_file_line should a <file_open>, <file_close> or <file_line> tag be
        # encountered. Since the XML standard does not allow nodenames to start
        # with 'xml' we also don't have to be concerned with a collision between
        # <xml_name> and <name> since the former is not allowed.
        meth = getattr(rule, 'visit_xml_'+tag_name+'_'+event, None)
        if meth is not None:
            try:
                meth(copy.copy(pos), node)
            except Exception as exc:  #pylint: disable=broad-except
                log_rule_exception("Exception thrown while calling " + \
                                   'visit_xml_' + tag_name + '_' + \
                                   event + ". See stderr.", exc, self.current_rule_name)
        else:
            # Location of 'xml' in name is different to avoid problems if the
            # xml document has an <any_other_xml_element> tag.
            meth = getattr(rule, 'visit_any_other_xml_element_' + event, None)
            if meth is not None:
                try:
                    meth(copy.copy(pos), node)
                except Exception as exc:  #pylint: disable=broad-except
                    log_rule_exception("Exception thrown while calling "
                                       + 'visit_any_other_xml_element_' + event
                                       + ". See stderr.", exc, self.current_rule_name)



    def run_rules_on_file(self, file_name:str, source_lines:[str], srcml:Srcml):
        self._ignore_filter.init_filter(file_name)

        self.activate_all_rules()

        next_line = 1
        element_line = 1

        self.visit_file_open_all_active_rules(file_name)

        srcml_bytes = srcml.get_srcml(file_name)

        if srcml_bytes is not None:
            root = ET.parse(io.BytesIO(srcml_bytes))
            context = ET.iterwalk(root, events=("start", "end"))

            for event,elem in context:
                srcml_xml_line = srcml.get_xml_line(elem, event)

                if srcml_xml_line > element_line:
                    element_line = srcml_xml_line

                if elem.tag == "{http://www.srcML.org/srcML/src}unit":
                    if event == "start":
                        pos = LogFilePosition(1, -1)
                        self.visit_xml_all_active_rules(pos, elem, event)
                    if event == "end":
                        self.visit_file_lines(next_line, len(source_lines), source_lines)
                        next_line = len(source_lines) + 1
                        # unit tag doesn't have position encoding but it is always at
                        # the end. Thus, make its reported line the last line of the file.
                        pos = LogFilePosition(len(source_lines), -1)
                        self.visit_xml_all_active_rules(pos, elem, event)
                else:
                    # Process line visitors of any lines not visited yet up to
                    # and including the line this element is on.
                    self.visit_file_lines(next_line, element_line, source_lines)
                    next_line = element_line + 1

                    srcml_pos_line, srcml_pos_col = srcml.get_pos_row_col(elem, event)
                    pos = LogFilePosition(srcml_pos_line, srcml_pos_col)
                    self.visit_xml_all_active_rules(pos, elem, event)
        else:
            self.visit_file_lines(1, len(source_lines), source_lines)

        self.visit_file_close_all_active_rules(file_name)

        self.current_rule_name = "rulecheck"

class FileManager:
    def __init__(self, rules:RuleManager, srcml:Srcml, verbose:bool):
        self._rules = rules
        self._srcml = srcml
        self.current_file_name = ""
        self.source_lines = [""]
        self._file_count = 0
        self.verbose = verbose

    def print_verbose(self, message:str):
        if self.verbose:
            print(message)

    def process_files(self, globs:[str]):

        if (not globs is None) and len(globs) == 1 and globs[0] == "-":
            for source in sys.stdin:
                self.process_source(source.rstrip())

        elif (not globs is None) and len(globs) > 0:
            for glob_str in globs:
                for source in glob.iglob(glob_str, recursive=True):
                    self.process_source(source)

    def process_source(self, source:str):
        self.current_file_name = source
        try:
            file_stream = open(source, 'r', newline='')
            try:
                self.print_verbose("Opened file for checking: " + source)
                self.source_lines=file_stream.readlines()
                self._file_count += 1
                self._rules.run_rules_on_file(source, self.source_lines, self._srcml)
            finally:
                file_stream.close()
        except (IOError, OSError) as exc:
            log_file_exception("Could not open file! See stderr.", exc, source)


    def get_file_count(self) -> int:
        return self._file_count



#################################################
##
## Globals
##
#################################################
FILE_MANAGER: FileManager
RULE_MANAGER: RuleManager
LOGGER: Logger
VERBOSE_ENABLED: bool

def print_verbose(message:str):
    global VERBOSE_ENABLED
    if VERBOSE_ENABLED:
        print(message)


def print_summary(logger:Logger):
    global FILE_MANAGER
    print("Total Files Checked: " + str(FILE_MANAGER.get_file_count()))
    print("Total Warnings (ignored): " + str(logger.get_warning_count()) + "("
          + str(logger.get_ignored_warning_count()) + ")")
    print("Total Errors (ignored): " + str(logger.get_error_count()) + "("
          + str(logger.get_ignored_error_count()) + ")")



def log_violation_wrapper(log_type:LogType, pos:LogFilePosition, msg:str,
                          include_indentation:bool):
    """ Wrapper used by Rule objects.

    This procedure handles gluing together the state of the file currently being checked with the
    violation information provided by a rule. This wrapper avoids passing a full object to the Rules
    and thus avoids Rules calling other methods on the logging object. In addition, by providing the
    file name, rule name, and source lines here, the rule classes don't have to include the
    information. This cuts down on what would be boilerplate code for each rule.
    """

    global LOGGER
    global RULE_MANAGER
    global FILE_MANAGER

    LOGGER.log_violation(log_type, pos, msg, include_indentation, FILE_MANAGER.current_file_name,
                         RULE_MANAGER.current_rule_name, FILE_MANAGER.source_lines)

def log_rule_exception(msg:str, exc:Exception, rule_name:str):
    """ Wrapper used to log issues when working with a rule.
    """

    global LOGGER
    global FILE_MANAGER

    LOGGER.log_violation(LogType.ERROR, LogFilePosition(-1,-1), msg, False, "rulecheck",
                         rule_name, [])
    print(exc, sys.stderr)

def log_file_exception(msg:str, exc:Exception, file_name:str):
    """ Wrapper used to log issues when working with a file.
    """

    global LOGGER
    global FILE_MANAGER

    LOGGER.log_violation(LogType.ERROR, LogFilePosition(-1,-1), msg, False, file_name,
                         "rulecheck", [])
    print(exc, file=sys.stderr)

def create_parser():
    parser = argparse.ArgumentParser()
    parser.description = "Tool to run rules on code."
    parser.add_argument("-c", "--config",
                        help="""config file. Specify the option multiple times to specify
                                multiple config files.""",
                        required=True, nargs=1, action="extend", type=str)
    parser.add_argument("-x", "--extensions",
                        help="extensions to include when traversing provided source path(s)",
                        required=False, nargs=1, action="extend", type=str)
    parser.add_argument("-r", "--rulepaths",
                        help="""path to rules. Specify the option multiple times to specify
                                multiple paths.""",
                        nargs=1, action="extend", type=str)
    parser.add_argument("-g", "--generatehashes",
                        help="output messages with hash values used for ignore files",
                        action="store_true")
    parser.add_argument("--srcml", help="path to srcml, required if srcml not in path",
                        nargs=1, type=str)
    parser.add_argument("--register-ext",
                        help="""specify extension to language mappings used with srcml.
                                --register-ext EXT=LANG""",
                        nargs=1, action="extend", type=str)
    # The srmclargs value must be quoted and start with a leading space because of this bug in
    # argparse: https://bugs.python.org/issue9334
    parser.add_argument("--srcmlargs",
                        help="""additional arguments for srcml. MUST BE QUOTED AND START WITH A
                              LEADING SPACE. Note that rulecheck will automatically handle the
                              --language option based on --register-ext parameters to rulecheck.
                              Also, --tabs has its own dedicated option.""",
                        default="--position --cpp-markup-if0", nargs=1, type=str)
    parser.add_argument("--tabs", help="number of spaces used for tabs", default=4, type=int)
    parser.add_argument("--Werror", help="all warnings will be promoted to errors",
                        action="store_true", default=False)
    parser.add_argument("-i", "--ignorelist", help="file with rule violations to ignore",
                        default = "", type=str)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s '+ __version__)
    parser.add_argument("sources",
                        help="""globs source file(s) and/or path(s). ** can be used to represent any
                                number of nested (non-hidden) directories. If '-' is specified,
                                file list is read from stdin.""",
                        nargs='*', action="append", type=str)

    return parser

def create_srcml(args) -> Srcml:
    if args.srcml:
        srcml_bin = shutil.which('srcml', path=args.srcml)
    else:
        srcml_bin = shutil.which('srcml')

    if srcml_bin:
        print_verbose("srcml binary located at: " + srcml_bin)
    else:
        print("Could not locate srcml binary!")
        if args.srcml:
            print("srcml path was specified as: " + args.srcml)
        else:
            print("system path was searched")
        return None

    srcml_args = []
    if args.srcmlargs:
        srcml_args.extend(args.srcmlargs.split())

    if args.tabs:
        srcml_args.append("--tabs=" + str(args.tabs))

    return Srcml(srcml_bin, srcml_args, VERBOSE_ENABLED)

def rulecheck(args) -> int:
    """Run rule check using specified command line arguments. Returns exit value.
    0 = No errors, normal program termination.
    1 = Internal rulecheck error
    2 = At least one rule reported an error
    3 = At least one rule reported a warning but no rules reported an error
    """
    global LOGGER
    global RULE_MANAGER
    global FILE_MANAGER
    global VERBOSE_ENABLED

    VERBOSE_ENABLED = False
    if args.verbose:
        VERBOSE_ENABLED = True

    srcml = create_srcml(args)

    if srcml is None:
        return 1

    if args.register_ext:
        for register_ext in args.register_ext:
            regext = register_ext.split("=")
            if len(regext) == 2:
                srcml.add_ext_mapping('.'+regext[0], regext[1])
            else:
                print("Bad --register-ext option: " + register_ext)
                return 1

        print_verbose("Extension to language mappings for srcml are: " + \
                      str(srcml.get_ext_mappings()))

    ignore_list_file_handle = None
    if args.ignorelist:
        print_verbose("Ignore list specified: " + args.ignorelist)
        ignore_list_file_handle = open(args.ignorelist, "r")

    ignore_filter = IgnoreFilter(ignore_list_file_handle, VERBOSE_ENABLED)

    LOGGER = Logger(args.tabs, args.generatehashes, args.Werror, ignore_filter, VERBOSE_ENABLED)

    Rule.set_logger(log_violation_wrapper)

    RULE_MANAGER = RuleManager(LOGGER, ignore_filter, VERBOSE_ENABLED)

    RULE_MANAGER.load_rules(args.config, args.rulepaths)

    FILE_MANAGER = FileManager(RULE_MANAGER, srcml, VERBOSE_ENABLED)

    # Flatten list of lists in args.sources and pass to process_files
    FILE_MANAGER.process_files([item for sublist in args.sources for item in sublist])


    if ignore_list_file_handle:
        ignore_list_file_handle.close()

    if VERBOSE_ENABLED:
        print_summary(LOGGER)

    if LOGGER.get_error_count() > 0:
        return 2
    if LOGGER.get_warning_count() > 0:
        return 3

    return 0

def main():
    parser = create_parser()
    args = parser.parse_args()
    result = rulecheck(args)
    sys.exit(result)
