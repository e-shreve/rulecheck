![Python package](https://github.com/e-shreve/rulecheck/workflows/Python%20package/badge.svg)

# Rule Check
Rule Check (aka rulecheck or source rule check) is a command line system for running custom static analysis rules on C, C++, C#, and Java code. The original use case is checking a code base against coding style or coding standard rules. 

Rule Check uses [srcml](https://www.srcml.org/) to parse the source code into XML and then invokes each rule's methods as appropriate to allow the rules to inspect any source code element of interest to the rule. This architecture minimizes duplicate parsing time and allows rule authors to focus on their rule logic instead of the logic needed to parse source code.

Features include:
* Parsing C, C++, C#, and Java source via srcml
* Parsing C and C++ prior to preprocessor execution (thus viewing code as developers do)
* Custom rules
  * Groups of rules can be created and published in 'rulepacks'
  * Projects can have custom rules within their own code base (no need to publish/install rules)
  * Rules can have their own custom settings. Rule check will provide the settings to the rule via its standard config file format.
* Multiple config file inputs
  * Projects can use an hierarchical set of configurations allowing organizations to provide rules across projects
* Supression of errors and warnings without modifying source code via ignore list input
* Supression of errors and warnings with source code comments
* Standardized output format for all rules
* Speicifcation of sources to be analyzed via glob format or via stdin

___

### Contents
___
* [Installation](#installation)
* [Running and Configuration](#running)
* [Design Choices](#design)
* [Resources](#resources)

To learn how to write your own rules, see [how to create rules](how_to_create_rules.md).
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

##### srcml
srcml is a source code to xml parser that can parse C, C++, C Preprocessor, C#, and Java code. The pip install of rulecheck will not
install srcml. Find installation files at https://www.srcml.org/ and install on your system.
Version required: 1.0.0 or greater.
For easiest use, srcml should be on the path. Otherwise, the path to srcml can be provided when starting rulecheck from the command line.

##### lxml
The python xml library lxml is used over the built-in ElementTree library due to speed and additional functionality such as the ability
to obtain the line number of tag from the source XML file. lxml has been available in Wheel install format since 2016
and thus should not present an issue for users. lxml will be installed by pip automatically when insalling rulecheck.

___
### <a id="running">Running and Configuration
___

```
rulecheck --help
```

#### Selecting Rules

Rules are selected by specifying one or more rule configuration files on the command line, using the -c or --config option. To specify more than one configuration file, use the config option on the command line once for each configuration file to be read.

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

Some rules *may*, however, throw an error if configured more than once. Consult the documentation of a rule for specific usage instructions. 

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
However, the ignore list method may require additional maintenance as the source code is changed compared to the use of
comments in the source code.

### Source Comment Commands to Rulecheck

A NORC comment is used to have rulecheck ignore violations reported for the same line the comment is on. The NORCNEXTLINE comment will cause rulecheck to ignore violations on the next line.

Both comments must include an open and closed parenthesis containing either the '\*' character or a comma
separated list of rules to be ignored. Use of the '\*' character will cause all rules to be suppressed.

For example:
```C

// Ignore all violations on the line:
void myFunction1(int a); // NORC(*)

// Ignore all violations on the next line:
// NORCNEXTLINE(*)
void myFunction2(int a); 

// Specific rules can be ignored:
// NORCNEXTLINE(myrulepack.rule1, myrulepack.rule2)
void myFunction3(int a); 

// Comments after the closing parenthesis may contain any text.
// It is good practice to justify the suppression.
void myFunction4(int a); // NORC(myrulepack.function\_name\_prefix): Function name required for backward compatibility.
```

Note that whitespace between NORC/NORCNEXTLINE and the opening parenthesis are not allowed.

### <a id="ignore_lists"></a>Ignore Lists

- [ ] to be written (Feature is implemented.)

___
### Rulepacks

- [ ] to be written

This section will describe the concept of rulepacks and provide a bit of the technical context for how they work (python path).

___


___
### <a id="design"></a>Design Choices
___

rulecheck intentionally does not support modification of the files parsed. Doing so would require rulecheck to 
repeatedly run modified files through all rules until no new log messages were produced. However, a modification
made by one rule could trigger another rule to be violated. Thus, the execution might never terminate. In addition,
many coding standard rules that can be automatically fixed deal strictly with whitespace and there are already many
tools and IDEs that support formatting of whitespace to any imaginable standard.
___
### Resources
___
* [srcml](https://www.srcml.org)
* [srcml source](https://github.com/srcML/srcML)
* [lxml](https://lxml.de/)
