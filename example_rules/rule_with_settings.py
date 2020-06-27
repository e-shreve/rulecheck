# This rule is the same as the line_based_rule example but it
# shows how a rule with custom settings can be created.

from rulecheck import rule
import re

class rule_with_settings(rule.Rule):

    # Custom settings are provided to the rule's init method as the
    # second parameter.
    def __init__(self, settings):
        # Rules should always call the super's init function to ensure
        # proper functioning
        super().__init__(settings)
        
        # Rules should be read within a try block to catch
        # when the setting is not provided.
        try:
            self.word_to_find = settings["word_to_find"]
            # Rules should validate values of settings and raise an error
            # if not appropriate.
            if re.search(r"\s", self.word_to_find):
                raise ValueError("word_to_find setting for rule_with_settings must be a single word (no whitespace allowed).")
        except:
            # If a required rule is not provided a KeyError should be raised
            # with a message stating which setting was missing.
            raise KeyError('Settings for rule_with_settings rule must include a word_to_find parameter.')

            # If a rule is optional, the except block can be used to set a default
            # value for the setting. (Not shown here.)

    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.LINE
    
    # visit_file_open is called when a file is first opened for processing.
    def visit_file_open(self, pos:rule.LogFilePosition, fileName:str):
        self.log(rule.LogType.ERROR, pos, "Visited file: " + fileName)
        
    # visit_file_line is called on each line of the file
    def visit_file_line(self, pos:rule.LogFilePosition, line:str):
        # The last parameter is the line text, including any newline characters at the end
        
        indexOfWord = line.find(self.word_to_find);
        if indexOfWord >= 0:
            # In visit_file_line, the pos parameter will have the col value set to -1. 
            # We can update it to give the user more information about where in the line
            # a problem was found. Note that column numbers are 1 based and find returns
            # a zero-based offset.
            pos.col = indexOfWord + 1
            self.log(rule.LogType.WARNING, pos, "use of the word '" + self.word_to_find + "' found: " + line.rstrip())  
    
    # visit_file_close is called when a file is first opened for processing.
    def visit_file_close(self, pos:rule.LogFilePosition, fileName:str):
        self.log(rule.LogType.WARNING, pos, "Done with file: " + fileName)
        