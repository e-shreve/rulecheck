import pytest
from rulecheck.engine import IgnoreFileEntry
from rulecheck.rule import LogType




def test_line_with_all_parts():
    """ Test parsing of line with all elements """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:2:4:ERROR:example_rules.file_based_rule:Visited return-256.c")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.ERROR
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    
def test_line_with_no_col_num():
    """ Test parsing of line with all elements except col number """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:2:ERROR:example_rules.file_based_rule:Visited return-256.c")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.ERROR
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    
def test_line_with_no_line_num():
    """ Test parsing of line with all elements except line and col numbers""" 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:ERROR:example_rules.file_based_rule:Visited return-256.c")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.ERROR
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    
def test_line_with_all_parts_and_warning_level():
    """ Test parsing of line with all elements and WARNING level """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:2:4:WARNING:example_rules.file_based_rule:Visited return-256.c")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.WARNING
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    
def test_line_with_rule_level_error():
    """ Test parsing of line resulting from a rule-level error """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:rulecheck:ERROR:example_rules.file_based_rule:Rule threw exception")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "rulecheck"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.ERROR
    assert entry.get_message() == "Rule threw exception"
    assert entry.is_valid()
    
def test_line_with_colons_in_message():
    """ Test parsing of line where the message field has ':' character(s) """ 
    
    # Entry has all possible fields and a message with ':'
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:2:4:ERROR:example_rules.file_based_rule:Visited a file: return-256.c")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.ERROR
    assert entry.get_message() == "Visited a file: return-256.c"
    assert entry.is_valid()
    
    # Entry has fewer than the maximum number of fields and has a message with ':'
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:rulecheck:ERROR:example_rules.file_based_rule:Rule threw exception:KeyError")
    
    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "rulecheck"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_level() == LogType.ERROR
    assert entry.get_message() == "Rule threw exception:KeyError"
    assert entry.is_valid()
    
def test_lines_with_bad_hashes():
    """ Test parsing of line with invalid hash values """ 
    
    # Too short
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79be:rulecheck:ERROR:example_rules.file_based_rule:Rule threw exception")
    assert not entry.is_valid()
    
    # Too long
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79beea:./../rulecheck/return-256.c:2:4:ERROR:example_rules.file_based_rule:Visited return-256.c")
    assert not entry.is_valid()    
    
    # Invalid character (3rd)
    entry = IgnoreFileEntry("b0+91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:2:ERROR:example_rules.file_based_rule:Visited return-256.c")
    assert not entry.is_valid()
    
def test_lines_with_bad_log_level():
    """ Test parsing of line with invalid log level """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:2:ERRORA:example_rules.file_based_rule:Visited return-256.c")
    assert not entry.is_valid()
    
def test_lines_with_bad_line_num():
    """ Test parsing of line with invalid line number """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:A:ERROR:example_rules.file_based_rule:Visited return-256.c")
    assert not entry.is_valid()
    
def test_lines_with_bad_col_num():
    """ Test parsing of line with invalid column number """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:./../rulecheck/return-256.c:1:C:ERROR:example_rules.file_based_rule:Visited return-256.c")
    assert not entry.is_valid()
    
def test_lines_missing_too_many_fields():
    """ Test parsing of line with invalid column number """ 
    entry = IgnoreFileEntry("b0b91dbc35617b55b5620613f8e79bee:ERROR:example_rules.file_based_rule:Visited return-256.c")
    assert not entry.is_valid()