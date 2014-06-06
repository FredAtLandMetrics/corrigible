#!/usr/bin/env python

import unittest
import os
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
    def test_variable_substitution(self):
        
        outputfn = "/tmp/corrigible-test-output.yml"
        
        # remove the test output file if it exists
        if os.path.isfile(outputfn):
            os.remove(outputfn)
            
        call([corrigible_exec_filepath, "test_variable_substitution", "--generate-playbook-only", "--playbook-output-file={}".format(outputfn)])