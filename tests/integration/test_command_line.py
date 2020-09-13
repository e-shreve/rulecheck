'''
Created on Sep 7, 2020

@author: Erik
'''

import re
import pytest
from rulecheck import __version__

@pytest.mark.script_launch_mode('subprocess')
def test_version(script_runner):
    """ This integration tests confirms version reporting
    """
    result = script_runner.run('rulecheck', '--version')
    assert result.success
    assert __version__ in result.stdout


@pytest.mark.script_launch_mode('subprocess')
def test_all_the_things(script_runner):
    """This integration tests confirms many items at once.
    1. Multiple configuration files can be loaded
    2. Multiple instantiation of the same rule can be done
    3. If a rule is specified twice with the same settings, it is not instantiated twice
    4. Multiple file globs can be specified
    5. Confirms that globs can be specified to recurse folder structure
    6. Tests that a rule throwing an exception during file processing results in an Error logged
       but the processing continues.
    7. Confirms rule path setting operation.
    8. Confirms werror rule-level setting (not command line level setting)
    9. Confirms verbose rule-level setting
    """
    result = script_runner.run('rulecheck',
                               '-v',
                               '-c', './tests/integration/rules1.json',
                               '-c', './tests/integration/rules2.json',
                               '--rulepaths', './tests',
                               r'./tests/src/basic utils/main.c',
                               r'./tests/src/network/**/*')

    assert result.returncode == 2 # 2 indicates error level violations found

    # Check that rule path was added:
    assert re.search(r'Adding to sys\.path: [^\n]*[/\\]tests', result.stdout)

    # Check loading of both config, with appropriate rules loaded and skipped
    assert re.search(r'From \.[/\\]tests[/\\]integration[/\\]rules1\.json loaded 3 rules: \n[^\n]*[/\\]rulepack1\.printFilename\n[^\n]*[/\\]rulepack1\.printRowsWithWord\n[^\n]*[/\\]rulepack1\.printRowsWithWord', result.stdout)  #pylint: disable=line-too-long
    assert re.search(r'From \.[/\\]tests[/\\]integration[/\\]rules2\.json loaded 2 rules: \n[^\n]*[/\\]rulepack1\.printRowsWithWord\n[^\n]*[/\\]rulepack1\.printLanguage', result.stdout) #pylint: disable=line-too-long
    assert re.search(r'From \.[/\\]tests[/\\]integration[/\\]rules2\.json skipped 2 rules already loaded: \n[^\n]*[/\\]rulepack1\.printFilename\n[^\n]*[/\\]rulepack1\.printRowsWithWord', result.stdout) #pylint: disable=line-too-long


    # Check that faulty rule (that throws exception) is noted:
    assert 'Could not load rule: rulepack2.badRuleThrowsException'  in result.stdout
    assert 'Exception on attempt to load rule: I always raise this.' in result.stdout

    # Check that all files were processed
    assert r'Total Files Checked: 5' in result.stdout
    assert re.search(r'Opened file for checking: .[/\\]tests[/\\]src[/\\]basic utils[/\\]main.c', result.stdout)                  #pylint: disable=line-too-long
    assert re.search(r'Opened file for checking: .[/\\]tests[/\\]src[/\\]network[/\\]err.c', result.stdout)                       #pylint: disable=line-too-long
    assert re.search(r'Opened file for checking: .[/\\]tests[/\\]src[/\\]network[/\\]tcp[/\\]tcp-sink-server.c', result.stdout)   #pylint: disable=line-too-long
    assert re.search(r'Opened file for checking: .[/\\]tests[/\\]src[/\\]network[/\\]udp[/\\]udp-client.c', result.stdout)        #pylint: disable=line-too-long
    assert re.search(r'Opened file for checking: .[/\\]tests[/\\]src[/\\]network[/\\]udp[/\\]udp-server.c', result.stdout)        #pylint: disable=line-too-long

    # Check per-rule verbose worked
    assert r'printRowsWithWord created for word: udp' in result.stdout
    assert r'printRowsWithWord created for word: tcp' not in result.stdout

    # Check summary results. Expect one error, which would be from using a per-rule werror setting
    assert r'Total Warnings (ignored): 13(0)' in result.stdout
    assert r'Total Errors (ignored): 1(0)' in result.stdout
