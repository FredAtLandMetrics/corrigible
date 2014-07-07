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
        
    def regen_test_hostsfile_gen_files(self, **kwargs):
        """re-run corrigible for the hostsfile generation test config"""
        self.rerun_corrigible(machine_config="test_hostsfile_generation",
                              generate_files_only=True)
        
    def regen_test_simple_directives(self, **kwargs):
        """re-run corrigible for the simple directive test config"""
        self.rerun_corrigible(machine_config="test_simple_directives",
                              generate_files_only=True)
        
    def test_machine_config_output_files_exist(self):
        """test that the output files exist after rerunning corrigible using the hostsfile generation test machine config"""
        self.regen_test_hostsfile_gen_files()
        self.assertTrue(os.path.isfile(self.output_playbook_filepath))
        self.assertTrue(os.path.isfile(self.output_hostsfile_filepath))
        
    def test_machine_config_hosts_file_accurate(self):
        """test that the generated hosts file is accurate after rerunning corrigible using the hostsfile generation test machine config"""
        self.regen_test_hostsfile_gen_files()
        hostgroups = self.hosts_groups_from_file(self.output_hostsfile_filepath)
        self.assertTrue('all' in hostgroups)
        self.assertTrue(len(hostgroups) == 1)
        lines = self.hostgroup_lines(self.output_hostsfile_filepath,'all')
        self.assertTrue(len(lines) == 1)
        self.assertTrue(lines[0] == "testhost ansible_ssh_host=1.2.3.4")
        
    def test_directive_index(self):
        """test that the directive index method in the provision files lib is properly returning the index specified in the directive filename"""
        dt_index = directive_index('directives_test')
        self.assertTrue(dt_index == 57)
        d_index = directive_index('apt_upgrade')
        self.assertTrue(d_index == 19)
        
    def test_directive_filepath(self):
        """test that the directive filepath method in the provision files lib is properly returning the filepath to the directive file"""
        dt_filepath = directive_filepath('directives_test');
        #print "dt_filepath: {}".format(dt_filepath)
        self.assertTrue(dt_filepath == os.path.abspath(os.path.join(script_dirpath,'resources','directives','57_directives_test.directive.yml')))
        
    def test_parameter_substitution(self):
        """after re-running corrigible on the simple directives test machine config, test that basic parameter substitution is working"""
        self.regen_test_simple_directives()
        self.assertTrue(os.path.isfile(self.output_playbook_filepath))
        self.assertTrue(os.path.isfile(self.output_hostsfile_filepath))
        s = self.playbook_as_struct()
        self.assertTrue(s[0]['user'] == 'ubuntu')
        self.assertTrue(s[0]['sudo'] == True)

    def test_directive_ordering_by_index(self):
        """after re-running corrigible on the simple directives test machine config, test that the directives are ordered as per the index indicated is each's filename"""
        self.regen_test_simple_directives()
        self.assertTrue(os.path.isfile(self.output_playbook_filepath))
        self.assertTrue(os.path.isfile(self.output_hostsfile_filepath))
        s = self.playbook_as_struct()
        self.assertTrue('user' in s[0]['tasks'][0])
        self.assertFalse('user' in s[1]['tasks'][0])
        self.assertFalse('user' in s[2]['tasks'][0])
        self.assertTrue('cron' in s[1]['tasks'][0])
        self.assertFalse('cron' in s[0]['tasks'][0])
        self.assertFalse('cron' in s[2]['tasks'][0])
        self.assertTrue('apt' in s[2]['tasks'][0])
        self.assertFalse('apt' in s[1]['tasks'][0])
        self.assertFalse('apt' in s[0]['tasks'][0])

if __name__ == '__main__':
    unittest.main()   
    