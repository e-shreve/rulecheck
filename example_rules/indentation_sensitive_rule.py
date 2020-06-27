from rulecheck import rule
from lxml import etree as ET

# By default, rules are considered as leading whitespace insensitive. This means that the rule is not expected
# to change what it logs based on the leading whitespace (indentation level). This allows rulecheck to strip 
# leading whitespace from a line when calculating the hash of the line used for the ignore list feature. This 
# improves the matching of the ignore list by allowing the indentation level of a line to change without impacting
# its identification in an ignore list.
#
# However, if a rule does consider leading whitespace (indentation) then the ignore list should use the leading
# whitespace for the hash value. 
#
# This rule provides an example of a rule that is sensitive to leading whitespace and shows how to tell rulecheck
# that it is so. This is done by overriding the is_indentation_sensitive method of the Rule class.
#
# To see the impact of changing the indentation sensitivity, try running this rule on source code that will
# trigger a log message and do so with the --generatehashes command line option. Then edit this file to change
# the return value of is_indentation_sensitive() to False and run the command line again. You should see a different
# leading hash value but the same message(s). Because the hash value is used to identify violations to be ignored
# when using an ignore list, this difference will impact the ability of rulecheck to correctly ignore the violation.

class indentation_sensitive_rule(rule.Rule):

    def __init__(self, settings):
        # Rules should always call the super's init function to ensure
        # proper functioning
        super().__init__(settings)
        
        self.last_indentation = 0
        self.in_comment = False

    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

    # This is the crtical function for indentation sensitivity. This function must
    # return True if the rule is sensitive to indentation. Otherwise it should return False. Note that the
    # Rule class already defines this method and returns False. Thus, if the rule is _not_ indentation
    # sensitive there is no need to define this function.
    def is_indentation_sensitive(self):
        return True
    
    # This rule logs an error if the indentation difference from a previous line
    # is not a multiple of 4. Blank lines are ignored.
    
    def visit_file_line(self, pos:rule.LogFilePosition, line:str):
        if self.in_comment:
            return 
        
        tab_expanded = line.expandtabs(tabsize=4)
        level = len(tab_expanded) - len(tab_expanded.lstrip())
        
        if level == len(tab_expanded):
            # Line is empty (all whitespace)
            return 
        
        if not abs(self.last_indentation - level) % 4 == 0:
            self.log(rule.LogType.ERROR, pos, "Line found at inappropriate indentation compared to last indented line.")
        else: 
            self.last_indentation = level
    
    # This rule takes advantage of the fact that rulecheck will call visit_file_line()
    # for a line prior to calling any visit_xml_* methods for tags representing content
    # of that line. Because of this ordering, when a comment starts, the self.in_comment
    # value will only be set to true after the visit_file_line has checked the starting
    # position of the comment on the line for a rule violation.
    def visit_xml_comment_start(self, pos:rule.LogFilePosition, element:ET.Element):
        self.in_comment = True
        
    def visit_xml_comment_end(self, pos:rule.LogFilePosition, element:ET.Element):
        self.in_comment = False