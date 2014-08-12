import unittest
import os
import copy
import yaml
import re

from subprocess import call

class CorrigibleTest(unittest.TestCase):
    
    def rerun_corrigible(self, **kwargs):
        """re-run corrigible for a given system config file"""
        # remove the test output file if it exists
        if os.path.isfile(self.output_playbook_filepath):
            os.remove(self.output_playbook_filepath)
        if os.path.isfile(self.output_hostsfile_filepath):
            os.remove(self.output_hostsfile_filepath)
            
        call_list =  [self.corrigible_exec_filepath, kwargs['system_config']]
        try:
            assert(bool(kwargs['generate_files_only']))
            call_list.append("--generate-files-only")
        except (AssertionError, KeyError):
            pass
        
        try:
            assert(bool(kwargs['skip_cleanup']))
            call_list.append("--skip-cleanup")
        except (AssertionError, KeyError):
            pass
        
        call_list.append("--playbook-output-file={}".format(self.output_playbook_filepath))
        call_list.append("--hosts-output-file={}".format(self.output_hostsfile_filepath))
        
        try:
            call_list.append('--selectors={}'.format(kwargs['run_selectors']))
        except KeyError:
            pass
        
        call(call_list, env=os.environ.copy())
        
        
    def hosts_groups_from_file(self, hosts_filepath):
        """given a path to an ansible hosts file, return the list of all host groups in the hostsfile"""
        ret = []
        with open(hosts_filepath) as f:
            lines = f.readlines()
            for l in lines:
                m = re.match(r"^\[(.*)\]", l)
                if m is not None:
                    ret.append(m.group(1))
        return ret
    
    def hostgroup_lines(self, hosts_filepath, hostgroup):
        """given a path to an ansible hosts file and the name of a hostgroup in that file, return a list of all the host lines in the hostgroup section"""
        ret = []
        with open(hosts_filepath) as f:
            lines = f.readlines()
            found = False
            for l in lines:
                
                # skip lines until found
                if not found:
                    m = re.match(r"^\[{}\]".format(hostgroup), l)
                    if m is not None:
                        found = True
                    continue
                
                # capture lines until next group
                m = re.match(r"^\[.*\]", l)
                if m is None and bool(l.strip()):
                    ret.append(l.strip())
                    continue
                
                # if we get this far, it's over, return
                break
            
        if not bool(ret):
            ret = None
            
        return ret
    
    def hostgroup_hostnames(self, hosts_filepath, hostgroup):
        return [line.split(' ')[0] for line in self.hostgroup_lines(hosts_filepath,hostgroup)]
        
        #lines = self.hostgroup_lines(hosts_filepath,hostgroup)
        #ret = []
        #for line in lines:
            #print "ln: {}".format(line)
            #parts = " ".split(line)
            #print "parts: {}".format(str(parts))
            #ret.append(parts[0])
        #print "hostgroup_hostnames returning: {}".format(str(ret))
        #return ret
    
    def playbook_as_struct(self):
        """read the playbook referred to by self.output_playbook_filepath as a yaml file and return the struct"""
        ret = None
        with open(self.output_playbook_filepath, 'r') as fh:
            ret = yaml.load(fh)
        return ret
        
    