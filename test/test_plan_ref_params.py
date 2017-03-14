#!/usr/bin/env python

import unittest
import os
import json
from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest

import corrigible.lib.plan
script_dirpath = os.path.join(os.path.dirname(corrigible.lib.plan.__file__), '..', 'test')

system_config_dirpath = os.path.join(script_dirpath,'resources','systems')
plans_config_dirpath = os.path.join(script_dirpath,'resources','plans')
files_config_dirpath = os.path.join(script_dirpath,'resources','files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')

os.environ['CORRIGIBLE_SYSTEMS'] = system_config_dirpath
os.environ['CORRIGIBLE_PLANS'] = plans_config_dirpath
os.environ['CORRIGIBLE_FILES'] = files_config_dirpath

PLAYBOOK_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"


class TestPlanRefParams(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath

    def test_without_plan_ref_params(self):
        """run with system file that doesn't use per-plan parameters and confirm that user matches what's in system
            parameter stanza"""
        self.rerun_corrigible(system_config="test_simple_plans",
                              generate_files_only=True)
        s = self.playbook_as_struct()
        self.assertTrue(s[6]['user'] == 'ubuntu')

    def test_with_plan_ref_params(self):
        """run with system file that users per-plan parameters and confirm that user matches what's in per-plan
            parameter stanza"""
        self.rerun_corrigible(system_config="test_simple_plans__planref_params",
                              generate_files_only=True)
        s = self.playbook_as_struct()
        self.assertTrue(s[6]['user'] == 'hank')

if __name__ == '__main__':
    unittest.main()
