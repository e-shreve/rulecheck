'''
Tests for Srcml class
'''
import pytest

from rulecheck.srcml import Srcml


def test_extensions():
    """ Test that extensions can be added to the mapping """
    srcml = Srcml('echo', [])
    result = srcml.get_srcml('bad.extension')
    assert result is None

    srcml.add_ext_mapping('.extension', 'Java')
    mappings = srcml.get_ext_mappings()
    assert '.extension' in mappings
    assert mappings['.extension'] == 'Java'

    result = srcml.get_srcml('bad.extension')
    assert '--language Java bad.extension' in result.decode('ascii')


def test_custom_arguments():
    """ Test that custom arguments are passed to the command line"""
    srcml = Srcml('echo', ['testarg1', 'testarg2'])

    result = srcml.get_srcml('good.c')
    assert 'testarg1 testarg2 --language C good.c' in result.decode('ascii')

def test_failed_command(capsys):
    """ Test that a failed command results in message printed to console """

    srcml = Srcml('srcml', ['--nosuchextension'])

    result = srcml.get_srcml('good.c')
    assert result is None
    captured = capsys.readouterr()
    # Won't be too specific on content as srcml may choose to change its output messages
    assert 'error calling srcml' in captured.out
    assert '--nosuchextension' in captured.out
    