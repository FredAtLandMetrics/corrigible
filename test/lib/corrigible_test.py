import unittest
import os
import copy
from subprocess import call

class CorrigibleTest(unittest.TestCase):
    
    def rerun_corrigible(self, **kwargs):
        """re-run corrigible for a given machine config file"""
        # remove the test output file if it exists
        if os.path.isfile(self.output_playbook_filepath):
            os.remove(self.output_playbook_filepath)
        if os.path.isfile(self.output_hostsfile_filepath):
            os.remove(self.output_hostsfile_filepath)
            
        try:
            assert(bool(kwargs['generate_files_only']))
            call([self.corrigible_exec_filepath, kwargs['machine_config'], "--generate-files-only", "--playbook-output-file={}".format(self.output_playbook_filepath), "--hosts-output-file={}".format(self.output_hostsfile_filepath)], env=os.environ.copy())
        except KeyError:
            call([self.corrigible_exec_filepath, kwargs['machine_config'], "--playbook-output-file={}".format(self.output_playbook_filepath), "--hosts-output-file={}".format(self.output_hostsfile_filepath)], env=os.environ.copy())
        
    