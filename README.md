Introduction
============

**corrigible** builds on the capabilities of the fantastic automated configuration tool, [ansible](http://www.ansible.com/home), by adding:
* ansible yaml re-use
* sysV-style ordering of ansible snippets
* playbook variables that are overrideable via environment variables
* enhanced variable substitution
* run selectors for full vs. partial playbook execution

Why?
====
I really like ansible, but it's awkward at scale.  I feel like it's made to be simple and, as soon as I try to do something a bit more complicated (but not THAT much), I end up copying bits of ansible playbooks around (or forgetting to, which is arguably worse).

Our particular problem was a large number of existing and planned codebases with similar, but not identical,
automated deployment requirements.  There was a fair bit of existing ansible playbook code already in use, but it was
fragile and fixes rarely made it to every codebase to which it should have been applied.

After much discussion with a coworker about our particular set of requirements, I scratched out a design
that addressed our needs without sacrificing ansible's simplicity (which we both agreed was priority #1).

The result is **corrigible**, which let us develop a library of re-usable snippets and structured collections
thereof that gave us the ability:
* to apply fixes across all targets at once
* to keep the existing playbook code
* to develop best-practices and guidelines that helped us add directives without disrupting surrounding
playbook code
* to create automated deployment code for new projects much more quickly

For one-off projects like my personal website or various personal projects, I can include a provision directory in the top-level of the source tree that contains plans, system files and files and use virtualenvwrapper to make my deployments a single-command affair, so I can

    corrigible production

to fire off my latest updates to the server or

    corrigible snapshot-production-database

or

    corrigible load-production-database-snapshot-to-dev-db

**And, extra! extra! read all about it!**
 you can now use the *--rocket-mode* command-line argument to skip any plans that haven't changed since the last run!!  And it should now work as you'd expect...the implementation prior to March 16, 2017 was not althogether functional.

Before You Begin
================

Corrigible needs a workspace, the location of which can defined using the environment variable, **CORRIGIBLE_PATH**.
In the workspace, should be three subdirectories: *files*, *plans*, and *systems*.

Overview of the Corrigible directories
======================================

The Files Directory
-------------------

Really just a dumping ground for files.  Create all the subdirectories you want.  Follow your own naming configurations.
The sky is the limit.  This is the wild west of file dumping grounds.

The Systems Directory and the Files That Occupy It
---------------------------------------------------

The *systems directory* is where system configuration files go.  Each system configuration file will contain the
following sections:
* hosts
* plans
* parameters _(optional)_

*For a more detailed description of different section types, see the **Section Types** section below.

The Plans Directory and Plan Files
---------------------------------------------

The *plans directory* is where plan files are located. There are two types of plan files, **ansible excerpt** files and
**plan container** files.

**Ansible excerpt files** are literally that, excerpts of ansible playbooks.  They can reference variables defined in
*parameters* sections (see **Section Types** below).

**Plan container files** look like system configuration files, except that they do not contain hosts sections (or,
rather, if they do, then the hosts section will be ignored).  Additionally, there is a naming convention for these files
that has implications as to the order in which the plans are processed.

Note that it is perfectly acceptable to put plan container files and ansible excerpt files in subdirectories within the
plans directory. Care should be taken to ensure that no two files have the same filename.

System config files and plan container files explained
============================================================

Systems config files and plan container files are very similar in format, but they vary a bit in scope.  System config
files are the starting point for corrigible, such that when corrigible is run with this command:
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
        - source: files/toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444
          order: 35
        - source: files/tmpl/templex.html
          destination: /var/www/index.html
          mode: 0444
          template: yes
          order: 35
    - files:
        parameters:
          order: 75
          mode: 0644
          owner: fred
          group: nohomersclub
        list:
          - source: files/somefile.txt
            destination: /etc/some/file.txt
    - inline:
          order: 12
          ansible:
            - hosts: all
              user: {{ sudouser }}
              sudo: {{ sudo }}
              tasks:
                - name: ensure latest os version
                  apt: upgrade=safe update_cache=yes

```

###The hosts section

The hosts section is the main difference between the two file types.  System config files have them and plan container
files do not.  Here's the hosts section from the example above:
    
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

It's pretty straightforward, really. It shows two hosts with their names and ip addresses.  This lets corrigible know
which network-accessible systems are to be targetted by the plans.

The hosts section also illustrates one of the more interesting features of corrigible, *run_selectors*. Run selectors
make it possible to selectively include or exclude certain plans depending on the run_selectors provided on the
corrigible command-line.

###The plans section

The plans section tells corrigible what it will be doing to the hosts listed in the hosts section.  It can contain any
number of references to plan container files, ansible workbook extracts, inline ansible snippets, and file transfer
listings. It's not immediately obvious, but the plans section in the example above contains all four types of
references.

```YAML
plans:
    - plan: apt_upgrade
      run_selectors:
          include:
            - ALL
          exclude:
            - update_dnsservers      
    - plan: install_cron
      parameters:
          some_custom_param: val1
          note: this makes jinja loops useful!
          addl_note: this has precedent over any parameters with the same name defined in the install_cron plan
          addl_note2: this can be overridden by an environment variable
    - plan: plans_test
    - plan: add_deploy_user
    - files:
        - source: files/toplevel.txt
          destination: /tmp/test_toplevel.txt
          mode: 0444
          order: 35
        - source: files/tmpl/templex.html
          destination: /var/www/index.html
          mode: 0444
          template: yes
          order: 35
    - files:
        parameters:
          order: 75
          mode: 0644
          owner: fred
          group: nohomersclub
        list:
          - source: files/somefile.txt
            destination: /etc/some/file.txt
    - inline:
          order: 12
          ansible:
            - hosts: all
              user: {{ sudouser }}
              sudo: {{ sudo }}
              tasks:
                - name: ensure latest os version
                  apt: upgrade=safe update_cache=yes
```
The sections that begin with *- files:* instruct corrigible to create ansible file copy directives based on the
information therein. Note that there are two forms. The latter prevents some unnecessary duplicated typing.  *Also, note
that, if the* ***template:*** ***yes*** *line is present, the file will be run through the jinja2 templating engine with
the same parameters record that informs the variable substitution in the plan and ansible plan files.*

The sections that begin with *- inline:* are simply copied into the resulting ansible playbook using the indicated order
(which defaults to zero if unspecified.

The lines that begin with a *- plan:* can refer to *either* a plan container file or an ansible excerpt file. Like the
host records above, they can contain run selectors and can be similarly included/excluded.

As it happens, all of the plans in this section refer to ansible playbook excerpts except for the one with the
'plans-test' name.  Note that there's no way to tell which is which without looking at the files in the plans directory.
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

By looking at the filename, it's easy to tell whether a given file is an ansible playbook excerpt or a plan container
file.

Note, too, that each file is prefixed by an integer. This guides corrigible when it determines the order in which
certain plans are to be executed.

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
The parameters section is discussed in the next section, but the plans section is the same as that of the system config
file and it behaves the same way.  It is important to note that the plans in a plan container file are executed in
sequence.  *This means that it is possible for a plan with a 100 prefix can be executed before a plan with a 50 prefix
if it is referenced in a directory container file with a prefix of 20.*

To segue into the parameters section, we'll look at the contents of a ansible playbook excerpt:
```YAML
# This is 81_apt_add_packages.ansible.yml
- user: {{ sudouser }}
  sudo: yes
  tasks:
    - name: install some apt packages
      apt: name={{ apt_packages_to_install }} state=present
```
No surprises here. Ansible playbooks already have variable substitution. Corrigible variable substitution works the
same way only, instead of being specified on the command line, corrigible reads assigns values to the variables from the
parameters section.
    
###The parameters section
The parameters section is how corrigible deals with variable substitution. The example system config included a
parameters section that looked like:
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
The *81_apt_add_packages.ansible.yml* file *(see above)*, when it is included via the *57_plans_test.plan.yml*, will
have the following variables available to it:
* sudouser
* deployuser
* sudo
* apt_packages_to_install

Note that *parameters in higher-level plan container files and in system config files will supercede those specified in
lower-level plan container files.*  Using this mechanism, it's possible for multiple systems to use the same plan
containers and yet retain the ability to customize plan behavior at the system config file level.

Also, values declared in the parameters section **are available to parameter substituion in the same file**.

Running Corrigible
==================

Once the system file and various plan files are in place, provisioning is as simple as:
```shell
corrigible somehost
```

Project Status
==============
The hard parts work and there's tests around key points.  It's been working for a number of projects for nearly two
years.  I've just (in early 2017) made it python3-friendly and now (in March 2017) I've done a fair bit of cleanup to
get the code in better shape for a couple of interviews, so the next step is:
* to allow for optional parallelism in execution based on the ordering (multiple, separate snippets with the same
sort-order number should be able to run in parallel)

Now that it's been in use for a variety of projects, I've gotten a feel for what features have actually been used and
what really hasn't ended up being particularly useful.  As of right now, v2 will likely include:
* no distinction between ansible snippets and plan files, snippet syntax will become a superset of ansible syntax
* provisioning for AWS, GCE, and Digital Ocean will be a part of the language
* added to the yaml syntax will be a way to include other yaml files
* rocket mode will be on by default, but will be opt-in for snippets (so everything runs every time, unless otherwise
directed). there will be options to run everything regardless of hash collisions and to treat everything as if it were a candidate for exclusion.
* there will be constants (see TODO)
* ability to reference parameter files so multiple system files can reference the same parameter file
* script hooks (use case: to check to see if the current checkpoint matches the latest in master)

Also, I've put up a [repository for examples](https://github.com/FredAtLandMetrics/corrigible-example1).

Contact
=======
Feedback is welcomed.  Feel free to email me at [fred@frameworklabs.us](mailto:fred@frameworklabs.us).  I do have a bit of a
spam problem, so please mention *corrigible* in the subject line.

Also, head to [Framework Labs](http://frameworklabs.us) for more information about the sort of work I do.  Please get
in touch if you have a project you would like help with!
