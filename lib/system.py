import os
import yaml
import copy

from jinja2 import Template

from corrigible.lib.planfilestack import plan_file_stack_push
from corrigible.lib.dirpaths import systems_dirpath
from corrigible.lib.selector import run_selector_affirmative
from corrigible.lib.sys_default_params import sys_default_parameters

SYSTEM_FILE_SUFFIX = "system"

_system_conf = None
def system_config(opts):
    global _system_conf
    try:
        if _system_conf is None:
            system_name = opts["system"]
            plan_file_stack_push(system_name)
            print "INFO: loading system config for: {}, at {}".format(system_name, system_config_filepath())
            with open (system_config_filepath(), "r") as system_def_fh:
                
                params = dict(sys_default_parameters().items() + os.environ.items())
                
                unrendered_system_def_str = system_def_fh.read()
                pass1_rendered_system_def_str = \
                    Template(unrendered_system_def_str).render(**params)
                
                # get params in pass1
                temp_conf = yaml.load(pass1_rendered_system_def_str)
                try:
                    parameter_dict = copy.copy(temp_conf['parameters'])
                except KeyError:
                    parameter_dict = None
                except Exception as e:
                    print "E: {}".format(str(e))

                # merge in parameters (with os.environ trumping parameters)
                try:
                    assert(parameter_dict is None)
                    render_params = params
                except AssertionError:
                    render_params = dict(parameter_dict.items() + os.environ.items() + sys_default_parameters().items())

                # final system config load
                pass2_rendered_system_def_str = \
                    Template(unrendered_system_def_str).render(**render_params)

                # filter the output str (remove hosts that are excluded via selectors)
                rendered_system_def_str = \
                    _filter_system_def(pass2_rendered_system_def_str, opts)
                _system_conf = yaml.load(rendered_system_def_str)
                
    except IOError:
        print "\nERR: system config not found at: {}, system_config will be None\n".format(system_config_filepath)
    return _system_conf

_sys_conf_fp = None
def system_config_filepath(sysconf_filepath=None):
    global _sys_conf_fp
    if sysconf_filepath is not None:
        _sys_conf_fp = sysconf_filepath
    return _sys_conf_fp
    # return os.path.join(systems_dirpath(), "{}.{}".format(system_name, SYSTEM_FILE_SUFFIX))

    
def _filter_system_def(raw, opts):
    system_conf = yaml.load(raw)
    
    hosts_list = system_conf['hosts']
    #print "hosts_list: {}".format(str(hosts_list))
    new_hosts_list = []
    for host in hosts_list:
        #print "host: {}".format(str(host))
        if 'run_selectors' in host and not run_selector_affirmative(host['run_selectors']):
            continue
        new_hosts_list.append(host)
    system_conf['hosts'] = new_hosts_list    
    #print "pre-dump"
    as_string = yaml.dump(system_conf)    
    #print "as_string: {}".format(as_string)
    return as_string

