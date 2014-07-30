#!/usr/bin/env python

import unittest
import os
import re

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

class TestTemplateFiles(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath

    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        self.rerun_corrigible(system_config="test_files_template",
                              generate_files_only=True,
                              skip_cleanup=True)

    def test_files_template(self):
        self.regen()
        s = self.playbook_as_struct()
        self.assertTrue(type(s) is list and len(s) > 0)
        self.assertTrue(type(s[0]) is dict)
        self.assertTrue('tasks' in s[0])
        self.assertTrue(type(s[0]['tasks']) is list and len(s[0]['tasks']) > 0)
        self.assertTrue(type(s[0]['tasks'][0]) is dict)
        copy_dict = s[0]['tasks'][0]
        self.assertTrue('copy' in copy_dict)
        copy_directive_str = copy_dict['copy']
        m = re.match(r'src\=([^\s]+)', copy_directive_str)
        self.assertTrue(m is not None)
        #print "m: {}".format(m.group(1))
        template_output_filepath = os.path.join(script_dirpath,'resources',m.group(1))
        
        template_output = None
        with open(template_output_filepath, "r") as fh:
            template_output = fh.read()
            
        self.assertTrue(type(template_output) is str and bool(template_output))
        self.assertTrue('chicken' in template_output)
        
if __name__ == '__main__':
    unittest.main()   
        
                