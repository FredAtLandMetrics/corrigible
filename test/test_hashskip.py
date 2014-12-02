#!/usr/bin/env python

import unittest
import os
import shutil

from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest
from corrigible.lib.planhash import plan_hash_str
from corrigible.lib.plan import plan_filepath

script_dirpath = os.path.dirname(  __file__ )
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
        
        
    # def test_hash_dir_create(self):
    #     if bool(os.path.isdir(hashes_dirpath)):
    #         shutil.rmtree(hashes_dirpath)
    #     self.assertFalse(bool(os.path.isdir(hashes_dirpath)))
    #     self.run_playbook()
    #     self.assertTrue(bool(os.path.isdir(hashes_dirpath)))
        
    def test_hash_for_ansible_plans(self):

        # remove the hashes dirpath (and any files or directories therein)
        if bool(os.path.isdir(hashes_dirpath)):
            shutil.rmtree(hashes_dirpath)
        self.assertFalse(bool(os.path.isdir(hashes_dirpath)))

        # run the playbook normally and assert that the file with the expected filepath is created
        self.run_playbook()
        self.assertTrue(bool(os.path.isdir(hashes_dirpath)))
        p_filepath = plan_filepath('hashskip_ansible_plan')
        expected_filepath = os.path.join(
            hashes_dirpath,
            '{}.{}'.format(
                os.path.basename(p_filepath),
                plan_hash_str(p_filepath)
            )
        )
        #print "expected filepath: {}".format(expected_filepath)
        self.assertTrue(os.path.isfile(expected_filepath))


        p_filepath = plan_filepath('hashskip_plan_plan')
        expected_filepath = os.path.join(
            hashes_dirpath,
            '{}.{}'.format(
                os.path.basename(p_filepath),
                plan_hash_str(p_filepath)
            )
        )
        #print "expected filepath: {}".format(expected_filepath)
        self.assertTrue(os.path.isfile(expected_filepath))
        
    # def test_second_pass_skip(self):
    #     if bool(os.path.isdir(hashes_dirpath)):
    #         shutil.rmtree(hashes_dirpath)
    #     self.assertFalse(bool(os.path.isdir(hashes_dirpath)))
    #     self.run_playbook()
    #     s = self.playbook_as_struct()
    #     print "s1: {}".format(s)
    #     self.assertTrue(bool(os.path.isdir(hashes_dirpath)))
    #
    #
    #     self.run_rocket_style()
    #     s = self.playbook_as_struct()
    #     print "s2: {}".format(s)
    #     self.assertTrue(type(s) is list)
    #     self.assertTrue(len(s) == 1)
        
if __name__ == '__main__':
    unittest.main()   
    