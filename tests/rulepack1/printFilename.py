from rulecheck import rule

class printFilename(rule.Rule):

    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.FILE

    def visit_file_open(self, pos:rule.LogFilePosition, file_name:str):
        self.log(rule.LogType.WARNING, pos, "Visited file: " + file_name)
        