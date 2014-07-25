Introduction
============

**corrigible** builds on the capabilities of the fantastic automated configuration tool, [ansible](http://www.ansible.com/home), by adding:
* ansible yaml re-use
* sysV-style ordering of ansible snippets
* simplified variable substitution
* run selectors for full vs. partial playbook execution

At some point, it will also provide for automated testing of post-run results and parallelization based on the sysV-style ordering

Why?
====
I really like ansible, but it's awkward at scale.  I feel like it's made to be simple and, as soon as I try to do something a bit more complicated (but not THAT much), I end up copying bits of ansible playbooks around (or forgetting to, which is arguably worse).

After a great discussion with a coworker about our particular set of requirements, I scratched out a design for corrigible to meet our needs without sacrificing ansible's simplicity (which we both agreed was priority #1).

For us, it will help scale ansible's utility without all the complexity.

Before You Begin
================

Corrigible needs workspace, which defaults to */usr/local/etc/corrigible*.  In the workspace, should be three subdirectories: *files*, *plans*, and *systems*:
* **files** - files to be copied to the provisioned systems.  subdirectories are ok.
* **systems** - toplevel config files for hosts (or groups of hosts)
* **plans** - playbook excerpts and *plan* files which allow for intelligent grouping of playbook excerpts

These directories default to */usr/local/etc/corrigible[files|systems|plans]* but can be customized via the following environment variables:
* **CORRIGIBLE_PATH** - define this to configure a directory which will contain *files*, *systems*, and *plans* subdirectories
* **CORRIGIBLE_FILES** - define this to configure a directory which will contain files for corrigible
* **CORRIGIBLE_SYSTEMS** - define this to configure a directory which will contain system configuration files for corrigible
* **CORRIGIBLE_PLANS** - define this to configure a directory which will contain plan files for corrigible

Overview of the Corrigible directories
======================================

The Files Directory
-------------------

Really just a dumping ground for files.  Create all the subdirectories you want.  Follow your own naming configurations.  The sky is the limit.  This is the wild west of file dumping grounds.

The Systems Directory and the Files That Occupy It
---------------------------------------------------

The *systems directory* is where system configuration files go.  Each system configuration file will contain the following sections:
* hosts
* plans
* parameters _(optional)_

*For a more detailed description of different section types, see the **Section Types** section below.

The Plans Directory and Plan Files
---------------------------------------------

The *plans directory* is where plan files are located. There are two types of plan files, **ansible excerpt** files and **plan container** files. 

**Ansible excerpt files** are literally that, excerpts of ansible playbooks.  They can reference variables defined in *parameters* sections (see **Section Types** below).

**Plan container files** look like system configuration files, except that they do not contain hosts sections (or, rather, if they do, then the hosts section will be ignored).  Additionally, there is a naming convention for these files that has implications as to the order in which the plans are processed.

Note that it is perfectly acceptable to put plan container files and ansible excerpt files in subdirectories within the plans directory. Care should be taken to ensure that no two files have the same filename.

System config files and plan container files explained
============================================================

Systems config files and plan container files are very similar in format, but they vary a bit in scope.  System config files are the starting point for corrigible, such that when corrigible is run with this command:
```
corrigible somesystem
```
the very first thing corrigible will do is go look in the systems dir for a file named *somemachine.system*.

Plan container files, on the other hand, are included by system config files (and other directory container files).


System config files
--------------------

This is a system configuration file that is based on one used by the test suite.

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
    
plans:
    - plan: apt_upgrade
      run_selectors:
          include:
            - ALL
          exclude:
            - update_dnsservers      
    - plan: install_cron
    - plan: plans_test
    - plan: add_deploy_user
    - files:
        - source: toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444

```

###The hosts section

The hosts section is the main difference between the two file types.  System config files have them and plan container files do not.  Here's the hosts section from the example above:
    
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

It's pretty straightforward, really. It shows two hosts with their names and ip addresses.  This lets corrigible know which network-accessible systems are to be targetted by the plans.

The hosts section also illustrates one of the more interesting features of corrigible, *run_selectors*. Run selectors make it possible to selectively include or exclude certain plans depending on the run_selectors provided on the corrigible command-line.

###The plans section

The plans section tells corrigible what it will be doing to the hosts listed in the hosts section.  It can contain any number of references to plan container files, ansible workbook extracts, and file transfer listings. It's not immediately obvious, but the plans section in the example above contains all three types of references.

```YAML
plans:
    - plan: apt_upgrade
      run_selectors:
          include:
            - ALL
          exclude:
            - update_dnsservers      
    - plan: install_cron
    - plan: plans_test
    - plan: add_deploy_user
    - files:
        - source: toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444
```
The lines that begin with a *- plan:* can refer to *either* a plan container file or an ansible excerpt file. Like the host records above, they can contain run selectors and can be similarly included/excluded.

As it happens, all of the plans in this section are refer to ansible playbook excerpts except for the one with the 'plans-test' name.  Note that there's no way to tell which is which without looking at the files in the plans directory.
```
fred@chimera:~/Projects/corrigible$ ls test/resources/plans
04_add_deploy_user.ansible.yml
11_install_cron.ansible.yml
19_apt_upgrade.ansible.yml
35_add_misc_users_grp_b.ansible.yml
38_add_misc_users_grp_c.ansible.yml
57_plans_test.plan.yml
75_add_misc_users_grp_a.ansible.yml
81_apt_add_packages.ansible.yml
```

By looking at the filename, it's easy to tell whether a given file is an ansible playbook excerpt or a plan container file.

Note, too, that each file is prefixed by an integer. This guides corrigible when it determines the order in which certain plans are to be executed. 

A look at the plan container file will show how similar it is to the system config file:
```YAML
# this is 57_plans_test.plan.yml

parameters:
    apt_packages_to_install: 'php5,imagemagick'
        
plans:
    - plan: apt_add_packages
    - plan: add_misc_users_grp_c
    - files:
        - source: some/path/testfile.txt
          destination: /tmp/testfile.txt
          mode: 0755
          order: 39
```
The parameters section is discussed in the next section, but the plans section is the same as that of the system config file and it behaves the same way.  It is important to note that the plans in a plan container file are executed in sequence.  *This means that it is possible for a plan with a 100 prefix can be executed before a plan with a 50 prefix if it is referenced in a directory container file with a prefix of 20.*

To segue into the parameters section, we'll look at the contents of a ansible playbook excerpt:
```YAML
# This is 81_apt_add_packages.ansible.yml
- user: {{ sudouser }}
  sudo: yes
  tasks:
    - name: install some apt packages
      apt: name={{ apt_packages_to_install }} state=present
```
No surprises here. Ansible playbooks already have variable substitution. Corrigible variable substitution works the same way only, instead of being specified on the command line, corrigible reads assigns values to the variables from the parameters section.
    
###The parameters section
The parameters section is how corrigible deals with variable substitution. The example system config included a parameters section that looked like:
```YAML
parameters:
    sudouser: ubuntu
    deployuser: deploy
    sudo: yes
```
and the plan container file had parameters like:
```YAML
parameters:
    apt_packages_to_install: 'php5,imagemagick'
```
The *81_apt_add_packages.ansible.yml* file, when it is included via the *57_plans_test.plan.yml*, will have the following variables available to it:
* sudouser
* deployuser
* sudo
* apt_packages_to_install

Note that *parameters in higher-level plan container files and in system config files will supercede those specified in lower-level plan container files.*  Using this mechanism, it's possible for multiple systems to use the same plan containers and yet retain the ability to customize plan behavior at the system config file level.

Running Corrigible
==================

Once the system file and various plan files are in place, provisioning is as simple as:
```shell
corrigible somehost
```

Project Status
==============
The hard parts work and there's tests around key points. Run selectors are now implemented.
 Next I'll be testing corrigible in real-world provisioning situations. I expect things will break.