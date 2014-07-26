#!/usr/bin/env python

import unittest
import os

from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest

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

class TestFilesWithParameters(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_files_parameters",
                              generate_files_only=True)
        
    def test_params_in_files(self, **kwargs):
        self.regen()
        s = self.playbook_as_struct()
        print "s: {}".format(s)
        tasksrec = {}
        tasksrec['file3'] = s[0]['tasks'][0]
        #print "tr:{}".format(tasksrec['file3'])
        self.assertTrue('copy' in tasksrec['file3'])
        self.assertTrue('file3' in tasksrec['file3']['copy'])
        tasksrec['file2'] = s[1]['tasks'][1]
        #print "tr:{}".format(tasksrec['file3'])
        self.assertTrue('copy' in tasksrec['file2'])
        self.assertTrue('file2' in tasksrec['file2']['copy'])
        
if __name__ == '__main__':
    unittest.main()   
        