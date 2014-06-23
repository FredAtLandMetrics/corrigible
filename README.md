Introduction
============

**corrigible** builds on the capabilities of the fantastic automated configuration tool, [ansible](http://www.ansible.com/home), by adding:
* ansible directive re-use
* sysV-style directive ordering
* simplified variable substitution
* runlevels for full vs. partial playbook execution
    
From the ansible workflow, **corrigible** removes:
* duplicated playbook directives
* hosts files

It begins with a workspace, which defaults to */usr/local/etc/corrigible*.  In the workspace, should be three subdirectories: *files*, *directives*, and *machines*:
* **files** - files to be copied to the provisioned machines.  subdirectories are ok.
* **machines** - toplevel config files for hosts (or groups of hosts)
* **directives** - playbook excerpts and *directive* files which allow for intelligent grouping of playbook excerpts

The *machines* and *directives* directories are where all the magic happens for corrigible.  The *machines* directory contains holds *meta* files which tell **corrigible** how to start the provisioning process for a given host (or group of hosts).

Once the machine file and various directive files are in place, provisioning is as simple as:
```shell
corrigible my_machine
```

