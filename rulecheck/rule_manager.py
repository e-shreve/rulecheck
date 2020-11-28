"""
    Rule Manager Module

    Contains the RuleManager class which is responsible for loading and configuring rules
    and then providing for running rules on a given File object.
"""

import copy
import json
import os
import pathlib
import re
import sys

# 3rd party imports
from lxml import etree as ET

# Local imports
from rulecheck.file import File
from rulecheck.srcml import Srcml
from rulecheck.ignore import IgnoreFilter
from rulecheck.logger import Logger
from rulecheck.rule import Rule
from rulecheck.rule import LogType
from rulecheck.rule import LogFilePosition
from rulecheck.verbose import Verbose



class RuleManager:
    """Provides all management of rules: loading, configuring and execution."""

    def __init__(self, logger:Logger, ignore_filter:IgnoreFilter):
        self._rules_dict = {}
        self._current_rule_name = "rulecheck"
        self._logger_ref = logger
        self._ignore_filter = ignore_filter

    @staticmethod
    def _add_rule_paths(rule_paths):
        if rule_paths:
            print (rule_paths)
            for rule_path in rule_paths:
                rule_path = str(pathlib.Path(rule_path).absolute())
                if os.path.isdir(rule_path):
                    try:
                        sys.path.index(rule_path)
                    except ValueError:
                        # Only add if it wasn't already in the path
                        Verbose.print("Adding to sys.path: " + rule_path)
                        sys.path.append(rule_path)
                else:
                    print("Rule path not found: " + rule_path)

    def _load_rule_set(self, rule_set):
        rules_loaded = list()
        rules_skipped = list()

        for rule in rule_set['rules']:
            try:
                rule_full_name = rule['name']
                # The class name must be the same as the last part of the module name
                rule_class_name = rule_full_name.rpartition(".")[-1]

                if rule['name'] not in sys.modules:
                    __import__(rule_full_name)

                settings = {}
                if 'settings' in rule:
                    settings = rule['settings']

                rule_object = getattr(sys.modules[rule_full_name], rule_class_name)(settings)

                identical_rule_exists = False

                if rule_full_name not in self._rules_dict:
                    self._rules_dict[rule_full_name] = []
                    self._rules_dict[rule_full_name].append(rule_object)
                else:
                    for loaded_rule in self._rules_dict[rule_full_name]:
                        if loaded_rule.get_settings() == rule_object.get_settings():
                            identical_rule_exists = True

                    if not identical_rule_exists:
                        self._rules_dict[rule_full_name].append(rule_object)

                rule_path = os.path.abspath(rule_full_name)

                if identical_rule_exists:
                    rules_skipped.append(rule_path)
                else:
                    rules_loaded.append(rule_path)

            except Exception as exc:  #pylint: disable=broad-except
                print("Could not load rule: " + rule_full_name)
                print("Exception on attempt to load rule: " + str(exc))

        return rules_loaded, rules_skipped

    def _set_current_rule_name(self, rule_name:str):
        self._current_rule_name = rule_name
        if self._logger_ref:
            self._logger_ref.set_current_rule_name(rule_name)

    def load_rules(self, config_files, rule_paths):
        """Loads all rules specified in the json configuration files."""

        RuleManager._add_rule_paths(rule_paths)

        for config_file in config_files:
            try:
                with open(config_file) as file_stream:
                    rule_set = json.load(file_stream)

                rules_loaded, rules_skipped = self._load_rule_set(rule_set)

                seperator = '\n  '
                if rules_loaded:
                    Verbose.print("From " + config_file + " loaded " + \
                                  str(len(rules_loaded)) + " rules: " + seperator + \
                                  seperator.join(rules_loaded))

                if rules_skipped:
                    Verbose.print("From " + config_file + " skipped " + \
                                  str(len(rules_loaded)) + " rules already loaded: " + \
                                  seperator +  seperator.join(rules_skipped))

                if (not rules_loaded) and (not rules_skipped):
                    Verbose.print("From " + config_file + " no rules found to load.")

            except Exception:  #pylint: disable=broad-except
                print("Could not open config file: " + config_file)

    def activate_all_rules(self):
        """Marks all loaded rules as active (meaning they will be executed against files.)"""
        for name, rule_array in self._rules_dict.items():
            for rule in rule_array:
                try:
                    rule.set_active()
                except Exception as exc:  #pylint: disable=broad-except
                    self.log_rule_exception("Exception thrown while activating rule. \
                                             See stderr.", exc, name)

    def visit_file_open_all_active_rules(self, file_name:str):
        """Calls visit_file_open for each active rule."""
        for name, rule_array in self._rules_dict.items():
            self._set_current_rule_name(name)
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_file_open(rule, file_name)
                except Exception as exc:  #pylint: disable=broad-except
                    self.log_rule_exception("Exception thrown while calling is_active(). \
                                             See stderr.", exc, name)

    def visit_file_open(self, rule:Rule, file_name:str):
        """Calls visit_file_open(pos, file_name) on any rule providing that method."""

        meth = getattr(rule, 'visit_file_open', None)
        if meth is not None:
            try:
                meth(LogFilePosition(-1, -1), file_name)
            except Exception as exc:  #pylint: disable=broad-except
                self.log_rule_exception("Exception thrown while calling visit_file_open. \
                                         See stderr.", exc, self._current_rule_name)

    def visit_file_close_all_active_rules(self, file_name:str):
        """Calls visit_file_close for each active rule."""
        for name, rule_array in self._rules_dict.items():
            self._set_current_rule_name(name)
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_file_close(rule, file_name)
                except Exception as exc:  #pylint: disable=broad-except
                    self.log_rule_exception("Exception thrown while calling is_active(). \
                                             See stderr.", exc, name)

    def visit_file_close(self, rule:Rule, file_name:str):
        """Calls visit_file_close(pos, file_name) on any rule providing that method."""

        meth = getattr(rule, 'visit_file_close', None)
        if meth is not None:
            try:
                meth(LogFilePosition(-1, -1), file_name)
            except Exception as exc:  #pylint: disable=broad-except
                self.log_rule_exception("Exception thrown while calling visit_file_close. \
                                         See stderr.", exc, self._current_rule_name)

    def visit_file_line_all_active_rules(self, line_num:int, line:str):
        """Calls visit_file_line for each active rule."""
        for name, rule_array in self._rules_dict.items():
            self._set_current_rule_name(name)
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_file_line(rule, line_num, line)
                except Exception as exc:  #pylint: disable=broad-except
                    self.log_rule_exception("Exception thrown while calling is_active(). \
                                             See stderr.", exc, name)

    def visit_file_line(self, rule:Rule, line_num:int, line:str):
        """Calls visit_file_line(pos, line) on any rule providing that method."""

        try:
            meth = getattr(rule, 'visit_file_line', None)
            if meth is not None:
                meth(LogFilePosition(line_num, -1), line)
        except Exception as exc:  #pylint: disable=broad-except
            self.log_rule_exception("Exception thrown while calling visit_file_line. See stderr.",
                exc, self._current_rule_name)

    def check_for_rule_disable(self, line_num:int, line:str):
        """Disables rule(s) if text on the provided line requests to do so."""
        match = re.search(r'(NORCNEXTLINE|NORC)\(([^)]+)', line)
        if match:
            if match.group(1) == 'NORCNEXTLINE':
                line_num += 1

            rules = match.group(2).split(',')

            for rule in rules:
                self._ignore_filter.disable(rule.strip(), line_num)

    def visit_file_lines(self, from_line:int, to_line:int, source_lines):
        """Calls visit_file_line(pos, line) once for each line from 'from_line' to
           'to_line' (inclusive) on any rule providing the visit_file_line method.
        """

        # Guard against going beyond end of source_lines array is needed to handle a bug in srcml.
        # See rulecheck's defect #22 (github) for details.
        for line_num in range(from_line, min(to_line+1, len(source_lines)+1)):
            # -1 to line_num to convert to array's 0 based index.
            self.check_for_rule_disable(line_num, source_lines[line_num-1])
            self.visit_file_line_all_active_rules(line_num, source_lines[line_num-1])

    @staticmethod
    def strip_namespace(full_tag_name:str) -> str:
        """Removes namespace portion of xml tag name"""
        return re.sub('{.*}', '', full_tag_name)

    def visit_xml_all_active_rules(self, pos:LogFilePosition, node: ET.Element, event):
        """Calls visit_xml for each active rule."""
        tag_name = RuleManager.strip_namespace(node.tag)

        for name, rule_array in self._rules_dict.items():
            self._set_current_rule_name(name)
            for rule in rule_array:
                try:
                    if rule.is_active():
                        self.visit_xml(rule, pos, node, tag_name, event)
                except Exception as exc:  #pylint: disable=broad-except
                    self.log_rule_exception("Exception thrown while calling is_active(). \
                                             See stderr.", exc, name)

    def visit_xml(self, rule:Rule, pos:LogFilePosition, #pylint: disable=too-many-arguments
                  node: ET.Element, tag_name:str, event):
        """Calls any visit_xml_* method the Rule has defined per the following algorithm:

           First look for visit methods that include the node name
           Note: parsing xml, the visit methods must be named visit_xml_nodename_start|end.
                 The use of xml_ at the start avoids collisions with visit_file_open and
                 visit_file_line should a <file_open>, <file_close> or <file_line> tag be
                 encountered. Since the XML standard does not allow nodenames to start
                 with 'xml' we also don't have to be concerned with a collision between
                 <xml_name> and <name> since the former is not allowed.
            If method in first step not found, call visit_any_other_xml_element_start|end
              if it exists.
        """
        meth = getattr(rule, 'visit_xml_'+tag_name+'_'+event, None)
        if meth is not None:
            try:
                meth(copy.copy(pos), node)
            except Exception as exc:  #pylint: disable=broad-except
                self.log_rule_exception("Exception thrown while calling " + \
                                   'visit_xml_' + tag_name + '_' + \
                                   event + ". See stderr.", exc, self._current_rule_name)
        else:
            # Location of 'xml' in name is different to avoid problems if the
            # xml document has an <any_other_xml_element> tag.
            meth = getattr(rule, 'visit_any_other_xml_element_' + event, None)
            if meth is not None:
                try:
                    meth(copy.copy(pos), node)
                except Exception as exc:  #pylint: disable=broad-except
                    self.log_rule_exception("Exception thrown while calling "
                                       + 'visit_any_other_xml_element_' + event
                                       + ". See stderr.", exc, self._current_rule_name)



    def run_rules_on_file(self, file:File):
        """Runs the rules on the provided File object.
           This method is responsible for implementing the algorithm to run the visit_
           methods of the rules in the correct order.
        """

        self._ignore_filter.init_filter(file.get_name())

        self.activate_all_rules()

        next_line = 1
        element_line = 1

        if self._logger_ref:
            self._logger_ref.set_current_file(file)

        self.visit_file_open_all_active_rules(file.get_name())

        root = file.get_srcml_etree_root()

        if root is not None:
            context = ET.iterwalk(root, events=("start", "end"))

            for event,elem in context:
                srcml_xml_line = Srcml.get_xml_line(elem, event)

                if srcml_xml_line > element_line:
                    element_line = srcml_xml_line

                if elem.tag == "{http://www.srcML.org/srcML/src}unit":
                    if event == "start":
                        pos = LogFilePosition(1, -1)
                        self.visit_xml_all_active_rules(pos, elem, event)
                    if event == "end":
                        self.visit_file_lines(next_line, len(file.get_lines()), file.get_lines())
                        next_line = len(file.get_lines()) + 1
                        # unit tag doesn't have position encoding but it is always at
                        # the end. Thus, make its reported line the last line of the file.
                        pos = LogFilePosition(len(file.get_lines()), -1)
                        self.visit_xml_all_active_rules(pos, elem, event)
                else:
                    # Process line visitors of any lines not visited yet up to
                    # and including the line this element is on.
                    self.visit_file_lines(next_line, element_line, file.get_lines())
                    next_line = element_line + 1

                    srcml_pos_line, srcml_pos_col = Srcml.get_pos_row_col(elem, event)
                    pos = LogFilePosition(srcml_pos_line, srcml_pos_col)
                    self.visit_xml_all_active_rules(pos, elem, event)
        else:
            self.visit_file_lines(1, len(file.get_lines()), file.get_lines())

        self.visit_file_close_all_active_rules(file.get_name())

        self._set_current_rule_name("rulecheck")


    def log_rule_exception(self, msg:str, exc:Exception, rule_name:str):
        """ Wrapper used to log issues when working with a rule.
        """
        if self._logger_ref:
            self._logger_ref.log_violation(LogType.ERROR, LogFilePosition(-1,-1), msg, False,
                                           "rulecheck", rule_name, [])
        print(exc, sys.stderr)
