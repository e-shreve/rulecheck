import abc
from enum import Enum, auto


class RuleType(Enum):
    FILE = auto()
    LINE = auto()
    SRCML = auto()

class LogType(Enum):
    WARNING = auto()
    ERROR = auto()

class LogFilePosition:

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
    log_function = None

    def __init__(self, settings):
        self._is_active = True
        self._settings = settings

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

    @staticmethod
    def set_logger(log_function):
        """ Changes the logger function backing all of the rules' log method.
            Rulecheck will call this method to configure the logger. It is not expected or intended
            for rules to call this method themselves.
        """
        Rule.log_function = log_function

    def log(self, log_type:LogType, pos:LogFilePosition, message:str):
        """ Log a rule violation (Error or Warning). The sytem will automatically format
            the output to fit a standard including the name of the file currently being parsed
            and the name of the rule. Thus, the message parameter need not repeat this information.
        """
        if callable(Rule.log_function):
            # Note: pylint disabled due to bug: https://github.com/PyCQA/pylint/issues/1493
            Rule.log_function(log_type, pos, message, self.is_indentation_sensitive())  #pylint: disable=not-callable
