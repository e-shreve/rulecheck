# Local imports
from rulecheck.file import File
from rulecheck.ignore import IgnoreFile
from rulecheck.ignore import IgnoreFilter
from rulecheck.ignore import get_ignore_hash
from rulecheck.rule import LogType
from rulecheck.rule import LogFilePosition

#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes



class Logger:
    """ Class used to perform the logging.

    Holds logging settings and implements the logging function.

    """

    def __init__(self):
        self._tabsize = 8
        self._show_hash = False
        self._warnings_are_errors = False
        self._ignore_filter = None
        self._verbose = False
        self._total_warnings = 0
        self._total_errors = 0
        self._total_ignored_warnings = 0
        self._total_ignored_errors = 0
        self._current_file = None
        self._current_rule_name = "rulecheck"
        self._ignore_file_out = None

    def set_verbose(self, verbose:bool):
        self._verbose = verbose

    def set_ignore_filter(self, ignore_filter:IgnoreFilter):
        self._ignore_filter = ignore_filter

    def set_current_file(self, file:File):
        self._current_file = file

    def set_current_rule_name(self, rulename:str):
        self._current_rule_name = rulename

    def set_ignore_file_out(self, ignore_file_out:IgnoreFile):
        self._ignore_file_out = ignore_file_out

    def get_current_file(self) -> File:
        return self._current_file

    def get_current_rule_name(self) -> str:
        return self._current_rule_name

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

    def _increment_warnings(self):
        if self.warnings_are_errors():
            self._increment_errors()
        else:
            self._total_warnings += 1

    def _increment_errors(self):
        self._total_errors += 1

    def _increment_ignored_warnings(self):
        if self.warnings_are_errors():
            self._increment_ignored_errors()
        else:
            self._total_ignored_warnings += 1

    def _increment_ignored_errors(self):
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
        filename:[line]:[col]:LogType:Rule Name:Log Message[:hash of line]

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
        line_text = None
        if pos.line > 0 and pos.line < len(source_lines):
            line_text = source_lines[pos.line-1]
        log_hash = get_ignore_hash(file_name, line_text, include_indentation,
                                   log_type.name, rule_name)

        if self._ignore_file_out:
            self._ignore_file_out.add(log_hash, log_type.name,
                                      pos.line, pos.col, msg,
                                      file_name, rule_name)

        if not self._ignore_filter or not \
           self._ignore_filter.is_filtered(rule_name, pos.line, log_hash):

            log_msg = log_msg + file_name + ":"

            if pos.line > 0:
                log_msg = log_msg + str(pos.line) + ":"
            if pos.col > 0:
                log_msg = log_msg + str(pos.col) + ":"

            log_msg = log_msg + " "

            log_msg = log_msg + adjusted_log_type.name + ": " + rule_name + ": " + \
                      msg.expandtabs(self.get_tab_size())

            if self.show_hash():
                log_msg = log_msg + ": " + log_hash

            print(log_msg)

            if adjusted_log_type == LogType.ERROR:
                self._increment_errors()
            else:
                self._increment_warnings()
        else:
            if adjusted_log_type == LogType.ERROR:
                self._increment_ignored_errors()
            else:
                self._increment_ignored_warnings()

LOGGER = Logger()

def log_violation_wrapper(log_type:LogType, pos:LogFilePosition, msg:str,
                          include_indentation:bool):
    """ Wrapper used by Rule objects.

    This procedure handles gluing together the state of the file currently being checked with the
    violation information provided by a rule. This wrapper avoids passing a full object to the Rules
    and thus avoids Rules calling other methods on the logging object. In addition, by providing the
    file name, rule name, and source lines here, the rule classes don't have to include the
    information. This cuts down on what would be boilerplate code for each rule.
    """

    global LOGGER  #pylint: disable=global-statement

    LOGGER.log_violation(log_type, pos, msg, include_indentation,
                         LOGGER.get_current_file().get_name(),
                         LOGGER.get_current_rule_name(),
                         LOGGER.get_current_file().get_lines())
