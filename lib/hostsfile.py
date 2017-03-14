import os

from .system import system_config
from .dirpaths import temp_exec_dirpath


def write_ansible_hosts(opts):
    """writes the ansible hostsfile"""
    mconf = system_config(opts)

    # iterate over the hostrecs and write the hostsfile
    hostrecs = mconf['hosts']
    hosts_filepath = ansible_hostsfile_filepath(opts)
    with open(hosts_filepath, "w") as fh:
        fh.write("[all]\n")
        for hostrec in hostrecs:
            fh.write("{} ansible_ssh_host={}\n".format(hostrec['hostname'], hostrec['ip_address']))
        fh.write("\n")


def ansible_hostsfile_filepath(opts):
    """returns the filepath where the ansible hostsfile will be created"""

    # if the location was specified on the cmdline, return that
    if "hosts_output_file" in opts and bool(opts["hosts_output_file"]):
        return opts["hosts_output_file"]

    # otherwise return the default location in the temp exec directory
    return os.path.join(temp_exec_dirpath(), "provision_{}.hosts".format(opts['system']))

