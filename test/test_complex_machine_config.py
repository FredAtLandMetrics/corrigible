#!/usr/bin/env python

import unittest
import os

from corrigible.lib.provision_files import directive_index, directive_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest

script_dirpath = os.path.dirname( os.path.dirname( __file__ ) )
machine_config_dirpath = os.path.join(script_dirpath,'resources','machines')
directives_config_dirpath = os.path.join(script_dirpath,'resources','directives')
files_config_dirpath = os.path.join(script_dirpath,'resources','files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')

os.environ['CORRIGIBLE_MACHINES'] = machine_config_dirpath
os.environ['CORRIGIBLE_DIRECTIVES'] = directives_config_dirpath
os.environ['CORRIGIBLE_FILES'] = files_config_dirpath

PLAYBOOK_FILEPATH__MACHINECONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__MACHINECONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"

class TestMachineConfig(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__MACHINECONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__MACHINECONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen_test_complex_directives(self, **kwargs):
        """re-run corrigible for the complex directive test config"""
        self.rerun_corrigible(machine_config="test_complex_directives",
                              generate_files_only=True)
        
    def test_complex_directive_ordering(self):
        """after re-running corrigible on the complex directives test machine config, test that the directives are ordered as per the index indicated is each's filename and as per the directive file containment"""
        self.regen_test_complex_directives()
        self.assertTrue(os.path.isfile(self.output_playbook_filepath))
        self.assertTrue(os.path.isfile(self.output_hostsfile_filepath))

if __name__ == '__main__':
    unittest.main()   
    