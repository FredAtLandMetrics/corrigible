Introduction
============

**corrigible** builds on the capabilities of the fantastic automated configuration tool, [ansible](http://www.ansible.com/home), by adding:
* more flexible re-use of ansible directives
* introduces directive ordering by group (e.g. to ensure, for instance, that all user accounts are added before any cron jobs are installed)
* orchestrate multiple, simplified playbooks with intuitive, meta-informative "directive" files
* simplified variable substitution in playbooks
* runlevels - use the same code to manage full and partial playbook runs
    
and it's intended purpose is to remove the following from the ansible workflow:
* libraries of separately-maintained playbooks with duplicated directives
* single playbooks with multiple goal sets

It begins with a workspace, which defaults to */usr/local/etc/corrigible*.  In the workspace, should be three subdirectories: *files*, *directives*, and *machines*.

The *files* directory simply contains files to be copied to the provisioned machines.  There can be subdirectories in there and there aren't any naming restrictions.  It's just a dumping ground for files.

The *machines* and *directives* directories are where all the magic happens for corrigible.  The *machines* directory contains holds *meta* files which tell **corrigible** how to start the provisioning process for a given host (or group of hosts).

Once the machine file and various directive files are in place, provisioning is as simple as:
```shell
corrigible my_machine
```

