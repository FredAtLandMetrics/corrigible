#!/usr/bin/env python

import unittest
import os

from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest

script_dirpath = os.path.dirname(  __file__ )
system_config_dirpath = os.path.join(script_dirpath,'resources','systems')
plans_config_dirpath = os.path.join(script_dirpath,'resources','plans')
files_config_dirpath = os.path.join(script_dirpath,'resources','files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')

os.environ['CORRIGIBLE_SYSTEMS'] = system_config_dirpath
os.environ['CORRIGIBLE_PLANS'] = plans_config_dirpath
os.environ['CORRIGIBLE_FILES'] = files_config_dirpath

PLAYBOOK_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"

class TestSameFileParamSubst(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_same_file_parameter_subst",
                              generate_files_only=True)
        
    def test_same_file_param_subst_in_system_file(self):
        self.regen()
        s = self.playbook_as_struct()
        
        self.assertTrue(type(s) is list and len(s) > 0)
        self.assertTrue(type(s[1]) is dict)
        self.assertTrue('tasks' in s[1] and type(s[1]['tasks']) is list and len(s[1]['tasks']) > 0)
        self.assertTrue(type(s[1]['tasks'][0]) is dict)
        self.assertTrue('copy' in s[1]['tasks'][0])
        self.assertTrue('somefile.txt' in str(s[1]['tasks'][0]['copy']))
        
    def test_same_file_param_subst_in_plan_file(self):
        self.regen()
        s = self.playbook_as_struct()
        
        self.assertTrue(type(s) is list and len(s) > 0)
        self.assertTrue(type(s[2]) is dict)
        self.assertTrue('tasks' in s[2] and type(s[2]['tasks']) is list and len(s[2]['tasks']) > 0)
        self.assertTrue(type(s[3]['tasks'][0]) is dict)
        self.assertTrue('copy' in s[3]['tasks'][0])
        self.assertTrue('blahfn.txt' in str(s[3]['tasks'][0]['copy']))
        

if __name__ == '__main__':
    unittest.main()   
