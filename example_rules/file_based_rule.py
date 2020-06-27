# At a minimum, all rules will need to import the rule package
from rulecheck import rule

# All rules must contain a class named the same as the containing
# file and extending the Rule class.
class file_based_rule(rule.Rule):

    # All rules must define the get_rule_type() method and
    # return the appropriate RuleType.
    # Because this is a FILE rule type, this rule should not use any of
    # the line or xml visit methods.
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.FILE
    
    # visit_file_open is called when a file is first opened for processing.
    def visit_file_open(self, pos:rule.LogFilePosition, fileName:str):
        # This shows how an ERROR can be logged. Of course one would want to 
        # implement some logic instead of logging an error on every file opened.
        self.log(rule.LogType.ERROR, pos, "Visited file: " + fileName)
        
    # visit_file_close is called when a file is first opened for processing.
    def visit_file_close(self, pos:rule.LogFilePosition, fileName:str):
        # This shows how a WARNING can be logged.
        self.log(rule.LogType.WARNING, pos, "Done with file: " + fileName)
        
    # The following methods should not be defined in this rule
    # since this is a FILE based rule:
    # visit_line
    # visit_xml_tagname_start, or visit_xml_tagname_end
    # visit_any_other_xml_element_start, or visit_any_other_xml_element_end