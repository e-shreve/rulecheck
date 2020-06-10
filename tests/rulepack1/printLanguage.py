from rulecheck import rule
from lxml import etree as ET


class printLanguage(rule.Rule):

    
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

    def visit_xml_unit_start(self, pos:rule.LogFilePosition, element : ET.Element):
        if "language" in element.attrib:          
            self.log(rule.LogType.WARNING, pos, "Language: " + element.attrib["language"])
        
    
        
