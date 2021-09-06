![Python package](https://github.com/e-shreve/rulecheck/workflows/Python%20package/badge.svg)  ![Upload Python Package](https://github.com/e-shreve/rulecheck/workflows/Upload%20Python%20Package/badge.svg)

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
* [Credits](#credits)

To learn how to write your own rules, see [how to create rules](how_to_create_rules.md).
___
### Installation

Ensure [srcml](#srcml), Python 3.6 or greater, and pip are present on the system and then run:
```
pip install rulecheck
```

#### Dependencies

##### Python
Python 3.6 or greater is required.

##### srcml
srcml is a source code to xml parser that can parse C, C++, C Preprocessor, C#, and Java code. 
The pip install of rulecheck will not install srcml. Find installation files at 
https://www.srcml.org/ and install on your system.
Version required: 1.0.0 or greater.
For easiest use, srcml should be on the path. Otherwise, the path to srcml can be provided when
starting rulecheck from the command line.

##### lxml
The python xml library lxml is used over the built-in ElementTree library due to speed and additional functionality such as the ability
to obtain the line number of tag from the source XML file. lxml has been available in Wheel install format since 2016
and thus should not present an issue for users. lxml will be installed by pip automatically when
installing rulecheck.

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

Optionally, a rule object may include a settings object. The full list of settings supported depends
on the particular rule. However, all rules support the following settings:
- werror: if value evaluates as true, it promotes all WARNINGS to ERRORS
- verbose: if value evaluates as true, the rule may provide additional output on stdout

True values are y, yes, t, true, on and 1; false values are n, no, f, false, off and 0. 

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
The following example will process any file contained in the src directory tree (including in subdirectories):

```bash
rulecheck -c config.json ./src/**/*
```

This example will process any file in the src directory tree ending with .h or .c (but not .H, .C, or any other extension):

```bash
rulecheck -c config.json ./src/**/*.[ch]
```

Multiple files and paths to search can be specified by separating them with spaces. If a space is in a path, enclose the glob in quotation marks.

Alternatively, the files or paths to check can be specified via stdin. Specify '-' as the final parameter to have rulecheck read the list in from stdin.

```bash
find ./src/ -type f -name "*.c" | rulecheck -c config.json -
```

When processing the paths and/or files specified, rulecheck will process any file found with one of the following case-sensitive extensions:
.c, .h, .i, .cpp, .CPP, .cp, .hpp, .cxx, .hxx, .cc, .hh, .c++, .h++, .C, .H, .tcc, .ii, .java, .aj, .cs

To change the list of extensions rulecheck will parse when searching paths, use the -x or --extensions command line option.

Note that extensions are case sensitive and .C and .H are by default treated as C++ source files whereas .c and .h are treated as C source files. 
To change the language to extension mapping see the --register-ext option.

#### Specifying Where Rule Scripts Are

Rules are encouraged to be installed onto the python path using a concept known as [rulepacks](#rulepacks). This is covered later in this document. 
However, there are situations where rules may not be installed to the python path. For example, when a rule is under development or when a rule is
created for a single project and is kept in the same revision control repository as the source being checked by the rule. For these situations, one or more
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
void myFunction4(int a); // NORC(myrulepack.function_name_prefix): Function name required for backward compatibility.
```

Note that whitespace between NORC/NORCNEXTLINE and the opening parenthesis are not allowed.

### <a id="ignore_lists"></a>Ignore Lists

Ignore lists provide a means to suppress rule violation messages without modifying the source code
containing the violation. Rulecheck provides for the creation of an ignore list and provides
for the modification of the ignore list based on source file diffs.

Ignore list entries will suppress the violation message for a given line in a source file as
long as no characters of that line have changed. Leading whitespace is included in this check
for some rules, but not for other rules (each rule may declare itself as leading whitespace
sensitive or not.) For rules which ignore leading whitespace, this allows ignore entries to continue
to work even if a line has had its indentation level changed (for example by surrounding it a new
if clause.) 

#### Ignore List Contents
Ignore lists are simple text files (enabling easy editing by hand should the need arise) with each
line typically containing a single ignore list entry. An ignore list entry (henceforth referred to
as an "entry") consists of the following elements, in order, and separated by colons and a single space (': '):
* Unique hash ID (must begin the line, no leading white space allowed)
  * The hash is over the file's name, the rule's name, the violation type, and the source line's contents (with or without leading whitespace depending on the rule's properties.)
* Path of file with violation, with line and column number information, if relevant to violation
  * Column information is provided for readability only and is not used by rulecheck
* Violation type (ERROR or WARNING)
* Rule name
* Violation message (may contain line breaks and colons)

#### Creating an Ignore List
Use the -g option to specify an output file in which rulecheck should write ignore list entries.
Rulecheck will _overwrite_ the destination file with an entry for _every_ violation encountered
during the execution of the rules. 

To quickly ignore all violations in an existing code base and start enforcing the rules on new
code only, simply generate an ignore list on the existing code and use it on all subsequent runs.

While somewhat obvious, keep in mind that only entries for rule violations of rules and rule 
configurations currently configured will be generated.   

#### Using Ignore Lists
Use the -i option to specify an input ignore list. 

#### Adding New Entries to an Existing Ignore List
Specify -i option to provide the existing ignore list and specify -g option to create a new list
file. Use any text diff utility to compare the files and selectively move any desired entries in the new
list into the existing list. 

#### Finding and Removing Unused Ignore List Entries
Use the -g option to generate a new ignore list file. Use any text comparison/diff utility to
compare the new file to the old ignore list file. Any entries in the old file that are not in the
new file are unused. You may simply delete those entries in the old file. 

#### Updating Ignore Lists for Line Number Changes
Rulecheck includes a feature to modify an ignore list file to accommodate line number changes in
source files. _Note:_ ignore list entries do not match on column numbers, column numbers are
provided for human readability only. _Note:_ only diff/patch files generated by git have been
tested. However, svn and hg are expected to also work.

Use the -p option to activate this feature. 

The easiest way to use this feature is to pipe the version control diff into rulecheck, by 
specifying '-' for the -p option.

```bash
git diff -U0 ./tests/src/network/err.c | rulecheck -p - -i ignore.txt 
```

_Note_ the use of -U0 with git diff to provide no extra context in the diff, resulting in only the
lines changed being present in the diff output (Git defaults to 3 context lines). For proper operation,
this must be done. 

If it is undesirable to modify the ignore list file, use the -g option to specify a new file to
write the output to.

The other way to use this feature is to generate patch files and then provide those patch files to
rulecheck. One or more globs to patch files may be specified. In order to provide appropriate line
number updates, the order of the patch files matter. Thus, patch files must properly sort by filename
according to their application order. Further, if multiple globs are provides to rulecheck, they must
be in the order in which the patches should be applied.

```bash
git format-patch -U0 HEAD~2
rulecheck -p *.patch -i ignore.txt
```

Again, note that U0 must be used to ensure the patch files do not contain extra context lines.



___
### <a id="rulepacks"></a>Rulepacks

- [ ] to be written

This section will describe the concept of rulepacks and provide a bit of the technical context for how they work (python path).

___


___
### <a id="design"></a>Design Choices
___

rulecheck intentionally does not support modification of the files parsed. Doing so would require rulecheck to 
repeatedly run modified files through all rules until no new log messages were produced. However, a modification
made by one rule could trigger another rule to be violated. Further, it is anticipated that many rules
written for rulecheck will either not be automatically fixable by simple formatting rules or simple
formatting modifications will too often undo formatting that was carefully considered by the source
author.
___
### Resources
___
* [srcml](https://www.srcml.org)
* [srcml source](https://github.com/srcML/srcML)
* [lxml](https://lxml.de/)
___
### <a id="credits"></a>Credits
___
* rulecheck includes and uses [Python Patch](https://pypi.python.org/pypi/patch), a library that can parse Git (and other) diffs.
* rulecheck depends on [SrcML](https://www.srcml.org/) for source code parsing.
