import pytest

from rulecheck.engine import rulecheck
from rulecheck.engine import create_arg_parser

#pylint: disable=redefined-outer-name

@pytest.fixture
def parser():
    """ Pytest fixture for generating the parser """
    return create_arg_parser()


@pytest.mark.skip(reason="test not finished")
def test_rule_instantiation_failure(parser, capsys):
    """Confirms that error is printed and program exits with error code if a rule specified
       in a config file can't be created.
    """

@pytest.mark.skip(reason="test not finished")
def test_verbose_mode(parser, capsys):
    """Confirms verbose mode prints summary information."""

@pytest.mark.skip(reason="test not finished")
def test_version(parser, capsys):
    """Confirms version number is printed with version argument."""

@pytest.mark.skip(reason="test not finished")
def test_file_extension_options(parser, capsys):
    """Confirms operation of --register-ext and --extensions options."""

@pytest.mark.skip(reason="test not finished")
def test_file_globs_via_stdin(parser, capsys):
    """Confirm that if '-' is specified as the last parameter, the glob list is
       taken from stdin.
    """

@pytest.mark.skip(reason="test not finished")
def test_help_is_provided(parser, capsys):
    """Confirm that all options are mentioned in help text."""

@pytest.mark.skip(reason="test not finished")
def test_werror(parser, capsys):
    """Confirm that all warnings are promoted to errors when --werror is specified."""

@pytest.mark.skip(reason="test not finished")
def test_rule_path_not_found(parser, capsys):
    pass

@pytest.mark.skip(reason="test not finished")
def test_rule_not_found(parser, capsys):
    pass

@pytest.mark.skip(reason="test not finished")
def test_config_file_not_found(parser, capsys):
    pass

@pytest.mark.skip(reason="test not finished")
def test_srcml_not_found(parser, capsys):
    pass

@pytest.mark.skip(reason="test not finished")
def test_config_file_has_no_rules(parser, capsys):
    pass

@pytest.mark.skip(reason="test not finished")
def test_file_not_found(parser, capsys):
    """Confirm that error is logged, but processing continues if a specified file is not found."""
