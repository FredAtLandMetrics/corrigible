#!/usr/bin/env python

import unittest
import os

from corrigible.lib.provision_files import directive_index, directive_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest

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

class TestMachineConfig(CorrigibleTest):

    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__MACHINECONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__MACHINECONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath
        
    def regen_test_complex_directives(self, **kwargs):
        """re-run corrigible for the complex directive test config"""
        self.rerun_corrigible(machine_config="test_complex_directives",
                              generate_files_only=True)
        
    def test_complex_directive_ordering(self):
        """after re-running corrigible on the complex directives test machine config, test that the directives are ordered as per the index indicated is each's filename and as per the directive file containment"""
        self.regen_test_complex_directives()
        self.assertTrue(os.path.isfile(self.output_playbook_filepath))
        self.assertTrue(os.path.isfile(self.output_hostsfile_filepath))
        
        s = self.playbook_as_struct()
        tasksrec = {}
        
        ## listed directives:
        #    directives_test (57)
        #    apt_upgrade (19)
        #    install_cron (11)
        #    add_misc_users_grp_b (35)
        #    add_misc_users_grp_a (75)
        #    add_deploy_user (04)
        
        ## and directives_test contains these directives:
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
        
        
        #    add_deploy_user (04)
        tasksrec['copy_toplevel_text_file'] = s[0]['tasks'][0]
        self.assertTrue('copy' in tasksrec['copy_toplevel_text_file'])
        
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
        tasksrec['add_misc_users_grp_b'] = s[4]['tasks'][0]
        self.assertTrue('user' in tasksrec['add_misc_users_grp_b'])
        self.assertTrue(tasksrec['add_misc_users_grp_b']['name'].strip() == "add tim")

        #    add_misc_users_grp_c (38)
        tasksrec['copy_deeper_file'] = s[5]['tasks'][0]
        self.assertTrue('copy' in tasksrec['copy_deeper_file'])

        tasksrec['add_misc_users_grp_c'] = s[6]['tasks'][0]
        self.assertTrue('user' in tasksrec['add_misc_users_grp_c'])
        self.assertTrue(tasksrec['add_misc_users_grp_c']['name'].strip() == "add sara")

        #    apt_add_packages (81)
        tasksrec['apt_add_packages'] = s[7]['tasks'][0]
        self.assertTrue('apt' in tasksrec['apt_add_packages'])
        self.assertTrue(tasksrec['apt_add_packages']['name'].strip() == "install some apt packages")

        #    add_misc_users_grp_a (75)
        tasksrec['add_misc_users_grp_a'] = s[8]['tasks'][0]
        self.assertTrue('user' in tasksrec['add_misc_users_grp_a'])
        self.assertTrue(tasksrec['add_misc_users_grp_a']['name'].strip() == "add frank")
        

if __name__ == '__main__':
    unittest.main()   
    