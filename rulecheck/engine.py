import argparse
import sys

# Local imports
from rulecheck.file_checker import check_files_command
from rulecheck.ignore import ignorelist_update_command
from rulecheck.verbose import Verbose
from rulecheck import __version__


def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.description = "Tool to run rules on code."

    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument("-c", "--config",
                        help="""config file. Specify the option multiple times to specify
                                multiple config files.""",
                        action="append", type=str)
    command_group.add_argument("-p", "--patch_ignore",
                               help="""patch an ignore list with patch
                                       files of the source or diff entries on stdin. Either, provide
                                       a glob to the patch files or use '-' to indicate the diff
                                       entries will be provided on stdin.
                                       Specify multiple times to specify multiple in-order
                                       globs to use.
                                       Use -i to specify ignore file to update (file will be 
                                       overwritten.) Optionally use -g to specify a new file
                                       to write the updated ignores to (file will be overwritten.)
                                       """,
                               nargs='*', action="append", type=str)

    parser.add_argument("-r", "--rulepaths",
                        help="""path to rules. Specify the option multiple times to specify
                                multiple paths.""",
                        action="append", type=str)
    parser.add_argument("--showhashes",
                        help="output messages to console with hash values used for ignore files",
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
    parser.add_argument("-i", "--ignorelist", help="file with rule violations to ignore or update",
                        default = "", type=str,
                        required=('--patch_ignore' in sys.argv or '-p' in sys.argv))
    parser.add_argument("-g", "--generateignorefile",
                        help="""output ignore list entries to specified file,
                                file contents will be overwritten""",
                        default = "", type=str)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s '+ __version__)
    parser.add_argument("sources",
                        help="""globs source file(s) and/or path(s). ** can be used to represent any
                                number of nested (non-hidden) directories. If '-' is specified,
                                file list is read from stdin.""",
                        nargs='*', action="append", type=str)

    return parser


def rulecheck(args) -> int:

    if args.verbose:
        Verbose.set_verbose(args.verbose)

    if args.config:
        return check_files_command(args)
    if args.patch_ignore:
        return ignorelist_update_command(args)

    return -1



def main():
    parser = create_arg_parser()
    args = parser.parse_args()
    result = rulecheck(args)
    sys.exit(result)
