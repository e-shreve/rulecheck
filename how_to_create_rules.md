### How To Create Rules

Rules are python scripts, organized into rulepacks by the python packaging system. Each rule defines methods that 
rulecheck will call as appropriate while it is parsing the files to be checked.

This guide covers all aspects of creating rules. In addition, example rules are provided in the example_rules
folder. See [examples](example_rules/examples.md) for an introduction to the examples.

#### Rulepacks

Rulepacks are Python packages of rules. The name of the rule pack is the name of the package. A rulepack must contain an __init__.py file so it can be recognized as a Python package. Rulepack authors are encouraged to create pip-installable packages. However, doing so is outside the scope of this guide.

#### Rule Script Contents

Each rule script is a Python file. It must contain a class of the same name as the script file name.
The class must extend the Rule class from the rulecheck package.
Further, the class must have a method named 'get_rule_type' which returns one of:

* RuleType.SRCML
* RuleType.LINE
* RuleType.FILE

Example for a file named rule1.py:

```Python
from rulecheck import rule

class rule1(rule.Rule):

    def get_rule_type(self)->rule.RuleType:
        return rule.RuleType.SRCML
```

The method get_rule_type is used by rulecheck to classify the information a rule operates on.
This information may be used in a future version of rulecheck for runtime performance optimizations.

- SRCML based rules use srcml based tags for parsing and may also use per-line and per-file parsing methods
- LINE based rules use per-line parsing and may also use the per-file parsing methods. However, they should not use any of the srcml tag information.
- FILE based rules use per-file parsing methods and avoid any other parsing methods.

Rules define optional methods which rulecheck will call during initialization and as it parses a file. These methods are listed below:

* visit_file_open(self, pos:rule.LogFilePosition, fileName:str)
   * Called when a file is opened for checking.
   * The fileName string will include the path of the file. However, it may or may not be the full path depending on how the file was specified to rulecheck on the command line.
* visit_file_line(self, pos:rule.LogFilePosition, line:str)
   * Called for each line of the file content. 
   * The line string contains a single line, including newline characters.
* visit_xml_[tagname]_start(self, pos:rule.LogFilePosition, element : etree.Element)
   * When visiting the opening tag of the srcml output, rulecheck will call any method following this naming pattern where [tagname] is the same as the parsed tag name.
   * For example, when processing a <comment> tag, rulecheck will call the following method if it exists: visit_xml_comment_start.
   * The element parameter is of type etree.Element from the lxml package.
* visit_xml_[tagname]_end(self, pos:rule.LogFilePosition, element : etree.Element)
   * Same as the start method above but this is called when a closing tag is processed.
   * For example, when processing a </comment> tag, rulecheck will call the following method if it exists: visit_xml_comment_end.
* visit_any_other_xml_element_start(self, pos:rule.LogFilePosition, element : etree.Element)
   * When visiting the opening tag of the srcml output, rulecheck will call this method if it is defined _and_ no matching visit_xml_[tagname]_start is defined.
* visit_any_other_xml_element_start(self, pos:rule.LogFilePosition, element : etree.Element)
   * When visiting the closing tag of the srcml output, rulecheck will call this method if it is defined _and_ no matching visit_xml_[tagname]_end is defined.
* visit_file_close(self, pos:rule.LogFilePosition, fileName:str)
   * Called when all file content has been processed. No further calls to the rule for this file will be made after this call.

The order in which rulecheck calls these parsing methods is: 
* visit_file_open
* visit_xml_unit_start
* then rulecheck loops over each line for each line from first to last and calls:
   * visit_file_line
   * visit_xml_* methods for any source element starting or ending on the line, in a left to right order.
* visit_xml_unit_end
* visit_file_close

In addition to those parsing related methods, the following methods may be called by rulecheck:

* __init__(self, settings)
   * This is the standard object initialization method called when an instance of the rule is created.
   * The settings value is a Python dictionary constructed from the 'settings' object of the configuration file provided on the command line.
   * This method should always call the parent class' init method: super().__init__()
* is_whitespace_sensitive(self) -> bool
   * The Rule class defines this method and returns False.
   * If a rule is sensitive to whitespace (whitespace can distinguish between passes, warnings, and errors) then this method should be overridden to return True. 

#### Position Information

All of the file parsing methods take a rule.LogFilePosition parameter. Rulecheck will
populate this parameter with the row and column number of the element being parsed. 
Rules can access and change these values as pos.row and pos.col.

A value of -1 for the row or column number indicates that the value is unknown or not applicable.
For example, on visit_file_open(), the position information will be set to [-1,-1].

The log method in the Rule class also takes a LogFilePosition parameter. Many times,
rules can simply pass the received position information on to the log method. However, 
if the finding does not apply to the starting position of the element being parsed, a rule
may clarify where it found an issue by modifying the information. For example, the position
information passed to visit_file_line() will always have the col number set to -1. If a rule
is flagging a problem which starts on column 10 of the line it should update this value to 10
prior to calling the log function.

#### Logging Rule Violations

Logging rule violations is accomplished by calling the self.log(...) method from the rule script.
The log method has the signature:

```Python
    def log(self, rule.logType:LogType, rule.pos:LogFilePosition, message:str):
```

There are two LogType values: ERROR and WARNING. Example calls:

```Python
self.log(rule.LogType.ERROR, pos, "String explaining error")
self.log(rule.LogType.WARNING, pos, "String explaining warning")

```

#### Custom Settings and Other Concerns for __init__()

This is the standard object initialization method called when an instance of the rule 
is created. This method should always call the parent class' init method: super().__init__().
   
The __init__() method for the rule must take a settings parameter. 
The settings value passed will be a Python dictionary constructed from the 'settings' object 
of the configuration file provided on the command line. If no settings were specified in the 
config file the dictionary will be empty.
    
Additional topics to cover in this section:
- [ ] how settings work
- [ ] Document that rules can be loaded multiple times. And that to prevent that a rule should throw an error on init if 2nd time called.
- [ ] document to throw KeyError if required setting is not present or a setting value is not valid.
- [ ] document that rules should default their settings to something reasonable if possible

#### Activating and Deactivating Rules

- [ ] to be written

___
##### Tips
Use global tabs setting from command line instead of per-rule setting for tabs

How to prevent rule from being instantiated twice