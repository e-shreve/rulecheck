from rulecheck import rule
from lxml import etree as ET


class badRuleThrowsException(rule.Rule):

    def __init__(self, settings):
        super().__init__(settings)
        raise Exception("I always raise this.")
    
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

        
    def visit_xml_if_start(self, pos:rule.LogFilePosition, element : ET.Element):
        self.log(rule.LogType.WARNING, pos, "Found if statement")
        
