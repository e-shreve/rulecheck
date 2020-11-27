import pytest

from rulecheck.engine import rulecheck
from rulecheck.engine import create_arg_parser

#pylint: disable=redefined-outer-name

@pytest.fixture
def parser():
    """ Pytest fixture for generating the parser """
    return create_arg_parser()

#TODO: Add to this test, as features are implemented:
# Per rule werror, per rule strict mode
@pytest.mark.skip(reason="test not finished")
def test_all_the_things(parser, capsys):
    """This integration tests confirms many items at once.
    1. Multiple configuration files can be loaded
    2. Multiple instantiation of the same rule can be done
    3. If a rule is specified twice with the same settings, it is not instantiated twice
    4. Multiple file globs can be specified
    5. Confirms that globs can be specified to recurse folder structure
    6. Tests that a rule throwing an exception during file processing results in an Error logged
       but the processing continues.
    7. Confirms rule path setting operation.
    """
    args = parser.parse_args(['-v',
                              '-c', '.\\tests\\integration\\rules1.json',
                              '-c', '.\\tests\\integration\\rules2.json',
                              '--rulepaths', '.\\tests',
                              '.\\tests\\src\\path1\\basic-utils\\main.c',
                              '.\\tests\\src\\path1\\network'])
    rulecheck(args)
    captured = capsys.readouterr()
    assert "common.c:WARNING:rulepack1.printFilename:Visited file: .\\tests\\src\\path1\\basic-utils\\common.c" \
        in captured.out

def test_rule_instantiation_failure(parser, capsys):
    """Confirms that error is printed and program exits with error code if a rule specified
       in a config file can't be created.
    """


def test_verbose_mode(parser, capsys):
    """Confirms verbose mode prints summary information."""

def test_version(parser, capsys):
    """Confirms version number is printed with version argument."""

def test_file_extension_options(parser, capsys):
    """Confirms operation of --register-ext and --extensions options."""


def test_file_globs_via_stdin(parser, capsys):
    """Confirm that if '-' is specified as the last parameter, the glob list is
       taken from stdin.
    """


def test_help_is_provided(parser, capsys):
    """Confirm that all options are mentioned in help text."""

def test_werror(parser, capsys):
    """Confirm that all warnings are promoted to errors when --werror is specified."""


def test_rule_path_not_found(parser, capsys):
    pass

def test_rule_not_found(parser, capsys):
    pass

def test_config_file_not_found(parser, capsys):
    pass

def test_srcml_not_found(parser, capsys):
    pass

def test_config_file_has_no_rules(parser, capsys):
    pass

def test_file_not_found(parser, capsys):
    """Confirm that error is logged, but processing continues if a specified file is not found."""
