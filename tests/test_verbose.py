'''
Tests for verbose module
'''

import pytest

from rulecheck.verbose import Verbose

def test_verbose(capsys):
    """ Confirm prints only when verbosity is set to true """
    Verbose.set_verbose(False)
    Verbose.print('test message')
    captured = capsys.readouterr()
    assert 'test message' not in captured.out

    Verbose.set_verbose(True)
    Verbose.print('test message')
    captured = capsys.readouterr()
    assert 'test message' in captured.out
