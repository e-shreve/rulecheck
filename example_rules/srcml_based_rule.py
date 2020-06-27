# Rules that use visitors based on SRCM tags will need to import etree from lxml.
from rulecheck import rule
from lxml import etree as ET

# All rules must contain a class named the same as the containing file and extending the Rule class.
class srcml_based_rule(rule.Rule):

    # All rules must define the get_rule_type() method and return the appropriate RuleType.
    # Because this is a SRCML rule type, this rule may use any of the  visit_file_* methods and
    # any of the xml visit methods.
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML


    # Rulecheck has srcml create an xml representation of each file to be parsed.
    # rulecheck then walks the xml in depth-first order. For each opening tag 
    # rulecheck will look for a method named 'visit_xml_tagname_start' defined
    # by a rule. If found, it will be called. Likewise for each closing tag,
    # any visit_xml_tagname_end method will be called.
    
    # The first xml tag of any srcml output is the unit tag. 
    # Here the example demonstrates using this tag to get the filename
    # and langauge type. 
    def visit_xml_unit_start(self, pos:rule.LogFilePosition, element:ET.Element):
        lang = element.attrib['language']
        filename = element.attrib['filename']
        self.log(rule.LogType.WARNING, pos, "Starting to parse " + filename + " which contains " +
                                            lang + " source code.")

    # This example checks for the number of case statements in a single switch
    # and prints an error if there are more than 20 or if there is no default.
    # It will also print a warning if there are more than 10 case statements.

    def visit_xml_switch_start(self, pos:rule.LogFilePosition, element : ET.Element):
        self.case_count = 0
        self.has_default_case = False
        self.switch_start_pos = pos
     
    def visit_xml_case_start(self, pos:rule.LogFilePosition, element:ET.Element):
        self.case_count += 1
    
    def visit_xml_default_start(self, pos:rule.LogFilePosition, element:ET.Element):
        self.has_default_case = True
        
    def visit_xml_switch_end(self, pos:rule.LogFilePosition, element : ET.Element):
        if (self.case_count > 20):
            self.log(rule.LogType.ERROR, self.switch_start_pos, "Switch statement has " + 
                                                                 str(self.case_count) + 
                                                                 " cases which is more than the limit of 20.")        
        elif (self.case_count > 10):
            self.log(rule.LogType.WARNING, self.switch_start_pos, "Switch statement has " +
                                                                  str(self.case_count) + 
                                                                  (" cases which is a lot",
                                                                   " but not more than the limit of 20."))
       
        if not self.has_default_case:
            self.log(rule.LogType.ERROR, self.switch_start_pos, 
                    "Switch statement does not have a required default case.")        
 
    
    #
    # There are two additional xml/srcml visit methods (see end of comment block) which
    # are called when a direct match on the tagname is not found. See self_disabling_rule.py
    # for an example of their use.
    #          
    # def visit_any_other_xml_element_start(self, pos:rule.LogFilePosition, element : ET.Element):
    # 
    # def visit_any_other_xml_element_end(self, pos:rule.LogFilePosition, element : ET.Element):
    