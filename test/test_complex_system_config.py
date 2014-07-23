#!/usr/bin/env python

import unittest
import os
import re

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

class TestComplexSystemConfig(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen_test_complex_plans(self, **kwargs):
        """re-run corrigible for the complex plan test config"""
        self.rerun_corrigible(system_config="test_complex_plans",
                              generate_files_only=True)
        
        
        
    def test_complex_plan_ordering(self):
        """after re-running corrigible on the complex plans test system config, test that the plans are ordered as per the index indicated is each's filename and as per the plan file containment"""
        self.regen_test_complex_plans()
        self.assertTrue(os.path.isfile(self.output_playbook_filepath))
        self.assertTrue(os.path.isfile(self.output_hostsfile_filepath))
        
        s = self.playbook_as_struct()
        tasksrec = {}
        
        ## listed plans:
        #    plans_test (57)
        #    apt_upgrade (19)
        #    install_cron (11)
        #    add_misc_users_grp_b (35)
        #    add_misc_users_grp_a (75)
        #    add_deploy_user (04)
        
        ## and plans_test contains these plans:
        #    apt_add_packages (81)
        #    add_misc_users_grp_c (38)
        
        ## so, we will expect an ordering like:
        #    add_deploy_user (04)
        #    install_cron (11)
        #    apt_upgrade (19)
        #    add_misc_users_grp_b (35)
        #    add_misc_users_grp_c (38)
        #    apt_add_packages (81)
        #    add_misc_users_grp_a (75)
        
        # ABOVE CHANGED WITH ADDITION OF FILES PLAN!!!
        
        #    add_deploy_user (04)
        tasksrec['copy_toplevel_text_file'] = s[0]['tasks'][0]
        self.assertTrue('copy' in tasksrec['copy_toplevel_text_file'])
        self.assertTrue(re.search(r'toplevel\.txt',tasksrec['copy_toplevel_text_file']['copy']))
        
        tasksrec['add_deploy_user'] = s[1]['tasks'][0]
        self.assertTrue('user' in tasksrec['add_deploy_user'])
        self.assertTrue(tasksrec['add_deploy_user']['name'].strip() == "add deploy user")
        
        #    install_cron (11)
        tasksrec['install_cron'] = s[2]['tasks'][0]
        self.assertTrue('cron' in tasksrec['install_cron'])
        self.assertTrue(tasksrec['install_cron']['name'].strip() == "install etc tar cron")
        
        #    apt_upgrade (19)
        tasksrec['apt_upgrade'] = s[3]['tasks'][0]
        self.assertTrue('apt' in tasksrec['apt_upgrade'])
        self.assertTrue(tasksrec['apt_upgrade']['name'].strip() == "ensure latest os version")
        
        #    add_misc_users_grp_b (35)
        tasksrec['add_misc_users_grp_c'] = s[4]['tasks'][0]
        self.assertTrue('user' in tasksrec['add_misc_users_grp_c'])
        self.assertTrue(re.search(r'toplevel\.txt',tasksrec['copy_toplevel_text_file']['copy']))
        self.assertTrue(tasksrec['add_misc_users_grp_c']['name'].strip() == "add sara")

        # file copy from 57_plans_test.plan.yml
        tasksrec['copy_some_file'] = s[5]['tasks'][0]
        self.assertTrue('copy' in tasksrec['copy_some_file'])
        self.assertTrue(re.search(r'testfile\.txt',tasksrec['copy_some_file']['copy']))
        
        #    apt_add_packages (81)
        tasksrec['apt_add_packages'] = s[6]['tasks'][0]
        self.assertTrue('apt' in tasksrec['apt_add_packages'])
        self.assertTrue(tasksrec['apt_add_packages']['name'].strip() == "install some apt packages")


if __name__ == '__main__':
    unittest.main()   
    