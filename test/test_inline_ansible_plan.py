#!/usr/bin/env python

import unittest
import os

from lib.plan import plan_index, plan_filepath
from test.lib.corrigible_test import CorrigibleTest

import lib.plan
script_dirpath = os.path.join(os.path.dirname(lib.plan.__file__), '..', 'test')
system_config_dirpath = os.path.join(script_dirpath,'resources','systems')
plans_config_dirpath = os.path.join(script_dirpath,'resources','plans')
files_config_dirpath = os.path.join(script_dirpath,'resources','files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')

os.environ['CORRIGIBLE_SYSTEMS'] = system_config_dirpath
os.environ['CORRIGIBLE_PLANS'] = plans_config_dirpath
os.environ['CORRIGIBLE_FILES'] = files_config_dirpath

PLAYBOOK_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"

class TestInlineAnsiblePlanSystemConfig(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_inline_ansible_directive",
                              generate_files_only=True)

    def test_inline_ansible_plan(self):
        """test that ansible yaml code defined via inline directive actually makes it into the final playbook"""
        self.regen()
        s = self.playbook_as_struct()
        tasksrec = {}
        self.assertTrue(type(s) is list and len(s) > 1)
        self.assertTrue(type(s[1]) is dict and 'tasks' in s[0])
        self.assertTrue(type(s[1]['tasks']) is list and len(s[0]['tasks']) > 0)
        self.assertTrue(type(s[1]['tasks'][0]) is dict)
        self.assertTrue('apt' in s[1]['tasks'][0])
        
        
if __name__ == '__main__':
    unittest.main()   
        