import shutil

# Local imports
from rulecheck.srcml import Srcml
from rulecheck.file_manager import FileManager
from rulecheck.rule_manager import RuleManager
from rulecheck.logger import Logger
from rulecheck.logger import LOGGER
from rulecheck.logger import log_violation_wrapper
from rulecheck.ignore import IgnoreFile
from rulecheck.ignore import IgnoreFilter
from rulecheck.rule import Rule
from rulecheck import __version__

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

def check_files_command(args, verbose:bool) -> int:
    """Run rule check using specified command line arguments. Returns exit value.
       0 = No errors, normal program termination.
       1 = Internal rulecheck error
       2 = At least one rule reported an error
       3 = At least one rule reported a warning but no rules reported an error
    """

    global LOGGER
    global VERBOSE_ENABLED

    VERBOSE_ENABLED = verbose

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

    ignore_file_input = IgnoreFile(VERBOSE_ENABLED)
    if args.ignorelist:
        print_verbose("Ignore list input specified: " + args.ignorelist)
        ignore_list_file_handle = open(args.ignorelist, "r")
        ignore_file_input.set_file_handle(ignore_list_file_handle)
        ignore_file_input.load()
        ignore_list_file_handle.close() #TODO use try finally to close

    ignore_filter = IgnoreFilter(ignore_file_input, VERBOSE_ENABLED)

    LOGGER.set_tab_size(args.tabs)
    LOGGER.set_show_hash(args.showhashes)
    LOGGER.set_warnings_are_errors(args.Werror)
    LOGGER.set_ignore_filter(ignore_filter)
    LOGGER.set_verbose(VERBOSE_ENABLED)

    Rule.set_logger(log_violation_wrapper)

    rule_manager = RuleManager(LOGGER, ignore_filter, VERBOSE_ENABLED)

    rule_manager.load_rules(args.config, args.rulepaths)

    file_manager = FileManager(rule_manager, srcml, LOGGER, VERBOSE_ENABLED)

    ignore_list_out_file_handle = None
    if args.generateignorefile:
        print_verbose("Ignore list output specified: " + args.generateignorefile)
        ignore_list_out_file_handle = open(args.generateignorefile, "w")
        ignore_file_output = IgnoreFile(VERBOSE_ENABLED)
        ignore_file_output.set_file_handle(ignore_list_out_file_handle)
        LOGGER.set_ignore_file_out(ignore_file_output)
        file_manager.set_ignore_file_out(ignore_file_output)

    # Flatten list of lists in args.sources and pass to process_files
    file_manager.process_files([item for sublist in args.sources for item in sublist])


    if ignore_list_out_file_handle:
        ignore_list_out_file_handle.close() # TODO use try/finally to close

    if VERBOSE_ENABLED:
        print_summary(LOGGER, file_manager)

    if LOGGER.get_error_count() > 0:
        return 2
    if LOGGER.get_warning_count() > 0:
        return 3

    return 0
