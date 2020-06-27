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
        #return self.line == other.line and self.col == other.col
        return True
    
    def __str__(self):
        return str(self.line) + ":" + str(self.col)

    def __repr__(self):
        return str(self.line) + ":" + str(self.col)

class Rule:       
    log_function = None
       
    def __init__(self, settings):
        self.active_state = True
        self._settings = settings
        
    def get_settings(self):
        return self._settings

    @abc.abstractmethod
    def get_rule_type(self) -> RuleType:
        """Implemented rules must declare their type"""
        pass

    def is_indentation_sensitive(self) -> bool:
        return False

    def is_active(self) -> bool:
        return self.active_state
    
    def set_active(self):
        self.active_state = True
        
    def set_inactive(self):
        self.active_state = False
        


    @staticmethod
    def set_logger(log_function):
        Rule.log_function = log_function

    def log(self, logType:LogType, pos:LogFilePosition, message:str):
        Rule.log_function(logType, pos, message, self.is_indentation_sensitive())
                
        
