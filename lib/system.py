import os
import yaml
import copy
import jinja2
import re

# from jinja2 import Template

from .planfilestack import plan_file_stack_push
from .dirpaths import systems_dirpath
from .selector import run_selector_affirmative
from .sys_default_params import sys_default_parameters
#from .jinja_ext import ShellExtension, env

#env = jinja2.Environment(autoescape=False, extensions=[ShellExtension])
env = jinja2.Environment(autoescape=False)

SYSTEM_FILE_SUFFIX = "system"

_system_conf = None
def system_config(opts):
    global _system_conf
    try:
        if _system_conf is None:
            system_name = opts["system"]
            plan_file_stack_push(system_name)
            system_config_filepath = os.path.join(systems_dirpath(), "{}.{}".format(system_name, SYSTEM_FILE_SUFFIX))
            print("INFO: loading system config for: {}, at {}".format(system_name, system_config_filepath))
            with open (system_config_filepath, "r") as system_def_fh: 
                
                params = dict(list(sys_default_parameters().items()) + list(os.environ.items()))

                params["CMDLINE"] = os.environ["_"]
                params["CMDLINE_WITHOUT_SELECTORS"] = re.sub(r'--selectors=[^\s]+','', params["CMDLINE"])
                
                unrendered_system_def_str = system_def_fh.read()
                pass1_rendered_system_def_str = \
                    env.from_string(unrendered_system_def_str).render(**params)
                
                print("pass1: {}".format(pass1_rendered_system_def_str))
                
                # get params in pass1
                temp_conf = yaml.load(pass1_rendered_system_def_str)
                #print "temp_conf: {}".format(temp_conf)
                try:
                    parameter_dict = copy.copy(temp_conf['parameters'])
                except KeyError:
                    parameter_dict = None
                except Exception as e:
                    print("E: {}".format(str(e)))
                #print "CP100!!!"
                # merge in parameters (with os.environ trumping parameters)
                try:
                    assert(parameter_dict is None)
                    render_params = params
                except AssertionError:
                    render_params = dict(list(parameter_dict.items()) + list(os.environ.items()) + list(sys_default_parameters().items()))
                    #render_params = copy.copy(parameter_dict)
                    #for key, val in os.environ.iteritems():
                        #render_params[key] = val

                print("render params: {}".format(render_params))

                # final system config load
                pass2_rendered_system_def_str = \
                    env.from_string(unrendered_system_def_str).render(**render_params)
                # print "pass2: {}".format(pass2_rendered_system_def_str)
                
                # filter the output str (remove hosts that are excluded via selectors)
                rendered_system_def_str = \
                    _filter_system_def(pass2_rendered_system_def_str, opts)
                
                # print "rendered_system_def_str: {}".format(rendered_system_def_str)
                _system_conf = yaml.load(rendered_system_def_str)
                
    except IOError:
        print("\nERR: system config not found at: {}, system_config will be None\n".format(system_config_filepath))
    return _system_conf
    
#def _get_system_config_parameters(sysdef_str):
    
    
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

