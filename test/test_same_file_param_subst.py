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
        """test that params defined in the parameters section of a system file are available in the plans stanza
            of the same system file"""
        self.regen()
        s = self.playbook_as_struct()
        
        self.assertTrue(type(s) is list and len(s) > 0)
        self.assertTrue(type(s[1]) is dict)
        self.assertTrue('tasks' in s[1] and type(s[1]['tasks']) is list and len(s[1]['tasks']) > 0)
        self.assertTrue(type(s[1]['tasks'][0]) is dict)
        self.assertTrue('copy' in s[1]['tasks'][0])
        self.assertTrue('somefile.txt' in str(s[1]['tasks'][0]['copy']))
        
    def test_same_file_param_subst_in_plan_file(self):
        """test that params defined in the parameters section of a plan file are available in the plans stanza
            of the same plan file"""
        self.regen()
        s = self.playbook_as_struct()
        
        self.assertTrue(type(s) is list and len(s) > 0)
        self.assertTrue(type(s[2]) is dict)
        self.assertTrue('tasks' in s[2] and type(s[2]['tasks']) is list and len(s[2]['tasks']) > 0)
        self.assertTrue(type(s[2]['tasks'][0]) is dict)
        self.assertTrue('copy' in s[2]['tasks'][0])
        self.assertTrue('blahfn.txt' in str(s[2]['tasks'][0]['copy']))
        

if __name__ == '__main__':
    unittest.main()   
