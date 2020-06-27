import argparse
import copy
import fileinput
import glob
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import typing

# 3rd party imports
from lxml import etree as ET

# Local imports
from rulecheck import rule
from rulecheck.rule import LogFilePosition


__version__ = '0.5'



#################################################
##
## Logging Related Code
##
#################################################


class Logger(object):
    """ Class used to perform the logging.

    Holds logging settings and implements the logging function.

    """

    def __init__(self, tab_size:int, show_hash:bool, warnings_are_errors:bool, ignore_list_file_handle:typing.TextIO, verbose:bool):
        self._tabsize= tab_size
        self._show_hash = show_hash
        self._warnings_are_errors = warnings_are_errors
        self._ignore_list_file_handle = ignore_list_file_handle
        self.verbose = verbose
        self._total_warnings = 0
        self._total_errors = 0


    def print_verbose(self, message:str):
        if self.verbose:
            print(message)

    def get_tab_size(self) -> int:
        """ Tab size in spaces count. """
        return self._tabsize

    def get_ignore_list_file_handle(self) -> typing.TextIO:
        return self._ignore_list_file_handle

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
            self._total_warnings += 1;

    def increment_errors(self):
        self._total_errors += 1;

    def get_warning_count(self) -> int:
        return self._total_warnings

    def get_error_count(self) -> int:
        return self._total_errors

    def log_violation(self, log_type:rule.LogType, pos:LogFilePosition, msg:str, include_indentation:bool, file_name:str, rule_name:str, source_lines:[str]):
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

        if log_type == rule.LogType.WARNING and self.warnings_are_errors() == True:
            adjusted_log_type = rule.LogType.ERROR

        log_msg = ""

        log_hash = -1
        if (pos.line > 0 and pos.line < len(source_lines)):
            line_text = source_lines[pos.line-1]
            #print ("log against line text: " + line_text)
            if not include_indentation:
                line_text = line_text.lstrip()
            log_hash = hashlib.md5((file_name + rule_name + log_type.name + line_text).encode('utf-8')).hexdigest()
        else:
            log_hash = hashlib.md5((file_name + rule_name + log_type.name).encode('utf-8')).hexdigest()

        if not self.is_in_ignore_list(log_hash, self.get_ignore_list_file_handle()):


            if (self.show_hash()):
                log_msg = log_msg + log_hash + ":"

            log_msg = log_msg + file_name + ":"

            if (pos.line > 0):
                log_msg = log_msg + str(pos.line) + ":"
            if (pos.col > 0):
                log_msg = log_msg + str(pos.col) + ":"

            log_msg = log_msg + adjusted_log_type.name + ":" + rule_name + ":" + msg.expandtabs(self.get_tab_size())
            print(log_msg)

            if adjusted_log_type == rule.LogType.ERROR:
                self.increment_errors()
            else:
                self.increment_warnings()

    def is_in_ignore_list(self, hash_to_check:hashlib.md5, ignore_list_file_handle) -> bool:
        """ Helper function for log_violation to determine if a violation is to be ignored. """

        result = False

        try:
            if ignore_list_file_handle:
                ignore_list_file_handle.seek(0)
                for line in ignore_list_file_handle:
                    if hash_to_check in line:
                        result = True
        except Exception as e:
            print("Failure while checking ignore list. Run with verbose mode on for more information.")
            self.print_verbose("Exception on parsing ignore list: " + str(e))

        return result


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
        self.verbose = verbose

    def print_verbose(self, message:str):
        if self.verbose:
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

        child = subprocess.Popen(srcml_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = child.communicate()

        if child.returncode != 0:
            print("error calling srcml, return code: " + str(child.returncode) + " stderr: ")
            print(stderr.decode(sys.stderr.encoding))
            return None

        return stdout

    def get_row_col(self, element : ET.Element, event:str):
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

class RuleManager:

    def __init__(self, verbose:bool):
        self._rules_dict = {}
        self.current_rule_name = "rulecheck"
        self.verbose = verbose

    def print_verbose(self, message:str):
        if self.verbose:
            print(message)

    def enable_verbose(self):
        self.verbose = True

    def load_rules(self, config_files, rule_paths):
        """Loads all rules specified in the json configuration files."""

        if rule_paths:
            for rp in rule_paths:
                rp = str(pathlib.Path(rp).absolute())
                if os.path.isdir(rp):
                    try:
                        sys.path.index(rp)
                    except ValueError:
                        # Only add if it wasn't already in the path
                        self.print_verbose("Adding to sys.path: " + rp)
                        sys.path.append(rp)
                else:
                    print("Rule path not found: " + rp)

        for config_file in config_files:
            try:
                with open(config_file) as f:
                    rule_set = json.load(f)

                rules_loaded = list()

                for r in rule_set['rules']:
                    try:
                        # The class name must be the same as the last part of the module name
                        rule_class_name = r['name'].rpartition(".")[-1]

                        if r['name'] not in sys.modules:
                            __import__(r['name'])

                        settings = {}
                        if 'settings' in r:
                            settings = r['settings']

                        ruleObj = getattr(sys.modules[r['name']], rule_class_name)(settings)

                        if r['name'] not in self._rules_dict:
                            self._rules_dict[r['name']] = []
                            self._rules_dict[r['name']].append(ruleObj)
                        else:
                            identical_rule_exists = False
                            for rule in self._rules_dict[r['name']]:
                                if rule.get_settings() == ruleObj.get_settings():
                                    identical_rule_exists = True

                            if not identical_rule_exists:
                                self._rules_dict[r['name']].append(ruleObj)

                        rule_location = os.path.abspath(r['name'])

                        rules_loaded.append(rule_location)

                    except Exception as e:
                        print("Could not load rule: " + r['name'])
                        print("Exception on attempt to load rule: " + str(e))

                seperator = '\n  '
                self.print_verbose("From " + config_file + " loaded rules: " + seperator + seperator.join(rules_loaded))
            except:
                print("Could not open config file: " + config_file)

    def activate_all_rules(self):
        for name, rule_array in self._rules_dict.items():
            for rule in rule_array:
                try:
                    rule.set_active()
                except Exception as e:
                    log_rule_exception("Exception thrown while activating rule. See stderr.", e, name)


    def visit_file_open(self, file_name:str):
        """Calls visit_file_open(pos, file_name) on any rule providing that method."""

        for name, rule_array in self._rules_dict.items():
                self.current_rule_name = name
                for rule in rule_array:
                    try:
                        if rule.is_active():
                            meth = getattr(rule, 'visit_file_open', None)
                            if meth is not None:
                                try:
                                    meth(LogFilePosition(-1, -1), file_name)
                                except Exception as e:
                                    log_rule_exception("Exception thrown while calling visit_file_open. See stderr.", e, name)
                    except Exception as e:
                        log_rule_exception("Exception thrown while calling is_active(). See stderr.", e, name)
                        

    def visit_file_close(self, file_name:str):
        """Calls visit_file_close(pos, file_name) on any rule providing that method."""

        for name, rule_array in self._rules_dict.items():
                self.current_rule_name = name
                for rule in rule_array:
                    try:
                        if rule.is_active():
                            meth = getattr(rule, 'visit_file_close', None)
                            if meth is not None:
                                try:
                                    meth(LogFilePosition(-1, -1), file_name)
                                except Exception as e:
                                    log_rule_exception("Exception thrown while calling visit_file_close. See stderr.", e, name)
                    except Exception as e:
                        log_rule_exception("Exception thrown while calling is_active(). See stderr.", e, name)

    def visit_file_line(self, line_num:int, line:str):
        """Calls visit_file_line(pos, line) on any rule providing that method."""

        for name, rule_array in self._rules_dict.items():
            self.current_rule_name = name
            for rule in rule_array:
                try:
                    if rule.is_active():
                        try:
                            meth = getattr(rule, 'visit_file_line', None)
                            if meth is not None:
                                meth(LogFilePosition(line_num, -1), line)
                        except Exception as e:
                            log_rule_exception("Exception thrown while calling visit_file_line. See stderr.", e, name)
                except Exception as e:
                    log_rule_exception("Exception thrown while calling is_active(). See stderr.", e, name)
                        
    def visit_file_lines(self, from_line:int, to_line:int, source_lines):
        """Calls visit_file_line(pos, line) once for each line from 'from_line' to 'to_line -1 '
           on any rule providing the visit_file_line method.
        """

        for line_num in range(from_line, to_line+1):
            # -1 to line_num to convert to array's 0 based index.
            self.visit_file_line(line_num, source_lines[line_num-1])

    def strip_namespace(self, fullTagName:str) -> str:
        """Removes namespace portion of xml tag name"""
        return re.sub('{.*}', '', fullTagName)

    def visit_xml(self, pos:LogFilePosition, node: ET.Element, event):

        tagName = self.strip_namespace(node.tag)

        for name, rule_array in self._rules_dict.items():
            self.current_rule_name = name
            for rule in rule_array:
                try:
                    if rule.is_active():
                        # First look for visit methods that include the tag name
                        # Note: parsing xml, the visit methods must be named visit_xml_nodename_start|end. 
                        # The use of xml_ at the start avoids collisions with visit_file_open and visit_file_line
                        # should a <file_open>, <file_close> or <file_line> tag be encountered. Since the XML standard
                        # does not allow nodenames to start with 'xml' we also don't have to be concerned with an
                        # collision between <xml_name> and <name> since the former is not allowed.
                        meth = getattr(rule, 'visit_xml_'+tagName+'_'+event, None)
                        if meth is not None:
                            try:
                                meth(copy.copy(pos), node)
                            except Exception as e:
                                log_rule_exception("Exception thrown while calling " + 'visit_xml_'+tagName+'_'+event + ". See stderr.", e, name)
                        else:
                            # Location of 'xml' in name is different to avoid problems if the
                            # xml document has an <any_other_xml_element> tag.
                            meth = getattr(rule, 'visit_any_other_xml_element_'+event, None)
                            if meth is not None:
                                try:
                                    meth(copy.copy(pos), node)
                                except Exception as e:
                                    log_rule_exception("Exception thrown while calling " + 'visit_any_other_xml_element_'+event + ". See stderr.", e, name)

                except Exception as e:
                    log_rule_exception("Exception thrown while calling is_active(). See stderr.", e, name)

    def run_rules_on_file(self, file_name:str, source_lines:[str], srcml:Srcml):

        self.activate_all_rules()

        next_line = 1
        element_line = 1

        self.visit_file_open(file_name)

        srcml_bytes = srcml.get_srcml(file_name)

        if srcml_bytes != None:
            context = ET.iterparse(io.BytesIO(srcml_bytes), events=("start", "end"))

            for event,elem in iter(context):
                line_num, col_num = srcml.get_row_col(elem, event)

                if line_num > element_line:
                    element_line = line_num

                if elem.tag == "{http://www.srcML.org/srcML/src}unit":
                    if event == "start":
                        pos = LogFilePosition(1, col_num)
                        self.visit_xml(pos, elem, event)
                    if event == "end":
                        self.visit_file_lines(next_line, len(source_lines), source_lines)
                        next_line = len(source_lines) + 1
                        # unit tag doesn't have position encoding but it is always at
                        # the end. Thus, make its reported line the last line of the file.
                        element_line = len(source_lines)

                        pos = LogFilePosition(element_line, col_num)
                        self.visit_xml(pos, elem, event)

                else:
                    # Process line visitors of any lines not visited yet up to
                    # and including the line this element is on.
                    self.visit_file_lines(next_line, element_line, source_lines)
                    next_line = element_line + 1


                    pos = LogFilePosition(element_line, col_num)
                    self.visit_xml(pos, elem, event)

        else:
            self.visit_file_lines(1, len(source_lines), source_lines)

        self.visit_file_close(file_name)

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

        if (not globs == None) and len(globs) == 1 and globs[0] == "-":
            for source in sys.stdin:
                self.process_source(source.rstrip())

        elif (not globs == None) and len(globs) > 0:
            for g in globs:
                for source in glob.iglob(g, recursive=True):
                    self.process_source(source)

    def process_source(self, source:str):
        self.current_file_name = source
        try:
            f = open(source, 'r', newline='')
            try:
                self.print_verbose("Opened file for checking: " + source)
                self.source_lines=f.readlines()
                self._file_count += 1
                self._rules.run_rules_on_file(source, self.source_lines, self._srcml)
            finally:
                f.close()
        except (IOError, OSError) as e:
            log_file_exception("Could not open file! See stderr.", e, source)


    def get_file_count(self) -> int:
        return self._file_count



#################################################
##
## Globals
##
#################################################
file_manager: FileManager
rule_manager: RuleManager
logger: Logger
verbose: bool

def print_verbose(message:str):
    global verbose
    if verbose:
        print(message)


def print_summary(logger:Logger):
    global file_manager
    print ("Total Files Checked: " + str(file_manager.get_file_count()))
    print ("Total Warnings: " + str(logger.get_warning_count()))
    print ("Total Errors: " + str(logger.get_error_count()))


def log_violation_wrapper(log_type:rule.LogType, pos:LogFilePosition, msg:str, include_indentation:bool):
    """ Wrapper used by Rule objects.

    This procedure handles gluing together the state of the file currently being checked with the violation
    information provided by a rule. This wrapper avoids passing a full object to the Rules and thus avoids Rules
    calling other methods on the logging object. In addition, by providing the file name, rule name, and source
    lines here, the rule classes don't have to include the information. This cuts down on what would be
    boilerplate code for each rule.
    """

    global logger
    global rule_manager
    global file_manager

    logger.log_violation(log_type, pos, msg, include_indentation, file_manager.current_file_name, rule_manager.current_rule_name, file_manager.source_lines)

def log_rule_exception(msg:str, e:Exception, rule_name:str):
    """ Wrapper used to log issues when working with a rule.
    """

    global logger
    global file_manager

    logger.log_violation(rule.LogType.ERROR, LogFilePosition(-1,-1), msg, False, "rulecheck", rule_name, [])
    print(e, sys.stderr)

def log_file_exception(msg:str, e:Exception, file_name:str):
    """ Wrapper used to log issues when working with a file.
    """

    global logger
    global file_manager

    logger.log_violation(rule.LogType.ERROR, LogFilePosition(-1,-1), msg, False, file_name, "rulecheck", [])
    print(e, file=sys.stderr)

def create_parser():
    parser = argparse.ArgumentParser()
    parser.description = "Tool to run rules on code."
    parser.add_argument("-c", "--config", help="config file. Specify the option multiple times to specify multiple config files.", required=True, nargs=1, action="extend", type=str)
    parser.add_argument("-x", "--extensions", help="extensions to include when traversing provided source path(s)", required=False, nargs=1, action="extend", type=str)
    parser.add_argument("-r", "--rulepaths", help="path to rules. Specify the option multiple times to specify multiple paths.", nargs=1, action="extend", type=str)
    parser.add_argument("-g", "--generatehashes", help="output messages with hash values used for ignore files", action="store_true")
    parser.add_argument("--srcml", help="path to srcml, required if srcml not in path", nargs=1, type=str)
    parser.add_argument("--register-ext", help="specify extension to language mappings used with srcml. --register-ext EXT=LANG", nargs=1, action="extend", type=str)
    # The srmclargs value must be quoted and start with a leading space because of this bug in argparse: https://bugs.python.org/issue9334
    parser.add_argument("--srcmlargs", help="additional arguments for srcml. MUST BE QUOTED AND START WITH A LEADING SPACE. Note that rulecheck will automatically handle the --language option based on --register-ext parameters to rulecheck. Also, --tabs has its own dedicated option.", default="--position --cpp-markup-if0", nargs=1, type=str)
    parser.add_argument("--tabs", help="number of spaces used for tabs", default=4, type=int)
    parser.add_argument("--Werror", help="all warnings will be promoted to errors", action="store_true", default=False)
    parser.add_argument("-i", "--ignorelist", help="file with rule violations to ignore", default = "", type=str)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s '+ __version__)
    parser.add_argument("sources", help="globs source file(s) and/or path(s). ** can be used to represent any number of nested (non-hidden) directories. If '-' is specified, file list is read from stdin.", nargs='*', action="append", type=str)

    return parser

def rulecheck(args) -> int:
    """Run rule check using specified command line arguments. Returns exit value.
    0 = No errors, normal program termination.
    1 = Internal rulecheck error
    2 = At least one rule reported an error
    3 = At least one rule reported a warning but no rules reported an error
    """
    global logger
    global rule_manager
    global file_manager
    global verbose

    verbose = False
    if args.verbose:
        verbose = True

    if args.srcml:
        srcml_bin = shutil.which('srcml', path=args.srcml)
    else:
        srcml_bin = shutil.which('srcml')

    if srcml_bin:
        print_verbose("srcml binary located at: " + srcml_bin)
    else:
        print ("Could not locate srcml binary!")
        if args.srcml:
            print ("srcml path was specified as: " + args.srcml)
        else:
            print ("system path was searched")
        return 1

    srcml_args = []
    if args.srcmlargs:
        srcml_args.extend(args.srcmlargs.split())

    if args.tabs:
        srcml_args.append("--tabs=" + str(args.tabs))

    srcml = Srcml(srcml_bin, srcml_args, verbose)

    if args.register_ext:
        for register_ext in args.register_ext:
            regext = register_ext.split("=")
            if len(regext) == 2:
                srcml.add_ext_mapping('.'+regext[0], regext[1])
            else:
                print ("Bad --register-ext option: " + register_ext)
                return 1

        print_verbose("Extension to language mappings for srcml are: " + str(srcml.get_ext_mappings()))

    ignore_list_file_handle = None
    if args.ignorelist:
        print_verbose("Ignore list specified: " + args.ignorelist)
        ignore_list_file_handle = open(args.ignorelist, "r")

    logger = Logger(args.tabs, args.generatehashes, args.Werror, ignore_list_file_handle, verbose)

    rule.Rule.set_logger(log_violation_wrapper)
    
    rule_manager = RuleManager(verbose)

    rule_manager.load_rules(args.config, args.rulepaths)

    file_manager = FileManager(rule_manager, srcml, verbose)

    # Flatten list of lists in args.sources and pass to process_files
    file_manager.process_files([item for sublist in args.sources for item in sublist])


    if ignore_list_file_handle:
        ignore_list_file_handle.close()

    if args.verbose:
        print_summary(logger)
        
    if logger.get_error_count() > 0:
        return 2
    elif logger.get_warning_count() > 0:
        return 3
    
    return 0
        
def main():
    parser = create_parser()
    args = parser.parse_args()
    result = rulecheck(args)
    sys.exit(result)

