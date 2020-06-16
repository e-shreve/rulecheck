# Source Rule Check
Introductory text


- [ ] Document in readme that rules can be loaded multiple times. And that to prevent that a rule should throw an error on init if 2nd time called.


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