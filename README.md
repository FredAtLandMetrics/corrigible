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

Machines config files and directive container files are very similar in format, but they vary a bit in scope.  Machine config files are the starting point for corrigible, such that when corrigible is run with this command:
```
corrigible somemachine
```
the very first thing corrigible will do is go look in the machines dir for a file named *somemachine.meta*.

Directive container files, on the other hand, are included by machine config files (and other directory container files).


Machine config files
--------------------

This is a machine configuration file that is based on one used by the test suite.

```YAML
hosts:
    - hostname: 'otherhost'
      ip_address: 2.3.4.5
    - hostname: 'testhost'
      ip_address: 1.2.3.4
      run_selectors:               # optional...ALWAYS targetted if unspecified
          include:
            # - ALL                # if present, matches all run selectors
            - update_dnsservers
          exclude:
            - restart_webservers   # useless as spec'd, handy if including ALL
    - hostname: 'otherhost'
      ip_address: 2.3.4.5
      ## run_selectors:     # default to all inclusive run selectors when not specified
      ##   include:
      ##     - ALL
      

parameters:
    sudouser: ubuntu
    deployuser: deploy
    sudo: yes
    
directives:
    - directive: apt_upgrade
      run_selectors:
          include:
            - ALL
          exclude:
            - update_dnsservers      
    - directive: install_cron
    - directive: directives_test
    - directive: add_deploy_user
    - files:
        - source: toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444

```

###The hosts section

The hosts section is the main difference between the two file types.  Machine config files have them and directive container files do not.  Here's the hosts section from the example above:
    
```YAML
hosts:
    - hostname: 'otherhost'
      ip_address: 2.3.4.5
    - hostname: 'testhost'
      ip_address: 1.2.3.4
      run_selectors:               # optional...ALWAYS targetted if unspecified
          include:
            # - ALL                # if present, matches all run selectors
            - update_dnsservers
          exclude:
            - restart_webservers   # useless as spec'd, handy if including ALL
    - hostname: 'otherhost'
      ip_address: 2.3.4.5
      ## run_selectors:     # default to all inclusive run selectors when not specified
      ##   include:
      ##     - ALL
```    

It's pretty straightforward, really. It shows two hosts with their names and ip addresses.  This lets **corrigible** know which network-accessible machines are to be targetted by the directives.

The hosts section also illustrates one of the more interesting features of **corrigible**, *run_selectors*. Run selectors make it possible to selectively include or exclude certain directives depending on the run_selectors provided on the **corrigible** command-line.

###The directives section

The directives section tells corrigible what it will be doing to the hosts listed in the hosts section.  It can contain any number of references to directive container files, ansible workbook extracts, and file transfer listings. It's not immediately obvious, but the directives section in the example above contains all three types of references.

```YAML
directives:
    - directive: apt_upgrade
      run_selectors:
          include:
            - ALL
          exclude:
            - update_dnsservers      
    - directive: install_cron
    - directive: directives_test
    - directive: add_deploy_user
    - files:
        - source: toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444
```
The lines that begin with a *- directive:* can refer to *either* a directive container file or an ansible excerpt file. Like the host records above, they can contain run selectors and can be similarly included/excluded.

As it happens, all of the directives in this section are refer to ansible playbook excerts except for the one with the 'directives-test' name.  Note that there's no way to tell which is which without looking at the files in the directives directory.
```
fred@chimera:~/Projects/corrigible$ ls test/resources/directives
04_add_deploy_user.ansible.yml
11_install_cron.ansible.yml
19_apt_upgrade.ansible.yml
35_add_misc_users_grp_b.ansible.yml
38_add_misc_users_grp_c.ansible.yml
57_directives_test.directive.yml
75_add_misc_users_grp_a.ansible.yml
81_apt_add_packages.ansible.yml
```

By looking at the filename, it's easy to tell whether a given file is an ansible playbook excerpt or a directive container file.

Note, too, that each file is prefixed by an integer. This guides **corrigible** when it determines the order in which certain directives are to be executed.


###The parameters section



Directive container files
-------------------------

Project Status
==============
The hard parts work and there's tests around key points. Run selectors are not yet implemented and testing has been limited to examination of generated ansible hosts and playbook files. Usage against an actual machine has not yet been done.