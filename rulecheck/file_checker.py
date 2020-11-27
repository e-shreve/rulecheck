import shutil
import tempfile

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
from rulecheck.verbose import Verbose
from rulecheck import __version__

def print_summary(logger:Logger, file_manager:FileManager):
    """Prints summary information of rule findings."""
    print("Total Files Checked: " + str(file_manager.get_file_count()))
    print("Total Warnings (ignored): " + str(logger.get_warning_count()) + "("
          + str(logger.get_ignored_warning_count()) + ")")
    print("Total Errors (ignored): " + str(logger.get_error_count()) + "("
          + str(logger.get_ignored_error_count()) + ")")

def create_srcml(args) -> Srcml:
    """A factory to create a Srcml object based on program arguments """
    if args.srcml:
        srcml_bin = shutil.which('srcml', path=args.srcml)
    else:
        srcml_bin = shutil.which('srcml')

    if srcml_bin:
        Verbose.print("srcml binary located at: " + srcml_bin)
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

    return Srcml(srcml_bin, srcml_args)

def register_extensions(srcml:Srcml, extensions) -> int:
    """Registers extension to language mappings with the srcml object"""
    for register_ext in extensions:
        regext = register_ext.split("=")
        if len(regext) == 2:
            srcml.add_ext_mapping('.'+regext[0], regext[1])
        else:
            print("Bad --register-ext option: " + register_ext)
            return 1

    Verbose.print("Extension to language mappings for srcml are: " + \
                  str(srcml.get_ext_mappings()))

    return 0

def configure_logger_options(args):
    """Handle all argument options that impact the logger"""
    global LOGGER  #pylint: disable=global-statement
    LOGGER.set_tab_size(args.tabs)
    LOGGER.set_show_hash(args.showhashes)
    LOGGER.set_warnings_are_errors(args.Werror)


def check_files_command(args) -> int:
    """Run rule check using specified command line arguments. Returns exit value.
       0 = No errors, normal program termination.
       1 = Internal rulecheck error
       2 = At least one rule reported an error
       3 = At least one rule reported a warning but no rules reported an error
    """

    global LOGGER  #pylint: disable=global-statement

    srcml = create_srcml(args)

    if srcml is None:
        return 1

    if args.register_ext:
        if not register_extensions(srcml, args.register_ext) == 0:
            return 1

    ignore_file_input = IgnoreFile()
    if args.ignorelist:
        Verbose.print("Ignore list input specified: " + args.ignorelist)
        ignore_list_file_handle = open(args.ignorelist, "r")
        try:
            ignore_file_input.set_file_handle(ignore_list_file_handle)
            ignore_file_input.load()
        finally:
            ignore_list_file_handle.close()

    ignore_filter = IgnoreFilter(ignore_file_input)

    configure_logger_options(args)
    LOGGER.set_ignore_filter(ignore_filter)

    Rule.set_logger(log_violation_wrapper)

    rule_manager = RuleManager(LOGGER, ignore_filter)

    rule_manager.load_rules(args.config, args.rulepaths)

    file_manager = FileManager(rule_manager, srcml, LOGGER)

    ignore_list_out_temp = None
    if args.generateignorefile:
        Verbose.print("Ignore list output specified: " + args.generateignorefile)

        ignore_file_output = IgnoreFile()

        # Create in tempfile first
        ignore_list_out_temp = tempfile.TemporaryFile(mode="w+")
        ignore_file_output.set_file_handle(ignore_list_out_temp)
        LOGGER.set_ignore_file_out(ignore_file_output)
        file_manager.set_ignore_file_out(ignore_file_output)

    # Flatten list of lists in args.sources and pass to process_files
    try:
        file_manager.process_files([item for sublist in args.sources for item in sublist])
    except Exception as ex:
        if ignore_list_out_temp:
            ignore_list_out_temp.close()
        raise ex

    if args.generateignorefile:
        try:
            Verbose.print("Writing new ignore list file: " + args.generateignorefile)
            ignore_list_out_file_handle = open(args.generateignorefile, "w")
            try:
                shutil.copyfileobj(ignore_list_out_temp, ignore_list_out_file_handle)
            finally:
                ignore_list_out_file_handle.close()
        finally:
            ignore_list_out_temp.close()

    if args.verbose:
        print_summary(LOGGER, file_manager)

    if LOGGER.get_error_count() > 0:
        return 2
    if LOGGER.get_warning_count() > 0:
        return 3

    return 0
