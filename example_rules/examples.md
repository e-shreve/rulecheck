# Example Rules

These rules are provided to illustrate how to write rules. After installing 
rulecheck, you can run these rules by using the all_rules.json file as the
config file and specifying the example_rules path using the -r option.
For example:
```bash
rulecheck -c ./rulecheck/example_rules/all_rules.json -r ./rulecheck/ ./path/to/my/source
```

The suggested order to read through the examples is:
1. [file_based_rule.py](file_based_rule.py)
2. [line_based_rule.py](line_based_rule.py)
3. [srcml_based_rule.py](srcml_based_rule.py)
4. [self_disabling_rule.py](self_disabling_rule.py)
5. [indentation_sensitive_rule.py](indentation_sensitive_rule.py)
6. [rule_with_settings.py](rule_with_settings.py)
