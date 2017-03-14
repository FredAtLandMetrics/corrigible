#!/usr/bin/env python

import unittest
import os
import shutil

from corrigible.test.lib.corrigible_test import CorrigibleTest
import corrigible.lib.plan

script_dirpath = os.path.join(os.path.dirname(corrigible.lib.plan.__file__), '..', 'test')
system_config_dirpath = os.path.join(script_dirpath,'resources','systems')
plans_config_dirpath = os.path.join(script_dirpath,'resources','plans')
files_config_dirpath = os.path.join(script_dirpath,'resources','files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')
hashes_dirpath = '/tmp/corrigible_hashes'

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
        self.rerun_corrigible(system_config="test_hashskip",
                              generate_files_only=True)
        
    def run_playbook(self, **kwargs):
        self.rerun_corrigible(system_config="test_hashskip")
        
    def regen_rocket_style(self, **kwargs):
        self.rerun_corrigible(system_config="test_hashskip",
                              generate_files_only=True,
                              rocket_mode=True)
        
    def run_rocket_style(self, **kwargs):
        self.rerun_corrigible(system_config="test_hashskip",
                              rocket_mode=True)

    def test_second_pass_skip(self):
        """test that rocket mode really is removing tasks from the playlist"""
        # get rid of the hashes directory to start fresh
        if bool(os.path.isdir(hashes_dirpath)):
            shutil.rmtree(hashes_dirpath)

        # confirm that running the playbook creates the hashes directory
        self.assertFalse(bool(os.path.isdir(hashes_dirpath)))
        self.run_playbook()
        self.assertTrue(bool(os.path.isdir(hashes_dirpath)))

        # confirm that playbook is length=5 (2 actual tasks, 3 hash-related tasks)
        s = self.playbook_as_struct()
        self.assertTrue(type(s) is list)
        self.assertTrue(len(s) == 5)

        # run in rocket mode
        self.run_rocket_style()

        # confirm that playbook is length=1 (1 hash-related task)
        s = self.playbook_as_struct()
        self.assertTrue(type(s) is list)
        self.assertTrue(len(s) == 1)
        
if __name__ == '__main__':
    unittest.main()   
    