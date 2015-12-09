#!/usr/bin/env python

import unittest
import os

from corrigible.test.lib.corrigible_test import CorrigibleTest

# need to get the path using a module instead of __FILE__ since the contents of __FILE__ will change depending on
# whether the test is run as an executable or via py.test
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

class TestInlineAnsiblePlanSystemConfig(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath

    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_shell_expansion",
                              generate_files_only=True)

    def run_playbook(self, **kwargs):
        self.rerun_corrigible(system_config="test_shell_expansion")

    def test_shell_expansion(self):
        if os.path.isfile('/tmp/test_shell_expansion.blah.txt'):
            os.unlink('/tmp/test_shell_expansion.blah.txt')
        self.assertFalse(bool(os.path.isfile('/tmp/test_shell_expansion.blah.txt')))
        self.run_playbook()
        self.assertTrue(bool(os.path.isfile('/tmp/test_shell_expansion.blah.txt')))

if __name__ == '__main__':
    unittest.main()
