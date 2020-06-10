from rulecheck import rule
from lxml import etree as ET

class rule2(rule.Rule):
    
    def __init__(self, settings):
        rule.Rule.__init__(self, settings)
        print ("rule2 init")

    
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

        
    def visit_xml_comment_start(self, pos:rule.LogFilePosition, node: ET.Element):        
        self.log(rule.LogType.ERROR, pos, "Found comment: " + node.text)
        