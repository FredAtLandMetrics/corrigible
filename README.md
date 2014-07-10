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
corrigible somehost
```

Before You Begin
================

As mentioned above, **corrigible** expects three directories to exist: one for files, one for machine config files and one for directive files.

These directories default to */usr/local/etc/corrigible[files|machines|directives]* but can be customized via the following environment variables:
* **CORRIGIBLE_PATH** - define this to configure a directory which will contain *files*, *machines*, and *directives* subdirectories
* **CORRIGIBLE_FILES** - define this to configure a directory which will contain files for corrigible
* **CORRIGIBLE_MACHINES** - define this to configure a directory which will contain machine configuration files for corrigible
* **CORRIGIBLE_DIRECTIVES** - define this to configure a directory which will contain directive files for corrigible

Overview of the Corrigible directories
======================================

The Files Directory
-------------------

Really just a dumping ground for files.  Create all the subdirectories you want.  Follow your own naming configurations.  The sky is the limit.  This is the wild west of file dumping grounds.

The Machines Directory and the Files That Occupy It
---------------------------------------------------

The *machines directory* is where machine configuration files go.  Each machine configuration file will contain the following sections:
* hosts
* directives
* parameters _(optional)_
* files _(optional)_

*For a more detailed description of different section types, see the **Section Types** section below.

The Directives Directory and Directives Files
---------------------------------------------

The *directives directory* is where directives files are located. There are two types of directives files, **ansible excerpt** files and **directive container** files. 

**Ansible excerpt files** are literally that, excerpts of ansible playbooks.  They can reference variables defined in *parameters* sections (see **Section Types** below).

**Directive container files** look like machine configuration files, except that they may not contain hosts sections (or, rather, if they do, then the hosts section will be ignored).  Additionally, there is a naming convention for these files that has implications as to the order in which the directives are processed.

Machine config files and directive container files explained
============================================================

Machine config files
--------------------
```YAML
hosts:
    - hostname: 'testhost'
      hostgroup: 'testgroup'
      ip_address: 1.2.3.4

parameters:
    sudouser: ubuntu
    deployuser: deploy
    sudo: yes
    
directives:
    - directive: apt_upgrade
    - directive: install_cron
    - directive: add_deploy_user
    - files:
        - source: toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444

```

Directive container files
-------------------------

