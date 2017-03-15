#!/usr/bin/env python

import unittest
import os
import json

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


class TestSystemParams(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_system_params",
                              generate_files_only=True)
        
    def test_system_parameters(self):
        """test that the user in the second stanza is set to the same user that is running the tests, as
            the sudouser in the parameter stanza of the system file is set to sys_local_user """
        self.regen()
        s = self.playbook_as_struct()
        self.assertTrue(type(s) is list)
        self.assertTrue(len(s) > 0)
        self.assertTrue(type(s[1]) is dict)
        self.assertTrue('user' in s[1])
        self.assertTrue(s[1]['user'] == os.environ['USER'])
        
if __name__ == '__main__':
    unittest.main()   
        