#!/usr/bin/env python

import unittest
import os
import re

from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest
from corrigible.lib.test import lookup_registered_tester
from corrigible.lib.tests.file import FileTest

script_dirpath = os.path.dirname( os.path.dirname( __file__ ) )
system_config_dirpath = os.path.join(script_dirpath,'resources','systems')
plans_config_dirpath = os.path.join(script_dirpath,'resources','plans')
files_config_dirpath = os.path.join(script_dirpath,'resources','files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')

os.environ['CORRIGIBLE_SYSTEMS'] = system_config_dirpath
os.environ['CORRIGIBLE_PLANS'] = plans_config_dirpath
os.environ['CORRIGIBLE_FILES'] = files_config_dirpath

PLAYBOOK_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"

class TestBasicSystemTests(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen_test_complex_plans(self, **kwargs):
        """re-run corrigible for the complex plan test config"""
        self.rerun_corrigible(system_config="test_basic_system_tests",
                              generate_files_only=True)
        
    def test_test_registration(self):
        tester = lookup_registered_tester({'file': 'path=/tmp/blah.txt owner=root mode=0400'})
        self.assertTrue(str(tester.__name__) is FileTest)

if __name__ == '__main__':
    unittest.main()   
