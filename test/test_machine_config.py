#!/usr/bin/env python

import unittest
import os
import copy
import re
import yaml
from subprocess import call

from corrigible.lib.provision_files import directive_index, directive_filepath

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

class TestMachineConfig(unittest.TestCase):

    def rerun_corrigible(self, **kwargs):
        """re-run corrigible for a given machine config file"""
        # remove the test output file if it exists
        if os.path.isfile(PLAYBOOK_FILEPATH__MACHINECONF_TEST):
            os.remove(PLAYBOOK_FILEPATH__MACHINECONF_TEST)
        if os.path.isfile(HOSTS_FILEPATH__MACHINECONF_TEST):
            os.remove(HOSTS_FILEPATH__MACHINECONF_TEST)
            
        try:
            assert(bool(kwargs['generate_files_only']))
            call([corrigible_exec_filepath, kwargs['machine_config'], "--generate-files-only", "--playbook-output-file={}".format(PLAYBOOK_FILEPATH__MACHINECONF_TEST), "--hosts-output-file={}".format(HOSTS_FILEPATH__MACHINECONF_TEST)], env=os.environ.copy())
        except KeyError:
            call([corrigible_exec_filepath, kwargs['machine_config'], "--playbook-output-file={}".format(PLAYBOOK_FILEPATH__MACHINECONF_TEST), "--hosts-output-file={}".format(HOSTS_FILEPATH__MACHINECONF_TEST)], env=os.environ.copy())
        

    def regen_test_hostsfile_gen_files(self, **kwargs):
        """re-run corrigible for the hostsfile generation test config"""
        self.rerun_corrigible(machine_config="test_hostsfile_generation",
                              generate_files_only=True)
        
    def regen_test_simple_directives(self, **kwargs):
        """re-run corrigible for the simple directive test config"""
        self.rerun_corrigible(machine_config="test_simple_directives",
                              generate_files_only=True)
        
    def hosts_groups_from_file(self, hosts_filepath):
        """given a path to an ansible hosts file, return the list of all host groups in the hostsfile"""
        ret = []
        with open(hosts_filepath) as f:
            lines = f.readlines()
            for l in lines:
                m = re.match(r"^\[(.*)\]", l)
                if m is not None:
                    ret.append(m.group(1))
        return ret
    
    def hostgroup_lines(self, hosts_filepath, hostgroup):
        """given a path to an ansible hosts file and the name of a hostgroup in that file, return a list of all the host lines in the hostgroup section"""
        ret = []
        with open(hosts_filepath) as f:
            lines = f.readlines()
            found = False
            for l in lines:
                
                # skip lines until found
                if not found:
                    m = re.match(r"^\[{}\]".format(hostgroup), l)
                    if m is not None:
                        found = True
                    continue
                
                # capture lines until next group
                m = re.match(r"^\[.*\]", l)
                if m is None and bool(l.strip()):
                    ret.append(l.strip())
                    continue
                
                # if we get this far, it's over, return
                break
            
        if not bool(ret):
            ret = None
            
        return ret
    
    def playbook_as_struct(self):
        """read the playbook referred to by PLAYBOOK_FILEPATH__MACHINECONF_TEST as a yaml file and return the struct"""
        ret = None
        with open(PLAYBOOK_FILEPATH__MACHINECONF_TEST, 'r') as fh:
            ret = yaml.load(fh)
        return ret
        
    def test_machine_config_output_files_exist(self):
        """test that the output files exist after rerunning corrigible using the hostsfile generation test machine config"""
        self.regen_test_hostsfile_gen_files()
        self.assertTrue(os.path.isfile(PLAYBOOK_FILEPATH__MACHINECONF_TEST))
        self.assertTrue(os.path.isfile(HOSTS_FILEPATH__MACHINECONF_TEST))
        
    def test_machine_config_hosts_file_accurate(self):
        """test that the generated hosts file is accurate after rerunning corrigible using the hostsfile generation test machine config"""
        self.regen_test_hostsfile_gen_files()
        hostgroups = self.hosts_groups_from_file(HOSTS_FILEPATH__MACHINECONF_TEST)
        self.assertTrue('all' in hostgroups)
        self.assertTrue(len(hostgroups) == 1)
        lines = self.hostgroup_lines(HOSTS_FILEPATH__MACHINECONF_TEST,'all')
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
        print "dt_filepath: {}".format(dt_filepath)
        self.assertTrue(dt_filepath == os.path.abspath(os.path.join(script_dirpath,'resources','directives','57_directives_test.directive.yml')))
        
    def test_parameter_substitution(self):
        """after re-running corrigible on the simple directives test machine config, test that basic parameter substitution is working"""
        self.regen_test_simple_directives()
        self.assertTrue(os.path.isfile(PLAYBOOK_FILEPATH__MACHINECONF_TEST))
        self.assertTrue(os.path.isfile(HOSTS_FILEPATH__MACHINECONF_TEST))
        s = self.playbook_as_struct()
        self.assertTrue(s[0]['user'] == 'ubuntu')
        self.assertTrue(s[0]['sudo'] == True)

if __name__ == '__main__':
    unittest.main()   
    