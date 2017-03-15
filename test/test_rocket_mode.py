#!/usr/bin/env python

import unittest
import os
import errno
import json
import tempfile
import shutil
import copy

from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.test.lib.corrigible_test import CorrigibleTest

import corrigible.lib.plan

script_dirpath = os.path.join(os.path.dirname(corrigible.lib.plan.__file__), '..', 'test')
system_config_dirpath = os.path.join(script_dirpath, 'resources', 'systems')
plans_config_dirpath = os.path.join(script_dirpath, 'resources', 'plans')
files_config_dirpath = os.path.join(script_dirpath, 'resources', 'files')
corrigible_exec_filepath = os.path.join(script_dirpath, '..', 'corrigible')
hashes_dirpath = '/tmp/corrigible_hashes'

# os.environ['CORRIGIBLE_SYSTEMS'] = system_config_dirpath
# os.environ['CORRIGIBLE_PLANS'] = plans_config_dirpath
# os.environ['CORRIGIBLE_FILES'] = files_config_dirpath

PLAYBOOK_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-output.yml"
HOSTS_FILEPATH__SYSTEMCONF_TEST = "/tmp/corrigible-test-hosts-output.hosts"

tmp_exec_dirpath = None
class TestSystemParams(CorrigibleTest):
    def setUp(self):
        self.output_playbook_filepath = PLAYBOOK_FILEPATH__SYSTEMCONF_TEST
        self.output_hostsfile_filepath = HOSTS_FILEPATH__SYSTEMCONF_TEST
        self.corrigible_exec_filepath = corrigible_exec_filepath

    def regen(self, **kwargs):
        """re-run corrigible for the simple plan test config"""
        env = copy.copy(os.environ)
        env["CORRIGIBLE_PATH"] = self.new_corrigible_environment_dirpath()
        self.rerun_corrigible(system_config="test_rocket_mode",
                              rocket_mode=kwargs["rocket_mode"] if "rocket_mode" in kwargs else False,
                              env=env)

    def new_corrigible_environment_dirpath(self):
        """returns the dirpath to the temp execution directory for this process"""
        global tmp_exec_dirpath

        # if the temp exec dirpath is still none, create the directory and symlink the files directory
        if tmp_exec_dirpath is None:
            tmp_exec_dirpath = tempfile.mkdtemp()
            # os.symlink(files_config_dirpath, os.path.join(tmp_exec_dirpath, os.path.basename(files_config_dirpath)))

        return tmp_exec_dirpath

    def clear_touched_files(self):
        def silentremove(filename):
            try:
                os.remove(filename)
            except OSError as e:  # this would be "except OSError, e:" before Python 2.6
                if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
                    raise
        for base in ["a", "b", "c", "z"]:
            silentremove(os.path.join("/tmp", "touch_{}.txt".format(base)))


    def test_rocket_mode(self):
        """this test creates a new corrigible environment in a temp dir, deletes the hash dir locally, runs
            the playbook, checks the resulting playbook to see that it matches expectations, then it runs it
            again, and verifies that now there is a lot of stuff that didn't make it into the playbook the
            second time, then it changes a plan 3 levels down from the system file, and confirms that not only
            does the plan get included, but the parent plans get included as well"""

        # --- create the new corrigible environment

        # dirs
        provision_dir = {}
        dirpath = self.new_corrigible_environment_dirpath()
        for dirname in ["plans", "systems", "files"]:
            provision_dir[dirname] = os.path.join(dirpath, dirname)
            os.mkdir(provision_dir[dirname])

        # systems
        shutil.copyfile(
            os.path.join(system_config_dirpath, "test_rocket_mode.system"),
            os.path.join(provision_dir["systems"], "test_rocket_mode.system")
        )

        # plans
        for plan in ["150_rocketmode_test.plan.yml", "200_touch_file_a.ansible.yml", "210_touch_file_b.ansible.yml"]:
            shutil.copyfile(
                os.path.join(plans_config_dirpath, plan),
                os.path.join(provision_dir["plans"], plan)
            )

        # --- clear hashes dir
        try:
            shutil.rmtree(hashes_dirpath)
        except FileNotFoundError:
            pass

        # -- clear touched files that may be left around from previous failed runs of this test
        self.clear_touched_files()

        # run corrigible
        self.regen(rocket_mode=True)

        # test that everything is in the playbook as expected
        s = self.playbook_as_struct()
        print("s: {}".format(s))

        self.assertTrue(s[1]["tasks"][0]["name"] == "touch temp file z")
        self.assertTrue(s[2]["tasks"][0]["name"] == "touch temp file a")
        self.assertTrue(s[4]["tasks"][0]["name"] == "touch temp file b")

        # run corrigible with rocket mode on
        self.regen(rocket_mode=True)

        # test that very little is in the playbook as expected
        s = self.playbook_as_struct()
        self.assertTrue(len(s) == 1)

        # self.assertTrue(False)

        # change low-level plan

        # run corrigible

        # test that some stuff still isn't there, but the changed plan and it's parent plan are both present

        # delete the temp corrigible environment



if __name__ == '__main__':
    unittest.main()
