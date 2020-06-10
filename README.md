# Source Rule Check
Introductory text

# TODO
- [x] For srcml rules, some tags should support an _entry and _exit or _start and _end method so rule knows when i.e. a block has ended.
- [x] Support logging errors and warnings
- [x] Support argument to promote warnings to errors
- [x] Output hash identifier with logs, hash content to be based on type of rule
- [x] Support line/srcml rules notifying that whitespace is to be ignored in hash (default will be to ignore whitespace)
- [x] Support ignore file based on hash
- [x] Call srcml to convert source
- [x] Provide line,col to visit methods so they don't have to parse it for logging messages.
- [ ] Verbose mode
        - [x] Summary count of warnings and errors
        - [x] Print filename when it is opened
        - [ ] Use timeit and print summary of how long each rule ran for and summary of srcml execution time and summary of "other" overhead time.
        - [x] Print path to srcml (that way if not specified can verify which binary is used)
        - [x] Print "Rules loaded from {config file}: rulex, ruley, ...." for each config file
- [x] Implement searching path(s) with extension(s), while still supporting --source specifying single files
- [x] Support rule paths argument
- [x] Support multiple config files
- [x] Support the srcml paramter
- [x] Support srcmlargs parameters.
- [x] Support option on which extensions to pass to srcml (use srcml option syntax --register-ext EXT=LANG )
- [x] Tab size parameter. Use to specify --tabs with srcml and also store in Rule class so rules can get the value for using .expandtabs() when printing
- [x] Add dependencies to setup.py
- [x] Add file close visit so rules know when a file is done
- [x] Test stdin files list
- [x] Change process_source to close file
- [ ] Add try: before calling any rule's visit methods. If exception, log message for the rule and print exception to stderr.
- [ ] Consider having log wrapper method check type of inputs and throw exception if not correct input.
- [ ] Test and cleanup as needed what happens when: rule path not found, rule not found, source not found, srcml not found, config file not found, srcml returns an error, settings for rule not present in json, no rules specified in config json    
- [ ] Consider passing the srcml unit _tree_ to file open so rules can use xpath searches if desired.
- [ ] Rules need to provide which languages they parse. There are the same srcml tags across several languages, but a style or other rule might only apply to a langugage or a few, not all.
         Rules can be dynamic in this by taking in a setting and changing what they return in the language getter.
- [ ] Provide a visitor on rules to be called once all files have been processed. 
- [ ] Per rule werror setting
- [ ] Have integration test parse output, using a any_other rule that logs every xml element with a viist_line that logs every line and show that the reported positon always increases
- [ ] Create test module to help rule authors test their rules. They should be able to specify:
          The rule class for rulechecktest to create
          A file for input
          	Maybe support taking in an already created srcml file
          Settings dictionary for their rule
          Get a list of log calls the rulemade
          Run standard set of asserts on their rule creation (does it do all the correct things on object creation?)
          Provide help text
- [ ] Provide verbosity level to turn on verbosity on each rule and support per rule verbose settings. Add print_verbose to Rule class.
- [ ] How can rules report their help/use? Maybe they should each have a main where they just print out usage? 
- [ ] Document/support rules failing config (bad settings) Maybe they should print their use/help on error? Or maybe they should DefaultProvider      a method to return that text and loadRules would print it on exception from init of the rule?
- [ ] Document in readme that rules can be loaded multiple times. And that to prevent that a rule should throw an error on init if 2nd time called.
- [ ] "Mute after n" option to print summary for a rule on a file on n+1th message from a rule (to reduce log size)
- [ ] Have logger keep total count of err and warn (two counts) for each rule (by rule name) over all files and include that in summary. Print Error Count, Warning Count, Rule Name so rule name length doesn't impact output formatting.
         The counts between instiatiations of the same rule would not be counted separately 
- [ ] Support ignore based on line comment (ignore next line, if possible ignore next srcml element)
- [ ] Support argument and per-rule setting to disable ignore/disable via line comments (strict mode)
- [ ] Support rule config (part of settings) to make rule strict so it can't be ignored by any method.
- [ ] Support line comment to push-disable and pop-last-setting for rule(s)
- [ ] Ignore via hash needs to take line number +/- n lines as many lines may hash to same value as the line content is identical. With this, 
      the hashes must be loaded from the ignore list and duplicates in ignore list counted and then decremented as they are found in the 
      files being searched. If count reaches 0 or line not within n lines of ignore row then it is a reported violation.
- [ ] Support ignore list cleanup option to output a new list with line numbers updated (if original list had issue at line 5, but it was found at line 6 then it is still a match and output new list with line 6 listed)

___

### Contents
___
* [Installation](#installation)
* [Running](#running)
* [Config](#config)
* [Rules](#rules)
  * [Built In](#built-in)
    * [A](#ruleA)
    * [B](#ruleA)
    * [C](#ruleA)
  * [Creating Rules](#creating-rules)
* [Resources](#resources)

___
### Installation

Dependencies include lxml. lxml is used over ElementTree due to speed and additional functionality such as the ability
to obtain the line number of tag from the source XML file. lxml has been available in Wheel install format since 2016
and thus should not present an issue for users.

___
```
pip install something
```

or

```
git clone https://github.com/
cd something
python setup.py install
```

___
### Running
___

Note that extensions are case sensitive and .C and .H are by default treated as C++ source files whereas .c and .h
are treated as C source files.

___
### Config
___

___
### Rules
___

___
#### Built In

___
##### RuleA

___
##### RuleB

___
##### RuleC

___
#### Creating Rules

Naming/Path
Extending Rule
What to do in __init__, how settings work
getRuleType

Note: parsing xml, the visit methods must be named visit_xml_nodename_start|end. The use of xml_ at the start
avoids collisions with visit_file_open and visit_file_line as XML does no allow any nodename to start with 'xml'.
___
##### SrcML Tags
___
##### Tips
Use global tabs setting from command line instead of per-rule setting for tabs
How to prevent rule from being instantiated twice

___
### Resources
___