'''
Created on Apr 2, 2020

@author: Erik
'''

import sys
import pathlib
import json

import pytest
from rulecheck.engine import RuleManager
from rulecheck.engine import IgnoreFilter
from rulecheck.engine import Srcml
from rulecheck import rule



@pytest.fixture
def rule_manager():
    ignore_filter = IgnoreFilter(None, verbose=False)
    return RuleManager(None, ignore_filter, verbose=False)

def test_no_config(rule_manager):
    """ Confirm that empty/none rule config list does not result in exception """ 
    rule_manager.load_rules([""], ["."])
    rule_manager.load_rules([], ["."])
    
def test_rule_paths_none(rule_manager):
    """ Confirm that none rule_paths list does not result in exception """
    rule_manager.load_rules([], None)
    
# Test rule_paths with one path and with two paths
def test_rule_paths(rule_manager):
    """ Confirm that one or more rule paths can be loaded """
    
    path1 = "./tests/rulepack1"
    rule_manager.load_rules([], [path1])
    abspath1 = str(pathlib.Path(path1).absolute())
    assert abspath1 in sys.path 
    
    sys.path.remove(abspath1)
    
    path2 = "./tests/rulepack2"
    rule_manager.load_rules([], [path1, path2])
    abspath2 = str(pathlib.Path(path2).absolute())
    assert abspath1 in sys.path 
    assert abspath2 in sys.path 
    

def test_config_load_multiple_rules(rule_manager, tmp_path, capsys):
    """Confirm that multiple rules can be loaded from a single config file.
    Also confirm that rules can be loaded both with and without settings
    specified.
    """
    
    config = {}
    config['rules'] = []
    config['rules'].append({
        'name': 'rulepack1.printFilename'
    })
    config['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'the'}
    })
    
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as outfile:
        json.dump(config, outfile)
    
    rule_manager.load_rules([str(config_file)], ['./tests'])
    
    captured = capsys.readouterr()
    assert "Could not load rule" not in captured.out
    assert 'rulepack1.findSingleLineCommentsWith' in rule_manager._rules_dict
    assert 'rulepack1.printFilename' in rule_manager._rules_dict
    

def test_config_load_multiple_configs(rule_manager, tmp_path, capsys):
    """Test two config files with some same and some different rules """
    
    config1 = {}
    config1['rules'] = []
    config1['rules'].append({
        'name': 'rulepack1.printFilename'
    })
    config1['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'the'}
    })
    
    config1_file = tmp_path / "config1.json"
    with open(config1_file, 'w') as outfile:
        json.dump(config1, outfile)
        
        
    config2 = {}
    config2['rules'] = []
    config2['rules'].append({
        'name': 'rulepack1.printFilename'
    })
    config2['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'the'}
    })
    config2['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'different'}
    })    
    config2['rules'].append({
        'name': 'rulepack1.printLanguage'
    })
    
    config2_file = tmp_path / "config2.json"
    with open(config2_file, 'w') as outfile:
        json.dump(config2, outfile)
    
    rule_manager.load_rules([str(config1_file), str(config2_file)], ['./tests'])
    
    captured = capsys.readouterr()
    assert "Could not load rule" not in captured.out
    assert 'rulepack1.findSingleLineCommentsWith' in rule_manager._rules_dict
    assert len(rule_manager._rules_dict['rulepack1.findSingleLineCommentsWith']) == 2
    assert 'rulepack1.printFilename' in rule_manager._rules_dict
    assert len(rule_manager._rules_dict['rulepack1.printFilename']) == 1    
    assert 'rulepack1.printLanguage' in rule_manager._rules_dict


def test_config_file_does_not_exist(rule_manager, capsys):
    """ Confirm error message if config file not found """
    
    rule_manager.load_rules(['__dummy_config.json'], ['./tests'])
    
    captured = capsys.readouterr()
    assert "Could not open config file: __dummy_config.json" in captured.out


    
def test_rule_path_does_not_exist(rule_manager, tmp_path, capsys):
    """ Confirm error message if rule path not found """
    config = {}
    config['rules'] = []
    config['rules'].append({
        'name': 'rulepack1.printFilename'
    })
    config['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'the'}
    })
    
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as outfile:
        json.dump(config, outfile)
    
    rule_manager.load_rules([str(config_file)], ['./tests_does_not_exist'])
    
    captured = capsys.readouterr()
    assert "Rule path not found" in captured.out



def test_missing_rule(rule_manager, tmp_path, capsys):
    """Confirm error printed if rule not found but other rules loaded """
    
    config = {}
    config['rules'] = []
    config['rules'].append({
        'name': 'rulepack1.doesNotExist'
    })
    config['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'the'}
    })
    
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as outfile:
        json.dump(config, outfile)
    
    rule_manager.load_rules([str(config_file)], ['./tests'])
    
    captured = capsys.readouterr()
    assert "Could not load rule: rulepack1.doesNotExist" in captured.out
    assert 'rulepack1.doesNotExist' not in rule_manager._rules_dict
    assert 'rulepack1.findSingleLineCommentsWith' in rule_manager._rules_dict


def test_rule_exception_handling(rule_manager, tmp_path, capsys):
    """Confirm error printed if rule throws exception when created but other rules loaded """
    
    config = {}
    config['rules'] = []
    config['rules'].append({
        'name': 'rulepack2.badRuleThrowsException'
    })
    config['rules'].append({
        'name': 'rulepack1.findSingleLineCommentsWith',
        'settings': {'with_string' : 'the'}
    })
    
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as outfile:
        json.dump(config, outfile)
    
    rule_manager.load_rules([str(config_file)], ['./tests'])
    
    captured = capsys.readouterr()
    assert "Could not load rule: rulepack2.badRuleThrowsException" in captured.out
    assert "I always raise this." in captured.out
    assert 'rulepack2.badRuleThrowsException' not in rule_manager._rules_dict
    assert 'rulepack1.findSingleLineCommentsWith' in rule_manager._rules_dict


def test_file_open(rule_manager, mocker):
    """ Ensure rules with "visit_file_open" are called. """
    rule1 = mocker.MagicMock()
    rule2 = mocker.MagicMock()
      
    rule_manager._rules_dict['rule1'] = [rule1]
    rule_manager._rules_dict['rule2'] = [rule2]
     
    rule_manager.visit_file_open('./tests/src/path2/basic-utils/common.c')
    
    rule1.visit_file_open.assert_called_once_with(rule.LogFilePosition(-1,-1), './tests/src/path2/basic-utils/common.c')
    rule1.visit_file_open.assert_called_once_with(rule.LogFilePosition(-1,-1), './tests/src/path2/basic-utils/common.c')

    # Ensure that both rules got a unique copy of the position argument
    assert rule1.visit_file_open.call_args[0][0] is not rule2.visit_file_open.call_args[0][0]
        


def text_file_lines(rule_manager, mocker):
    """Test operation of visit_file_lines and visit_file_line.
    
    Confirm that rules with "visit_file_line" methods are called and that each
    gets a unique copy of position information and each gets the appropriate line text.
    """
    rule1 = mocker.MagicMock()
    rule2 = mocker.MagicMock()
      
    rule_manager._rules_dict['rule1'] = [rule1]
    rule_manager._rules_dict['rule2'] = [rule2]
     
    with open('./tests/src/path1/basic-utils/common.c', 'r') as file:
        
        source_lines = file.readlines()
        
        rule_manager.visit_file_lines(2, 5, source_lines)
    
        expected_calls = [mocker.call(rule.LogFilePosition(2,-1), source_lines[1]),
                          mocker.call(rule.LogFilePosition(3,-1), source_lines[2]),
                          mocker.call(rule.LogFilePosition(4,-1), source_lines[3]),]
    
        rule1.visit_file_line.assert_has_calls(expected_calls)
        rule2.visit_file_line.assert_has_calls(expected_calls)

        # Ensure correct number of calls (no extra)
        assert rule1.visit_file_line.call_count == 3
        assert rule2.visit_file_line.call_count == 3
        
        # Ensure that both rules got a unique copy of the position argument
        assert rule1.visit_file_line.call_args[0][0] is not rule2.visit_file_line.call_args[0][0]
 

def test_visit_xml(rule_manager, mocker):
    """Test visit of xml node.
    
        Includes testing both start and end events, the 'visit_any_other_xml_element'
        call, and that each call gets its own copy of the Log Position.
    """
    rule1 = mocker.Mock(spec_set=['visit_xml_tag1_start', 'visit_any_other_xml_element_start', 'is_active'])
    rule1.visit_xml_tag1_start = mocker.Mock()
    rule1.visit_any_other_xml_element_start = mocker.Mock()
    rule1.is_active = mocker.Mock(return_value = True)

    rule2 = mocker.Mock(spec_set=['visit_any_other_xml_element_start', 'is_active'])
    rule2.visit_any_other_xml_element_start = mocker.Mock()
    rule2.is_active = mocker.Mock(return_value = True)
    
    rule_manager._rules_dict['rule1'] = [rule1]
    rule_manager._rules_dict['rule2'] = [rule2]
    
    node = mocker.Mock()
    node.tag = "tag1"
    
    position = rule.LogFilePosition(1,5)
    rule_manager.visit_xml(position, node, "start")
    
    # Check that tag specific visit was called on Rule 1 with correct parameters and
    # 'any_other' was called rule 2 with correct parameters.
    rule1.visit_xml_tag1_start.assert_called_once_with(rule.LogFilePosition(1,5), node)
    rule2.visit_any_other_xml_element_start.assert_called_once_with(rule.LogFilePosition(1,5), node)
    # Check that each rule got a unique copy of the Position argument.
    assert rule1.visit_xml_tag1_start.call_args[0][0] is not rule2.visit_any_other_xml_element_start.call_args[0][0]
    assert rule1.visit_xml_tag1_start.call_args[0][0] is not position
    assert rule2.visit_any_other_xml_element_start.call_args[0][0] is not position

    # Confirm total call counts.
    assert rule1.visit_xml_tag1_start.call_count == 1
    assert rule1.visit_any_other_xml_element_start.call_count == 0
    assert rule2.visit_any_other_xml_element_start.call_count == 1

    
    
    node.tag = "tag2"
    
    rule_manager.visit_xml(rule.LogFilePosition(1,5), node, "start")

    assert rule1.visit_xml_tag1_start.call_count == 1
    assert rule1.visit_any_other_xml_element_start.call_count == 1
    assert rule2.visit_any_other_xml_element_start.call_count == 2
    
    node.tag = "tag1"
    
    rule_manager.visit_xml(rule.LogFilePosition(1,5), node, "end")

    assert rule1.visit_xml_tag1_start.call_count == 1
    assert rule1.visit_any_other_xml_element_start.call_count == 1


def test_run_rules_on_file_no_srcml_order(rule_manager, mocker):
    """Confirm order of operations performed by run_rules_on_file
    when srcml is not generated"""
    
    srcml = mocker.Mock(spec_set=['get_srcml'])
    srcml.get_srcml = mocker.Mock(return_value = None)
    
    rule1 = mocker.Mock(spec_set=['visit_file_open', 'visit_file_line', 'visit_file_close', 'visit_any_other_xml_element_start', 'is_active', 'set_active'])
    rule1.visit_file_open = mocker.Mock()
    rule1.visit_file_line = mocker.Mock()
    rule1.visit_file_close = mocker.Mock()
    rule1.visit_any_other_xml_element_start = mocker.Mock()
    rule1.is_active = mocker.Mock(return_value = True)
    rule1.set_active = mocker.Mock()

    rule2 = mocker.Mock(spec_set=['visit_file_open', 'visit_file_line', 'visit_file_close', 'visit_any_other_xml_element_start', 'is_active', 'set_active'])
    rule2.visit_file_open = mocker.Mock()
    rule2.visit_file_line = mocker.Mock()
    rule2.visit_file_close = mocker.Mock()
    rule2.visit_any_other_xml_element_start = mocker.Mock()
    rule2.is_active = mocker.Mock(return_value = True)
    rule2.set_active = mocker.Mock()
    
    rulemocks = mocker.Mock()
    rulemocks.r1, rulemocks.r2 = rule1, rule2
    
    rule_manager._rules_dict['rule1'] = [rule1]
    rule_manager._rules_dict['rule2'] = [rule2]

    rule_manager.run_rules_on_file("file.c", ["line1", "line2", "line3"], srcml)
    filePos = rule.LogFilePosition(-1,-1)
    rulemocks.assert_has_calls([mocker.call.r1.set_active(), mocker.call.r2.set_active(),
                                mocker.call.r1.is_active(), mocker.call.r1.visit_file_open(filePos, 'file.c'),
                                mocker.call.r2.is_active(), mocker.call.r2.visit_file_open(filePos, 'file.c'),
                                mocker.call.r1.is_active(), mocker.call.r1.visit_file_line(rule.LogFilePosition(1,-1), "line1"),
                                mocker.call.r2.is_active(), mocker.call.r2.visit_file_line(rule.LogFilePosition(1,-1), "line1"),
                                mocker.call.r1.is_active(), mocker.call.r1.visit_file_line(rule.LogFilePosition(2,-1), "line2"),
                                mocker.call.r2.is_active(), mocker.call.r2.visit_file_line(rule.LogFilePosition(2,-1), "line2"),
                                mocker.call.r1.is_active(), mocker.call.r1.visit_file_line(rule.LogFilePosition(3,-1), "line3"),
                                mocker.call.r2.is_active(), mocker.call.r2.visit_file_line(rule.LogFilePosition(3,-1), "line3"),
                                mocker.call.r1.is_active(), mocker.call.r1.visit_file_close(filePos, 'file.c'),
                                mocker.call.r2.is_active(), mocker.call.r2.visit_file_close(filePos, 'file.c')])


def test_run_rules_on_file_with_srcml_order(rule_manager, mocker):
    """Confirm order of operations performed by run_rules_on_file
    when srcml is generated"""
    
    srcml_xml = r'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                    <unit xmlns="http://www.srcML.org/srcML/src" xmlns:cpp="http://www.srcML.org/srcML/cpp" xmlns:pos="http://www.srcML.org/srcML/position" revision="1.0.0" language="C" filename=".\main.c" pos:tabs="8"><cpp:include pos:start="1:1" pos:end="1:19">#<cpp:directive pos:start="1:2" pos:end="1:8">include</cpp:directive> <cpp:file pos:start="1:10" pos:end="1:19">"common.h"</cpp:file></cpp:include>

                    <function pos:start="3:1" pos:end="7:1"><type pos:start="3:1" pos:end="3:3"><name pos:start="3:1" pos:end="3:3">int</name></type>
                    <name pos:start="4:1" pos:end="4:4">main</name><parameter_list pos:start="4:5" pos:end="4:10">(<parameter pos:start="4:6" pos:end="4:9"><decl pos:start="4:6" pos:end="4:9"><type pos:start="4:6" pos:end="4:9"><name pos:start="4:6" pos:end="4:9">void</name></type></decl></parameter>)</parameter_list>
                    <block pos:start="5:1" pos:end="7:1">{<block_content pos:start="6:9" pos:end="6:21">
                        <expr_stmt pos:start="6:9" pos:end="6:21"><expr pos:start="6:9" pos:end="6:20"><call pos:start="6:9" pos:end="6:20"><name pos:start="6:9" pos:end="6:18">function_x</name><argument_list pos:start="6:19" pos:end="6:20">()</argument_list></call></expr>;</expr_stmt>
                    </block_content>}</block></function>
                    </unit>'''.encode()
                    
    mocker.patch.object(Srcml, 'get_srcml', lambda a,b: srcml_xml)

    srcml = Srcml("", [], False)
    
    rule1 = mocker.Mock(spec_set=['visit_file_open', 'visit_file_line', 'visit_file_close', 'visit_any_other_xml_element_start', 'visit_any_other_xml_element_end', 'visit_xml_function_start', 'visit_xml_function_end', 'is_active', 'set_active'])
    rule1.visit_file_open = mocker.Mock()
    rule1.visit_file_line = mocker.Mock()
    rule1.visit_any_other_xml_element_start= mocker.Mock()
    rule1.visit_any_other_xml_element_end= mocker.Mock()
    rule1.visit_file_close = mocker.Mock()
    rule1.visit_xml_function_start = mocker.Mock()
    rule1.visit_xml_function_end = mocker.Mock()
    rule1.is_active = mocker.Mock(return_value = True)
    rule1.set_active = mocker.Mock()


    
    rulemocks = mocker.Mock()
    rulemocks.r1 = rule1
    
    rule_manager._rules_dict['rule1'] = [rule1]


    rule_manager.run_rules_on_file("file.c", ['#include "common.h"', "", "int", "main(void)", "{", "    function_x();", "}", ""], srcml)
    filePos = rule.LogFilePosition(-1,-1)
    rulemocks.assert_has_calls([mocker.call.r1.set_active(),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_open(rule.LogFilePosition(-1, -1), 'file.c'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(1, -1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(1, -1), '#include "common.h"'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(1, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(1, 2), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(1, 8), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(1, 10), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(1, 19), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(1, 19), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(2, -1), ''),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(3, -1), 'int'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_xml_function_start(rule.LogFilePosition(3, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(3, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(3, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(3, 3), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(3, 3), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(4, -1), 'main(void)'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(4, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(4, 4), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(4, 5), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(4, 6), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(4, 6), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(4, 6), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(4, 6), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(4, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(4, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(4, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(4, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(4, 10), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(5, -1), '{'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(5, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(6, -1), '    function_x();'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(6, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(6, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(6, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(6, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(6, 9), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(6, 18), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_start(rule.LogFilePosition(6, 19), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(6, 20), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(6, 20), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(6, 20), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(6, 21), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(6, 21), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(7, -1), '}'),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(7, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_xml_function_end(rule.LogFilePosition(7, 1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_line(rule.LogFilePosition(8, -1), ''),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_any_other_xml_element_end(rule.LogFilePosition(8, -1), mocker.ANY),
                                mocker.call.r1.is_active(),
                                mocker.call.r1.visit_file_close(rule.LogFilePosition(-1, -1), 'file.c')
                                ])


# Test
# have srcml return srcml data
#    Confirm rules are activated then visit_file_open
#    Confirm interleaving of xml and line visits
#    Confirm correct position on xml visit

# Test rules deactivating themselves for a file 