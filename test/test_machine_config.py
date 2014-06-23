#!/usr/bin/env python

import unittest
import os
import copy
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
        
    
    def test_machine_config(self):
        self.regen_test_machine_config_files()
        #print "PLAYBOOK_FILEPATH__MACHINECONF_TEST, HOSTS_FILEPATH__MACHINECONF_TEST: {}, {}".format(PLAYBOOK_FILEPATH__MACHINECONF_TEST, HOSTS_FILEPATH__MACHINECONF_TEST)
        self.assertTrue(os.path.isfile(PLAYBOOK_FILEPATH__MACHINECONF_TEST))
        self.assertTrue(os.path.isfile(HOSTS_FILEPATH__MACHINECONF_TEST))
        

if __name__ == '__main__':
    unittest.main()   
    