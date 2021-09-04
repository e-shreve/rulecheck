import pytest
from rulecheck.ignore import IgnoreEntry
from rulecheck.rule import LogType

#pylint: disable=line-too-long


def test_line_with_all_parts():
    """ Test parsing of line with all elements """
    line = "b0b91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c:2:4: ERROR: example_rules.file_based_rule: Visited return-256.c"  
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_line_with_no_col_num():
    """ Test parsing of line with all elements except col number """
    line = "b0b91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c:2: ERROR: example_rules.file_based_rule: Visited return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_line_with_no_line_num():
    """ Test parsing of line with all elements except line and col numbers"""
    line = "b0b91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c: ERROR: example_rules.file_based_rule: Visited return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_line_with_all_parts_and_warning_level():
    """ Test parsing of line with all elements and WARNING level """
    line = "b0b91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c:2:4: WARNING: example_rules.file_based_rule: Visited return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.WARNING
    assert entry.get_message() == "Visited return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_line_with_rule_level_error():
    """ Test parsing of line resulting from a rule-level error """
    line = "b0b91dbc35617b55b5620613f8e79bee: rulecheck: ERROR: example_rules.file_based_rule: Rule threw exception"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "rulecheck"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Rule threw exception"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_line_with_colons_in_message():
    """ Test parsing of line where the message field has ':' character(s) """

    # Entry has all possible fields and a message with ':'
    line = "b0b91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c:2:4: ERROR: example_rules.file_based_rule: Visited a file: return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "./../rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited a file: return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

    # Entry has fewer than the maximum number of fields and has a message with ':'
    line = "b0b91dbc35617b55b5620613f8e79bee: rulecheck: ERROR: example_rules.file_based_rule: Rule threw exception:KeyError"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "rulecheck"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Rule threw exception:KeyError"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_line_with_colons_in_filename():
    """ Test parsing of line where the filename field has ':' character """

    # Entry has all possible fields and a filename with ':'
    line = "b0b91dbc35617b55b5620613f8e79bee: C:/project/rulecheck/return-256.c:2:4: ERROR: example_rules.file_based_rule: Visited a file: return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "C:/project/rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited a file: return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

    # Entry has all possible fields except col number and has a filename with ':'
    line = "b0b91dbc35617b55b5620613f8e79bee: C:/project/rulecheck/return-256.c:2: ERROR: example_rules.file_based_rule: Visited a file: return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "C:/project/rulecheck/return-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited a file: return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

    # Entry has all possible fields except col and line number and has a filename with ':'
    line = "b0b91dbc35617b55b5620613f8e79bee: C:/project/rulecheck/return-256.c: ERROR: example_rules.file_based_rule: Visited a file: return-256.c"
    entry = IgnoreEntry.from_ignore_file_line(line)

    assert entry.get_hash() == "b0b91dbc35617b55b5620613f8e79bee"
    assert entry.get_file_name() == "C:/project/rulecheck/return-256.c"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
    assert entry.get_rule_name() == "example_rules.file_based_rule"
    assert entry.get_log_type() == LogType.ERROR
    assert entry.get_message() == "Visited a file: return-256.c"
    assert entry.is_valid()
    assert entry.get_ignore_file_line() == line

def test_lines_with_bad_hashes():
    """ Test parsing of line with invalid hash values """

    # Too short
    entry = IgnoreEntry.from_ignore_file_line("b0b91dbc35617b55b5620613f8e79be: rulecheck: ERROR: example_rules.file_based_rule: Rule threw exception")
    assert not entry.is_valid()

    # Too long
    entry = IgnoreEntry.from_ignore_file_line("b0b91dbc35617b55b5620613f8e79beea: ./../rulecheck/return-256.c:2:4: ERROR: example_rules.file_based_rule: Visited return-256.c")
    assert not entry.is_valid()

    # Invalid character (3rd)
    entry = IgnoreEntry.from_ignore_file_line("b0+91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c:2: ERROR: example_rules.file_based_rule: Visited return-256.c")
    assert not entry.is_valid()

def test_lines_with_bad_log_level():
    """ Test parsing of line with invalid log level """
    entry = IgnoreEntry.from_ignore_file_line("b0b91dbc35617b55b5620613f8e79bee: ./../rulecheck/return-256.c:2: ERRORA: example_rules.file_based_rule: Visited return-256.c")
    assert not entry.is_valid()

def test_lines_missing_too_many_fields():
    """ Test parsing of line with invalid column number """
    entry = IgnoreEntry.from_ignore_file_line("b0b91dbc35617b55b5620613f8e79bee: ERROR :example_rules.file_based_rule: Visited return-256.c")
    assert not entry.is_valid()

def test_filename_with_colons():
    """ Test parsing of line with filename that contains colons and has lin:col info.
        Test parsing of line with filename that contains colons and doesn't have lin:col info. """
    entry = IgnoreEntry.from_ignore_file_line("b0b91dbc35617b55b5620613f8e79bee: ./../rule:check/ret:urn-256.c:2:4: ERROR: example_rules.file_based_rule: Visited return-256.c")
    assert entry.is_valid()
    assert entry.get_file_name() == "./../rule:check/ret:urn-256.c"
    assert entry.get_line_num() == 2
    assert entry.get_col_num() == 4

    entry = IgnoreEntry.from_ignore_file_line("b0b91dbc35617b55b5620613f8e79bee: ./../rule:check/ret:urn-256.c: ERROR: example_rules.file_based_rule: Visited return-256.c")
    assert entry.is_valid()
    assert entry.get_file_name() == "./../rule:check/ret:urn-256.c"
    assert entry.get_line_num() == -1
    assert entry.get_col_num() == -1
