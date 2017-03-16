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
hashes_dirpath = '/corrigible/hashes'

os.environ['CORRIGIBLE_SYSTEMS'] = system_config_dirpath
os.environ['CORRIGIBLE_PLANS'] = plans_config_dirpath
os.environ['CORRIGIBLE_FILES'] = files_config_dirpath
os.environ['CORRIGIBLE_HASHES'] = hashes_dirpath

PLAYBOOK_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"

class TestLocalConnectForTesting(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_local_connect_for_testing",
                              generate_files_only=True)
        
    def run_playbook(self, **kwargs):
        self.rerun_corrigible(system_config="test_local_connect_for_testing")
        
    def test_local_connect(self):
        """test that the local ssh connection is working (needed for some tests to work)"""
        if os.path.isfile('/tmp/test_local_connect.test.txt'):
            os.unlink('/tmp/test_local_connect.test.txt')
        self.assertFalse(bool(os.path.isfile('/tmp/test_local_connect.test.txt')))
        self.run_playbook()
        self.assertTrue(bool(os.path.isfile('/tmp/test_local_connect.test.txt')))
        
if __name__ == '__main__':
    unittest.main()   
    