import os
import yaml
import copy
import jinja2
import re

from .planfilestack import plan_file_stack_push
from .dirpaths import systems_dirpath
from .selector import run_selector_affirmative
from .sys_default_params import sys_default_parameters

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
                
                # get params in pass1
                temp_conf = yaml.load(pass1_rendered_system_def_str)
                try:
                    parameter_dict = copy.copy(temp_conf['parameters'])
                except KeyError:
                    parameter_dict = None

                # merge in parameters (with os.environ trumping parameters)
                if parameter_dict is None:
                    render_params = params
                else:
                    render_params = dict(
                        list(parameter_dict.items()) + \
                        list(os.environ.items()) + \
                        list(sys_default_parameters().items())
                    )

                # final system config load
                pass2_rendered_system_def_str = env.from_string(unrendered_system_def_str).render(**render_params)

                # filter the output str (remove hosts that are excluded via selectors)
                rendered_system_def_str = _filter_system_def(pass2_rendered_system_def_str, opts)
                
                _system_conf = yaml.load(rendered_system_def_str)
                
    except IOError:
        print("\nERR: system config not found at: {}, system_config will be None\n".format(system_config_filepath))
    return _system_conf

    
def _filter_system_def(raw, opts):
    system_conf = yaml.load(raw)
    
    hosts_list = system_conf['hosts']
    new_hosts_list = []
    for host in hosts_list:
        if 'run_selectors' in host and not run_selector_affirmative(host['run_selectors']):
            continue
        new_hosts_list.append(host)
    system_conf['hosts'] = new_hosts_list    
    return yaml.dump(system_conf)

