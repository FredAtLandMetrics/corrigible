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

class TestRunSelectors(CorrigibleTest):
    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def _assert_hostsmap(self, incmap):
        hosts = self.hostgroup_hostnames(self.output_hostsfile_filepath, 'all')
        #print "hosts: {}".format(str(hosts))
        for res_pair in incmap:
            hostname, present = res_pair
            #print "testing host: {}, present: {}".format(hostname, present)
            if present is None or present is False:
                self.assertFalse(hostname in hosts)
            elif present is True:
                self.assertTrue(hostname in hosts)
        
    def test_hosts(self, **kwargs):
        self.rerun_corrigible(system_config="test_rs_hosts",
                              generate_files_only=True)
        incmap =  [ [ 'a', True ],
                    [ 'b', True ],
                    [ 'c', True ],
                    [ 'd', False ],
                    [ 'e', True ] ]
        self._assert_hostsmap(incmap)

        # determine that the hosts file looks like it should with no run selectors

        self.rerun_corrigible(system_config="test_rs_hosts",
                              generate_files_only=True,
                              run_selectors="testrs5")
        incmap =  [ [ 'a', True ],
                    [ 'b', True ],
                    [ 'c', False ],
                    [ 'd', True ],
                    [ 'e', True ] ]
        self._assert_hostsmap(incmap)

    def test_plans(self):
        self.rerun_corrigible(system_config="test_rs_hosts",
                              generate_files_only=True)
        s = self.playbook_as_struct()
        self.assertTrue(type(s) is list and len(s) >= 3)
        self.assertTrue(type(s[1]) is dict)
        self.assertTrue('tasks' in s[1].keys())
        self.assertTrue(type(s[1]['tasks']) is list)
        self.assertTrue(type(s[1]['tasks'][0]) is dict)
        self.assertTrue('apt' in s[1]['tasks'][0].keys())
        self.assertFalse('cron' in s[1]['tasks'][0].keys())
        self.rerun_corrigible(system_config="test_rs_hosts",
                              generate_files_only=True,
                              run_selectors="update_dnsservers")
        s = self.playbook_as_struct()
        self.assertTrue(type(s) is list and len(s) >= 3)
        self.assertTrue(type(s[1]) is dict)
        self.assertTrue('tasks' in s[1].keys())
        self.assertTrue(type(s[1]['tasks']) is list)
        self.assertTrue(type(s[1]['tasks'][0]) is dict)
        self.assertTrue('cron' in s[1]['tasks'][0].keys())
        self.assertFalse('apt' in s[1]['tasks'][0].keys())

    
if __name__ == '__main__':
    unittest.main()   
      
