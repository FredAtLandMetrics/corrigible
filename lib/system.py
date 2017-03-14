import os
import yaml
import copy
import jinja2
import re

from .planfilestack import plan_file_stack_push
from .dirpaths import systems_dirpath
from .selector import run_selector_affirmative
from .sys_default_params import sys_default_parameters


# init jinja environment
env = jinja2.Environment(autoescape=False)


SYSTEM_FILE_SUFFIX = "system"


_system_conf = None


def system_config(opts):
    """return the processed systemconfig yaml as a struct"""
    global _system_conf

    # just return the config struct if this has been done before
    if _system_conf is not None:
        return _system_conf

    # determine full system config filepath
    system_name = opts["system"]
    plan_file_stack_push(system_name)
    system_config_filepath = os.path.join(systems_dirpath(), "{}.{}".format(system_name, SYSTEM_FILE_SUFFIX))

    # read the system config to string
    try:
        with open (system_config_filepath, "r") as system_def_fh:
            unrendered_system_def_str = system_def_fh.read()
    except IOError:
        print("\nERR: system config not found at: {}, system_config will be None\n".format(system_config_filepath))
        return None

    # build the pass1_render_params dict
    pass1_render_params = dict(list(sys_default_parameters().items()) + list(os.environ.items()))
    pass1_render_params["CMDLINE"] = os.environ["_"]
    pass1_render_params["CMDLINE_WITHOUT_SELECTORS"] = re.sub(r'--selectors=[^\s]+','', pass1_render_params["CMDLINE"])

    # pass 1: read to struct as is, extract parameters section for pass 2
    pass1_rendered_system_def_str = env.from_string(unrendered_system_def_str).render(**pass1_render_params)
    pass_1_system_dict = yaml.load(pass1_rendered_system_def_str)
    parameter_dict = None if 'parameters' not in pass_1_system_dict else pass_1_system_dict['parameters']

    # build the pass2_render_params_dict
    pass2_render_params = pass1_render_params \
        if parameter_dict is None \
        else dict(list(parameter_dict.items()) + list(pass1_render_params.items()))

    # pass 2: render the yaml using parameter from environment and from system file itself
    pass2_rendered_system_def_str = env.from_string(unrendered_system_def_str).render(**pass2_render_params)

    # filter the rendered yaml str (remove hosts that are excluded via selectors)
    unfiltered_config_dict = yaml.load(pass2_rendered_system_def_str)
    hosts_list = unfiltered_config_dict['hosts']
    new_hosts_list = []
    for host in hosts_list:
        if 'run_selectors' in host and not run_selector_affirmative(host['run_selectors']):
            continue
        new_hosts_list.append(host)
    unfiltered_config_dict['hosts'] = new_hosts_list

    # load the filtered yaml string to a dict
    _system_conf = unfiltered_config_dict

    return _system_conf
