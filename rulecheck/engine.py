import argparse
import shutil
import sys

# Local imports
from rulecheck.srcml import Srcml
from rulecheck.file_manager import FileManager
from rulecheck.rule_manager import RuleManager
from rulecheck.logger import Logger
from rulecheck.logger import LOGGER
from rulecheck.logger import log_violation_wrapper
from rulecheck.ignore import IgnoreFilter
from rulecheck.rule import Rule
from rulecheck import __version__

#pylint: disable=missing-function-docstring
#pylint: disable=too-many-arguments
#pylint: disable=too-many-instance-attributes


#################################################
##
## Globals
##
#################################################

VERBOSE_ENABLED: bool


def print_verbose(message:str):
    global VERBOSE_ENABLED
    if VERBOSE_ENABLED:
        print(message)

def print_summary(logger:Logger, file_manager:FileManager):
    print("Total Files Checked: " + str(file_manager.get_file_count()))
    print("Total Warnings (ignored): " + str(logger.get_warning_count()) + "("
          + str(logger.get_ignored_warning_count()) + ")")
    print("Total Errors (ignored): " + str(logger.get_error_count()) + "("
          + str(logger.get_ignored_error_count()) + ")")





def create_parser():
    parser = argparse.ArgumentParser()
    parser.description = "Tool to run rules on code."
    parser.add_argument("-c", "--config",
                        help="""config file. Specify the option multiple times to specify
                                multiple config files.""",
                        required=True, action="append", type=str)
    parser.add_argument("-r", "--rulepaths",
                        help="""path to rules. Specify the option multiple times to specify
                                multiple paths.""",
                        action="append", type=str)
    parser.add_argument("-g", "--generatehashes",
                        help="output messages with hash values used for ignore files",
                        action="store_true")
    parser.add_argument("--srcml", help="path to srcml, required if srcml not in path",
                        nargs=1, type=str)
    parser.add_argument("--register-ext",
                        help="""specify extension to language mappings used with srcml.
                                --register-ext EXT=LANG""",
                        action="append", type=str)
    # The srmclargs value must be quoted and start with a leading space because of this bug in
    # argparse: https://bugs.python.org/issue9334
    parser.add_argument("--srcmlargs",
                        help="""additional arguments for srcml. MUST BE QUOTED AND START WITH A
                              LEADING SPACE. Note that rulecheck will automatically handle the
                              --language option based on --register-ext parameters to rulecheck.
                              Also, --tabs has its own dedicated option.""",
                        default="--position --cpp-markup-if0", nargs=1, type=str)
    parser.add_argument("--tabs", help="number of spaces used for tabs", default=4, type=int)
    parser.add_argument("--Werror", help="all warnings will be promoted to errors",
                        action="store_true", default=False)
    parser.add_argument("-i", "--ignorelist", help="file with rule violations to ignore",
                        default = "", type=str)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s '+ __version__)
    parser.add_argument("sources",
                        help="""globs source file(s) and/or path(s). ** can be used to represent any
                                number of nested (non-hidden) directories. If '-' is specified,
                                file list is read from stdin.""",
                        nargs='*', action="append", type=str)

    return parser

def create_srcml(args) -> Srcml:
    if args.srcml:
        srcml_bin = shutil.which('srcml', path=args.srcml)
    else:
        srcml_bin = shutil.which('srcml')

    if srcml_bin:
        print_verbose("srcml binary located at: " + srcml_bin)
    else:
        print("Could not locate srcml binary!")
        if args.srcml:
            print("srcml path was specified as: " + args.srcml)
        else:
            print("system path was searched")
        return None

    srcml_args = []
    if args.srcmlargs:
        srcml_args.extend(args.srcmlargs.split())

    if args.tabs:
        srcml_args.append("--tabs=" + str(args.tabs))

    return Srcml(srcml_bin, srcml_args, VERBOSE_ENABLED)

def rulecheck(args) -> int:
    """Run rule check using specified command line arguments. Returns exit value.
    0 = No errors, normal program termination.
    1 = Internal rulecheck error
    2 = At least one rule reported an error
    3 = At least one rule reported a warning but no rules reported an error
    """
    global LOGGER
    global VERBOSE_ENABLED

    VERBOSE_ENABLED = False
    if args.verbose:
        VERBOSE_ENABLED = True

    srcml = create_srcml(args)

    if srcml is None:
        return 1

    if args.register_ext:
        for register_ext in args.register_ext:
            regext = register_ext.split("=")
            if len(regext) == 2:
                srcml.add_ext_mapping('.'+regext[0], regext[1])
            else:
                print("Bad --register-ext option: " + register_ext)
                return 1

        print_verbose("Extension to language mappings for srcml are: " + \
                      str(srcml.get_ext_mappings()))

    ignore_list_file_handle = None
    if args.ignorelist:
        print_verbose("Ignore list specified: " + args.ignorelist)
        ignore_list_file_handle = open(args.ignorelist, "r")

    ignore_filter = IgnoreFilter(ignore_list_file_handle, VERBOSE_ENABLED)

    LOGGER.set_tab_size(args.tabs)
    LOGGER.set_show_hash(args.generatehashes)
    LOGGER.set_warnings_are_errors(args.Werror)
    LOGGER.set_ignore_filter(ignore_filter)
    LOGGER.set_verbose(VERBOSE_ENABLED)

    Rule.set_logger(log_violation_wrapper)

    rule_manager = RuleManager(LOGGER, ignore_filter, VERBOSE_ENABLED)

    rule_manager.load_rules(args.config, args.rulepaths)

    file_manager = FileManager(rule_manager, srcml, LOGGER, VERBOSE_ENABLED)

    # Flatten list of lists in args.sources and pass to process_files
    file_manager.process_files([item for sublist in args.sources for item in sublist])


    if ignore_list_file_handle:
        ignore_list_file_handle.close()

    if VERBOSE_ENABLED:
        print_summary(LOGGER, file_manager)

    if LOGGER.get_error_count() > 0:
        return 2
    if LOGGER.get_warning_count() > 0:
        return 3

    return 0

def main():
    parser = create_parser()
    args = parser.parse_args()
    result = rulecheck(args)
    sys.exit(result)
