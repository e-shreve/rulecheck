from rulecheck import rule
from lxml import etree as ET


class findSingleLineCommentsWith(rule.Rule):

    def __init__(self, settings):
        super().__init__(settings)
        try:
            self.with_string = settings["with_string"]
        except:
            raise KeyError('Settings for findSingleLineCommentsWith rule must include a with_string parameter.')
    
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

    def visit_xml_comment_start(self, pos:rule.LogFilePosition, element : ET.Element):
        if "type" in element.attrib:          
            if element.attrib["type"] == "line":
                self.log(rule.LogType.WARNING, pos, "Found line comment " + element.text)
        
    
        
