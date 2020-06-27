# This examples shows how to disable a rule from being
# called for the remainder of a file's processing.
# Note that rulecheck will automatically re-enable
# a rule when opening a file for parsing.
#
# There are two general use cases for this feature.

# The first is when the rule does not apply to all files
# and the rule is able to self-determine if it applies based on
# the file or path name and/or content of the file. By disabling
# itself, the rule logic doesn't need to worry about handling additional
# calls without logging an error or warning.

# The second is when a rule has finished checking for compliance
# before the end of the file. For example, a rule requiring that
# files begin with a comment containing certain content can disable 
# itself once it has determined if the rule was violated or not. 
# Again, the rule logic doesn't need to be concerned with avoiding
# logging duplicate messages since it won't be called again until the
# next file begins processing.
# 

from rulecheck import rule
from lxml import etree as ET

class self_disabling_rule(rule.Rule):

    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML

    def visit_xml_comment_start(self, pos:rule.LogFilePosition, element : ET.Element):
        if not "copyright" in element.text: 
            # Don't report a row or col number in the log since
            # the problem is not at a particular location in the file.
            pos.row = -1
            pos.col = -1         
            self.log(rule.LogType.ERROR, pos, "File does not start with a copyright comment.")
                
        self.set_inactive()
                
    def visit_any_other_xml_element_start(self, pos:rule.LogFilePosition, element : ET.Element):
        # Don't report a row or col number in the log since
        # the problem is not at a particular location in the file.
        pos.row = -1
        pos.col = -1
        self.log(rule.LogType.ERROR, pos, "File does not start with a copyright comment.")
        
        # Try commenting out this line and see how the logging output changes on files
        # that have no comments.
        self.set_inactive()