from rulecheck import rule
from lxml import etree as ET
import os

class rule1(rule.Rule):

    
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

        
    def visit_xml_name_start(self, pos:rule.LogFilePosition, element : ET.Element):
        if element.text is not None:
            #print("Name: " + element.text)
            pass
        
    def visit_xml_block_start(self, pos:rule.LogFilePosition, element : ET.Element):
        print(element.attrib["{http://www.srcML.org/srcML/position}start"])
        #print(element.attrib["{http://www.srcML.org/srcML/position}end"])
        print(("block: " + os.linesep + ''.join(element.itertext())).expandtabs(4))
        
    def visit_xml_block_end(self, pos:rule.LogFilePosition, element : ET.Element):
        print("block end")