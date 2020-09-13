from rulecheck import rule

class printRowsWithWord(rule.Rule):

    def __init__(self, settings):
        super().__init__(settings)

        try:
            self._word = settings["word"]
        except Exception:  #pylint: disable=broad-except
            self._word = "the"

        self.print_verbose("printRowsWithWord created for word: " + self._word)

    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.LINE

    def visit_file_line(self, pos:rule.LogFilePosition, line:str):
        col = line.find(self._word)
        if col >= 0:
            pos.col = col
            self.log(rule.LogType.WARNING, pos,
                     "use of the word " + self._word + " : " + line.rstrip())
