import pytest
from rulecheck.engine import Logger
from rulecheck import rule




def test_tab_size_setting():
    logger = Logger(4, False, False, None, False)
    assert logger.get_tab_size() == 4
    
    logger = Logger(6, False, False, None, False)
    assert logger.get_tab_size() == 6
    
    logger.set_tab_size(3)
    assert logger.get_tab_size() == 3
    

def test_warning_and_error_counting():
    logger= Logger(4, False, False, None, False)
    assert logger.warnings_are_errors() == False
    
    assert logger.get_warning_count() == 0
    assert logger.get_error_count() == 0
    logger.increment_warnings()
    assert logger.get_warning_count() == 1
    assert logger.get_error_count() == 0
    logger.increment_errors()
    assert logger.get_warning_count() == 1
    assert logger.get_error_count() == 1
    
    logger = Logger(4, False, True, None, False)
    assert logger.warnings_are_errors() == True
    
    assert logger.get_warning_count() == 0
    assert logger.get_error_count() == 0
    logger.increment_warnings()
    assert logger.get_warning_count() == 0
    assert logger.get_error_count() == 1
    logger.increment_errors()
    assert logger.get_warning_count() == 0
    assert logger.get_error_count() == 2
    
    
    logger.set_warnings_are_errors(False)
    assert logger.warnings_are_errors() == False
    
def test_show_hash_setting():
    logger= Logger(4, False, False, None, False)
    assert logger.show_hash() == False
    
    logger = Logger(4, True, False, None, False)
    assert logger.show_hash() == True
    
    logger.set_show_hash(False)
    assert logger.show_hash() == False
    

def test_log_contains_essential_info(capsys):
    logger = Logger(4, False, False, None, False)
    pos = rule.LogFilePosition(1,1)
    logger.log_violation(rule.LogType.WARNING, pos, "a message", False, "afilename.txt", "myrulepack.rule20", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert "a message" in captured.out
    assert "afilename.txt" in captured.out
    assert "1:1" in captured.out
    assert "myrulepack.rule20" in captured.out
    assert "WARNING" in captured.out
    
    pos = rule.LogFilePosition(2,1)
    logger.log_violation(rule.LogType.ERROR, pos, "a message 2", False, "afilename2.txt", "myrulepack.rule21", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert "a message 2" in captured.out
    assert "afilename2.txt" in captured.out
    assert "2:1" in captured.out
    assert "myrulepack.rule21" in captured.out
    assert "ERROR" in captured.out
    
    
def test_log_handles_pos_info(capsys):
    logger = Logger(4, False, False, None, False)
    
    
    """ Show that line and col number of > 0 is included """
    pos = rule.LogFilePosition(1,1)
    logger.log_violation(rule.LogType.WARNING, pos, "a message", False, "afilename.txt", "myrulepack.ruleC", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert "1:1" in captured.out
    
    """ Show that line and col number of > 0 is included """
    pos = rule.LogFilePosition(2,5)
    logger.log_violation(rule.LogType.WARNING, pos, "a message", False, "afilename.txt", "myrulepack.ruleC", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert "2:5" in captured.out
    
    """ Show that col not included if <= 0 but line number still is """
    pos = rule.LogFilePosition(2,0)
    logger.log_violation(rule.LogType.WARNING, pos, "a message", False, "afilename.txt", "myrulepack.ruleC", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert ":2:" in captured.out
    assert "0" not in captured.out
    pos = rule.LogFilePosition(2,-1)
    logger.log_violation(rule.LogType.WARNING, pos, "a message", False, "afilename.txt", "myrulepack.ruleC", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert ":2:" in captured.out
    assert "-1" not in captured.out
    
    """ Show that line and col number are not included if they are both <= 0 """
    pos = rule.LogFilePosition(0,0)
    logger.log_violation(rule.LogType.WARNING, pos, "a message", False, "afilename.txt", "myrulepack.ruleC", ["source line 1", "source line 2"])
    captured = capsys.readouterr()
    assert ":0:" not in captured.out
    

def test_log_hash(capsys):
    # Setup logger to show hash
    logger = Logger(4, True, False, None, False)
    
    pos = rule.LogFilePosition(1,1)
    include_white_space = True
    logger.log_violation(rule.LogType.WARNING, pos, "a message", include_white_space, "afilename.txt", "myrulepack.ruleC", ["a line of text"])
    first_log = capsys.readouterr()
    
    pos = rule.LogFilePosition(1,1)
    include_white_space = False
    logger.log_violation(rule.LogType.WARNING, pos, "a message", include_white_space, "afilename.txt", "myrulepack.ruleC", ["    a line of text  "])
    second_log = capsys.readouterr()
    
    assert first_log.out == second_log.out
    
    logger.set_show_hash(False)
    include_white_space = False
    logger.log_violation(rule.LogType.WARNING, pos, "a message", include_white_space, "afilename.txt", "myrulepack.ruleC", ["    a line of text  "])
    third_log = capsys.readouterr()
    
    assert second_log.out != third_log.out

def test_pos_line_out_of_range(capsys):
    
    # Since the source lines are used for the hash,
    # setup the logger to show the hash.
    logger = Logger(4, True, False, None, False)
    
    pos = rule.LogFilePosition(2,1)
    include_white_space = True
    logger.log_violation(rule.LogType.WARNING, pos, "a message", include_white_space, "afilename.txt", "myrulepack.ruleC", ["a line of text"])
    captured = capsys.readouterr()
    
    assert "a message" in captured.out
    assert "afilename.txt" in captured.out
    # Still expect reported line number to be shown
    assert "2:1" in captured.out
    assert "myrulepack.ruleC" in captured.out
    assert "WARNING" in captured.out

#### TODO: Need to add ignore file list tests, don't forget to check
# for error cases (bad handle?)