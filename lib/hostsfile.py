import os

from .system import system_config
from .dirpaths import temp_exec_dirpath

def write_ansible_hosts(opts):
    mconf = None
    try:
        mconf = system_config(opts)
        hostrecs = mconf['hosts']
        
        hosts_filepath = ansible_hostsfile_filepath(opts)
        #print "writing to: {}".format(hosts_filepath)
        with open(hosts_filepath, "w") as fh:
            fh.write("[all]\n")
            
            for hostrec in hostrecs:
                fh.write("{} ansible_ssh_host={}\n".format(hostrec['hostname'], hostrec['ip_address']))
            fh.write("\n")
    except TypeError:
        #print "system_config: {}".format(str(mconf))
        if mconf is None:
            print("ERR: No system config, not writing ansible hosts file")
            return
        else:
            raise

def ansible_hostsfile_filepath(opts):
    try:
        output_filepath = opts["hosts_output_file"]
        assert(output_filepath is not None)
        return output_filepath
    except (AssertionError, KeyError):
        return os.path.join(temp_exec_dirpath(),
                            "provision_{}.hosts".format(opts['system']))

