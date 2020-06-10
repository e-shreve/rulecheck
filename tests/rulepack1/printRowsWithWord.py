from rulecheck import rule


class printRowsWithWord(rule.Rule):

    
    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.LINE

    def visit_file_line(self, pos:rule.LogFilePosition, line:str):
        if line.find("the") >= 0:
            self.log(rule.LogType.WARNING, pos, "use of the word " + 'the' + " : " + line.rstrip())