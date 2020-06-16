# Rule Check
Rule Check (aka rulecheck or source rule check) is a command line system for running custom static analysis rules on C, C++, and Java code. The original intended use case is for checking a code base against coding style or coding standard rules. 

Rule Check uses [srcml](https://www.srcml.org/) to parse the source code into XML and then invokes each rule's methods as appropriate to allow the rules to inspect any source code element of interest to the rule. This architecture minimizes duplicate parsing time and allows rule authors to focus on their rule logic instead of the logic needed to parse source code.

Features include:
* Support for parsing C, C++, Java source
* Supports parsing C and C++ prior to preprocessor execution (parses code in the form the developer uses)
* Supports custom rules
  * Groups of rules can be created and published in 'rulepacks'
  * Projects can have custom rules within their own code base (no need to publish/install rules)
  * Rules can have their own custom settings. Rule check will provide the settings to the rule via its standard config file format.
* Supports multiple config file inputs
  * Projects can use an hierarchical set of configurations allowing organizations to provide rules across projects
* Standardized output format for all rules
* Supports ignore list input to ignore specific rule violations in a code base without modifying the code
* Source to be analyzed specified in glob format

Features to be developed include:
* Ability to ignore rule violations by using comments in the source code to turn off/on rules.


___

### Contents
___
* [Installation](#installation)
* [Running](#running)
* [Config](#config)
* [Creating Rules](#creating-rules)
* [Resources](#resources)

___
### Installation

Ensure dependencies are present on the system (see below) and then run:
```
git clone https://github.com/e-shreve/rulecheck
cd rulecheck
pip install .
```

#### Dependencies

##### Python
Pythong 3.8 is required.

##### lxml
The pythong xml library lxml is used over the built-in ElementTree library due to speed and additional functionality such as the ability
to obtain the line number of tag from the source XML file. lxml has been available in Wheel install format since 2016
and thus should not present an issue for users.

##### srcml
srcml is a source code to xml parser that can parse C, C++, and Java code. Find installation files at https://www.srcml.org/.
Version required: 1.0.0 or greater.
For easiest use, srcml should be on the path. Otherwise, the path to srcml can be provided when starting rulecheck from the command line.

___
### Running
___

```
rulecheck --help
```

Note that extensions are case sensitive and .C and .H are by default treated as C++ source files whereas .c and .h
are treated as C source files.

___
### Config
___

- [ ] Document in readme that rules can be loaded multiple times. And that to prevent that a rule should throw an error on init if 2nd time called.

___
### Creating Rules

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
* [srcml](https://www.srcml.org)
* [srcml source](https://github.com/srcML/srcML)
* [lxml](https://lxml.de/)
