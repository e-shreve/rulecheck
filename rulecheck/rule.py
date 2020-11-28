"""
    Rule Module

    Provides the base Rule class for all rules as well as the following support classes:
      * RuleType enum
      * LogType enum
      * LogFilePosition class

    Note that the last two are defined in the Rule Module and not the Logging module so that rule
    implementations have fewer imports to be concerned about.
"""

import abc
import distutils.util
from enum import Enum, auto

class RuleType(Enum):
    """Designates the 'type' of a Rule object/class. Every rule must provide a type via
       its get_rule_type() method.

        - SRCML based rules use srcml based tags for parsing and may also use per-line and
                per-file parsing methods
        - LINE based rules use per-line parsing and may also use the per-file parsing methods.
               However, they should not use any of the srcml tag information.
        - FILE based rules use per-file parsing methods and avoid any other parsing methods.
    """

    FILE = auto()
    LINE = auto()
    SRCML = auto()

class LogType(Enum):
    """Designates the log type or level for a given log message. One of:
       WARNING or ERROR. Note that werror options may force WARNINGS to be reported
       as ERRRORs.
    """

    WARNING = auto()
    ERROR = auto()

class LogFilePosition:
    """Provides the line and col(umn) information for a rule violation log message.
       Both line and col values are one-based (start at 1, not 0).

       Access the line and col members directly. For example, for LogFilePosition object pos:
       pos.line
       pos.col

       Use -1 for a value if should not be included in a log message.
    """

    def __init__(self, line:int, col:int):
        self.line = line
        self.col = col

    def __eq__(self, other):
        return self.line == other.line and self.col == other.col

    def __str__(self):
        return str(self.line) + ":" + str(self.col)

    def __repr__(self):
        return str(self.line) + ":" + str(self.col)

class Rule:
    """Base class for all rules.
    """

    __log_function = None

    def __init__(self, settings):
        self._is_active = True
        self._settings = settings

        try:
            self._werror = distutils.util.strtobool(settings["werror"].lower())
        except Exception:  #pylint: disable=broad-except
            self._werror = False

        try:
            self._verbose = distutils.util.strtobool(settings["verbose"].lower())
        except Exception:  #pylint: disable=broad-except
            self._verbose = False

    def get_settings(self):
        """ Returns the settings map. Expected to be name, value pairs. """
        return self._settings

    @abc.abstractmethod
    def get_rule_type(self) -> RuleType:
        """ Implemented rules must declare their type. """

    def is_indentation_sensitive(self) -> bool:  #pylint: disable=no-self-use
        """ Override to return True if leading whitespace changes (indentation level)
            may impact the result of rule's check.
        """
        return False

    def is_active(self) -> bool:
        """ Returns true if the rule is active and will, therefore, have its visitors called. """
        return self._is_active

    def set_active(self):
        """ Activate the rule so that it will have its visitors called during parsing of a file. """
        self._is_active = True

    def set_inactive(self):
        """ Deactivate a rule so its visitors will no longer be called.

            Rules should call this method on self, to save on processing time when/if the rule
            logic determines it need not process any additional visitors for the source file
            currently being processed.

            Note: Rulecheck will always (re)activate rules automatically when a source file is first
            opened for parsing.
        """
        self._is_active = False

    def print_verbose(self, message: str):
        """Print method useful for diagnosing issues with Rule implementations.
           This method is _not_ a substitution for the log method. Do _not_ use this method to
           report rule violations.
        """
        if self._verbose:
            print(message)

    @staticmethod
    def set_logger(log_function):
        """ Changes the logger function backing all of the rules' log method.
            Rulecheck will call this method to configure the logger. It is not expected or intended
            for rules to call this method themselves.
        """
        Rule.__log_function = log_function

    def log(self, log_type:LogType, pos:LogFilePosition, message:str):
        """ Log a rule violation (Error or Warning). The system will automatically format
            the output to fit a standard including the name of the file currently being parsed
            and the name of the rule. Thus, the message parameter need not repeat this information.
        """

        if self._werror:
            log_type = LogType.ERROR

        if callable(Rule.__log_function):
            # Note: pylint disabled due to bug: https://github.com/PyCQA/pylint/issues/1493
            Rule.__log_function(log_type, pos, message, self.is_indentation_sensitive())  #pylint: disable=not-callable
