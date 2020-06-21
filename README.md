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

Ensure Python 3.8 or greater is present on the system (see below) and then run:
```
git clone https://github.com/e-shreve/rulecheck
cd rulecheck
pip install .
```

#### Dependencies

##### Python
Python 3.8 or greater is required.

##### lxml
The python xml library lxml is used over the built-in ElementTree library due to speed and additional functionality such as the ability
to obtain the line number of tag from the source XML file. lxml has been available in Wheel install format since 2016
and thus should not present an issue for users. lxml will be installed by pip automatically when insalling rulecheck.

##### srcml
srcml is a source code to xml parser that can parse C, C++, C Preprocessor, C#, and Java code. The pip install of rulecheck will not
install srcml. Find installation files at https://www.srcml.org/ and install on your system.
Version required: 1.0.0 or greater.
For easiest use, srcml should be on the path. Otherwise, the path to srcml can be provided when starting rulecheck from the command line.


___
### Running and Configuration
___

```
rulecheck --help
```

#### Selecting Rules

Rule selection is done by specifying one or more rule configuration files on the command line, using the -c or --config option. To specify more than one configuration file, use the config option on the command line once for each configuration file to be read.

Note that rule selection is additive across all configuration files specified. Thus, if config1.json activates ruleA and config2.json activates RuleB then both RuleA and RuleB will be active.

Example of specifying more than one configuration file:

```bash
rulecheck -c config1.json -c config2.json ./src/**/*
```

Rule configuration files are json files, with the following structure:

```JSON
{
  "rules": [
    {
       "name" : "rulepack1.ruleA",
       "settings" : {
          "opt1" : "dog"
       }
    },
    {
       "name" : "rulepack1.ruleB",
       "settings" : {
          "opt1" : "cat"
       }
    }
  ]
}
```

At the top level, an array named "rules" must be provided. Each member of this array is a rule object. 

Each rule object must consist of a "name" string. The name may contain '.' characters which are used to differentiate between 
collections of rules known as rulepacks.

Optionally, a rule object may include a settings object. The expected/supported content of the settings object will depend on the rule. 

Note that rules *may* support being specified multiple times. For example, a rule for finding banned terms or words could support multiple instantiations each with a different word or term specified:

```JSON
{
  "rules": [
    {
       "name" : "rulepack1.bannedword",
       "settings" : {
          "word" : "master"
       }
    },
    {
       "name" : "rulepack1.bannedword",
       "settings" : {
          "word" : "slave"
       }
    }
  ]
}
```

Some rules *may*, however, throw an error if configured more than once. Consult the documentation for a rule for usage instructions. 

To prevent running the same rule multiple times, rulecheck will not load a rule twice if it has the *exact* same settings. In the following run, rulecheck will only load the bannedword rule twice, despite it being specified three times.

```bash
rulecheck -c config1.json -c config2.json ./src/**/*
```

Where config 1.json contains:

```JSON
{
  "rules": [
    {
       "name" : "rulepack1.bannedword",
       "settings" : {
          "word" : "slave"
       }
    }
  ]
}
```

And config2.json contains:

```JSON
{
  "rules": [
    {
       "name" : "rulepack1.bannedword",
       "settings" : {
          "word" : "master"
       }
    },
    {
       "name" : "rulepack1.bannedword",
       "settings" : {
          "word" : "slave"
       }
    }
  ]
}
```

Rulecheck's ability to load multiple configuration files and combine them supports a hierarchical configuration structure. For example, a company may provide a rule set and standard config at the organization level. A team may then apply additional rules and config file for all of their projects. Finally each project may have its own config file. Instead of needing to combine all three config files into a single set (and thus force updates to each project when a higher level policy is changed), rule check can be given all three config files and it takes care of combining the configurations.


#### Specifying Files to Process

The files to process and/or the paths rulecheck will search to find files to process are provided on the command line as the last parameter (it must be the last parameter.) 
The paths are specified in glob format. Recursive searches using '**' are supported. 
In addition, the '?' (any character), '*' (any number of characters), and '[]' (character in range) wildcards are supported.

Multiple files and paths to search can be specified by separating them with spaces. If a space is in a path, enclose the glob in quotation marks.

Alternatively, the files or paths to check can be specified via stdin. Specify '-' as the final parameter to have rulecheck read the list in from stdin.

When searching the paths specified, rulecheck will process any file found with one of the following case-sensitive extensions:
.c, .h, .i, .cpp, .CPP, .cp, .hpp, .cxx, .hxx, .cc, .hh, .c++, .h++, .C, .H, .tcc, .ii, .java, .aj, .cs

To change the list of extensions rulecheck will parse when searching paths, use the -x or --extensions command line option.

Note that extensions are case sensitive and .C and .H are by default treated as C++ source files whereas .c and .h are treated as C source files. 
To change the language to extension mapping see the --register-ext option.

#### Specifying Where Rule Scripts Are

Rules are encouraged to be installed onto the python path using a concept known as "rulepacks." This is covered later in this document. 
However, there are situations where rules may not be installed to the python path. For example, when a rule is under development or when a rule is
created for a single project and is kept in the same revision control system as the source being checked by the rule. For these situations, one or more
paths to rules may be specified on the command line using the -r option. If more than one path is needed, repeat the option on the command line for
each path.

Note that the name of a rule specified in a configuration file may contain part of the path to the rule script itself. For example, if

```JSON
	"name" : "rulepack1.ruleA"
```

is in a configuration file, rulecheck will look for a 'rulepack1/ruleA.py' script to load on the path. 

#### Using Ignore List Files

A single ignore list file may be provided to rulecheck via the -i or --ignorelist command line option.
Ignorelists are created by running rulecheck on the source with the -g or --generatehashes command line option,
capturing the rule violations to a file and then pruning that list to the list of violaions to be ignored.
More information can be found [later in this document](#ignore_lists).

#### Options For Controlling srcml

* '--srcml' to specify the path to the srcml binary. Use this option if srcml is not on the path.
* '--tabs' specifies number of spaces to use when substituting tabs for spaces. This impacts the column numbers reported in rule messages.
* '--register-ext' specifies language to extension mappings used by srcml.
* '--srcml-args' allows for specification of additional options to srcml. Do not specify --tabs or -register-ext options here as they have their own dedicated options described above. This option must be provided within double quotation marks and must start with a leading space.


#### Other Options

* '--Werror' will promote all reported rule warnings to errors.
* '--tabs' specifies number of spaces to use when substituting tabs for spaces. This impacts the column numbers reported in rule messages.
* '-v' for verbose output.
* '--version' prints the version of rulecheck and then exits.
* '--help' prints a short help message and then exits.

___
### Waiving and Ignoring Rule Violations

There are two methods for telling rulecheck to ignore a rule finding for a particular file, line, or element of a file.
The first is to use comments in the source code file to instruct rulecheck on when to disable and reenable a rule.
The second is to use an "ignore list" which allows one to provide this information without modifying the source files.
However, the ignore list method may require additional maintenance as the source code is changes compared to the use of
comments in the source code.

### Source Comment Commands to Rulecheck

- [ ] to be written once feature is implemented.

### <a id="ignore_lists"></a>Ignore Lists

- [ ] to be written (Feature is implemented.)

___
### Rulepacks

- [ ] to be written

This section will describe the concept of rulepacks and provide a bit of the technical context for how they work (python path).

___
### Creating Rules

#### Introduction

Rules are python scripts, organized into rulepacks by the python packaging system. Each rule defines methods that rulecheck will call as appropriate
while it is parsing the files to be checked.

#### Rulepacks

Rulepacks are Python packages of rules. The name of the rule pack is the name of the package. A rulepack must contain an __init__.py file so it can be
recognized as a Python package. Rulepack authors are encouraged to create pip-installable packages. However, doing so is outside the scope of this guide.

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

SRCML based rules use srcml based tags for parsing and may also use per-line and per-file parsing methods
LINE based rules use per-line parsing and may also use the per-file parsing methods. However, they should not use any of the srcml tag information.
FILE based rules use per-file parsing methods and avoid any other parsing methods.

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

- [ ] to be written

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

___
### Design Choices
___

Note: parsing xml, the visit methods must be named visit_xml_nodename_start|end. The use of xml_ at the start
avoids collisions with visit_file_open and visit_file_line as XML does no allow any nodename to start with 'xml'.
___
### Resources
___
* [srcml](https://www.srcml.org)
* [srcml source](https://github.com/srcML/srcML)
* [lxml](https://lxml.de/)
