#!/usr/bin/env python

import unittest
import os
import copy
import re
from subprocess import call

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

    def regen_test_machine_config_files(self, **kwargs):
        # remove the test output file if it exists
        if os.path.isfile(PLAYBOOK_FILEPATH__MACHINECONF_TEST):
            os.remove(PLAYBOOK_FILEPATH__MACHINECONF_TEST)
        if os.path.isfile(HOSTS_FILEPATH__MACHINECONF_TEST):
            os.remove(HOSTS_FILEPATH__MACHINECONF_TEST)
            
        call([corrigible_exec_filepath, "test_machine_config", "--generate-files-only", "--playbook-output-file={}".format(PLAYBOOK_FILEPATH__MACHINECONF_TEST), "--hosts-output-file={}".format(HOSTS_FILEPATH__MACHINECONF_TEST)], env=os.environ.copy())
        
    def hosts_groups_from_file(self, hosts_filepath):
        ret = []
        with open(hosts_filepath) as f:
            lines = f.readlines()
            for l in lines:
                m = re.match(r"^\[(.*)\]", l)
                if m is not None:
                    ret.append(m.group(1))
        return ret
    
    def hostgroup_lines(self, hosts_filepath, hostgroup):
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
    
    def test_machine_config_output_files_exist(self):
        self.regen_test_machine_config_files()
        self.assertTrue(os.path.isfile(PLAYBOOK_FILEPATH__MACHINECONF_TEST))
        self.assertTrue(os.path.isfile(HOSTS_FILEPATH__MACHINECONF_TEST))
        
    def test_machine_config_hosts_file_accurate(self):
        self.regen_test_machine_config_files()
        hostgroups = self.hosts_groups_from_file(HOSTS_FILEPATH__MACHINECONF_TEST)
        self.assertTrue('all' in hostgroups)
        self.assertTrue(len(hostgroups) == 1)
        lines = self.hostgroup_lines(HOSTS_FILEPATH__MACHINECONF_TEST,'all')
        self.assertTrue(len(lines) == 1)
        self.assertTrue(lines[0] == "testhost ansible_ssh_host=1.2.3.4")

if __name__ == '__main__':
    unittest.main()   
    