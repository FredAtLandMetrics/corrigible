Introduction
============

Corrigible builds on the capabilities of the fantastic automated configuration tool, [ansible](http://www.ansible.com/home), by adding:
* more flexible re-use of ansible directives
* introduces directive ordering by group (e.g. to ensure, for instance, that all user accounts are added before any cron jobs are installed)
* orchestrate multiple, simplified playbooks with intuitive, meta-informative "directive" files
* simplified variable substitution in playbooks
* runlevels - use the same code to manage full and partial playbook runs
    
and it's intended purpose is to remove the following from the ansible workflow:
* libraries of separately-maintained playbooks with duplicated directives
* single playbooks with multiple goal sets