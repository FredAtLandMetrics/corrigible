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

class TestMachineConfig(unittest.TestCase):
    def test_machine_config(self):
        
        output_playbook_filepath = "/tmp/corrigible-test-output.yml"
        output_hosts_filepath = "/tmp/corrigible-test-hosts-output.hosts"
        
        # remove the test output file if it exists
        if os.path.isfile(output_playbook_filepath):
            os.remove(output_playbook_filepath)
        if os.path.isfile(output_hosts_filepath):
            os.remove(output_hosts_filepath)
            
        call([corrigible_exec_filepath, "test_machine_config", "--generate-files-only", "--playbook-output-file={}".format(output_playbook_filepath), "--hosts-output-file={}".format(output_hosts_filepath)], env=os.environ.copy())
        
        self.assertTrue(os.path.isfile(output_playbook_filepath))
        self.assertTrue(os.path.isfile(output_hosts_filepath))
        

if __name__ == '__main__':
    unittest.main()   
    