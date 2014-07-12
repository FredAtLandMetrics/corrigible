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

class TestRunSelectors(CorrigibleTest):
    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__MACHINECONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__MACHINECONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def test_hosts(self, **kwargs):
        self.rerun_corrigible(machine_config="test_rs_hosts",
                              generate_files_only=True)
        # determine that the hosts file looks like it should with no run selectors
        
        self.rerun_corrigible(machine_config="test_rs_hosts",
                              generate_files_only=True,
                              run_selectors="testrs1")
        self.rerun_corrigible(machine_config="test_rs_hosts",
                              generate_files_only=True,
                              run_selectors="testrs5")
        self.rerun_corrigible(machine_config="test_rs_hosts",
                              generate_files_only=True,
                              run_selectors="testrs1,testrs5")
