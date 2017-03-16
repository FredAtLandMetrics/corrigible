# -*- coding: utf-8 -*-

import jinja2
import yaml
import heapq
import copy
import os
import subprocess
import tempfile
import six
import pprint

from .system import system_config
from .exceptions import \
    PlanFileDoesNotExist, \
    UnknownPlanEncountered, \
    FilesDictLacksListKey, \
    NoSudoUserParameterDefined, \
    MalformedInlineAnsibleSnippet
from .planfilestack import \
    plan_file_stack_push, \
    plan_file_stack_pop, \
    plan_file_stack_as_str
from .plan import plan_index, plan_filepath
from .selector import run_selector_affirmative
from .dirpaths import temp_exec_dirpath, hashes_dirpath
from .sys_default_params import sys_default_parameters
from .planhash import plan_hash_filepath, plan_hash_filepath_exists
from .rocketmode import rocket_mode


# init jinja environment
env = jinja2.Environment(autoescape=False)


# the top and bottom of the plan order scale
MAX_PLAN_ORDER = 9999999
MIN_PLAN_ORDER = 0


def ansible_playbook_filepath(opts):
    """returns a filepath to the ansible playbook that is the corrigible output"""
    return os.path.join(temp_exec_dirpath(), "provision_{}.playbook".format(opts['system'])) \
        if "playbook_output_file" not in opts or opts["playbook_output_file"] is None \
        else opts["playbook_output_file"]


def run_ansible_playbook(hosts_filepath, playbook_filepath):
    """calls ansible playbook with specified playbook file and hostsfile"""

    # chdir to temp exec dirpath (so all refs to files can start with 'files/')
    os.chdir(temp_exec_dirpath())
    
    subprocess.call(
        ["ansible-playbook", "-vvvv", '-i', hosts_filepath, playbook_filepath],
        env=_merge_args(
            os.environ,
            {
                'PATH': os.environ["SAFE_CORRIGIBLE_PATH"] \
                    if "SAFE_CORRIGIBLE_PATH" in os.environ \
                    else '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'
            }
        )
    )


def write_hashes_fetch_playbook(opts):
    """fetch rocketmode hashes from remote machine"""

    mconf = system_config(opts)

    # get plans and params
    plans = mconf['plans'] if 'plans' in mconf else {}
    params = mconf['parameters'] if 'parameters' in mconf else {}

    # augment params with sys params and os environ variables
    params = dict(list(params.items()) + list(sys_default_parameters().items()) + list(os.environ.items()))

    # handle no plans
    if not bool(plans):
        print("WARN: no plans defined!")
        return

    # handle unknown plan
    try:
        playbook_output = _playbook_hashes_prefix(params, fetch_hashes=True)
    except PlanFileDoesNotExist as e:
        print("ERR: plan referenced for which no file was found: {}, stack: {}".\
            format(str(e), plan_file_stack_as_str()))
        raise

    # write the playbook output
    with open(ansible_playbook_filepath(opts), "w") as fh:
        fh.write(playbook_output)


def write_ansible_playbook(opts):
    """main corrigible output function, writes ansible playbook"""

    mconf = system_config(opts)

    snippet_structure = _get_playbook_snippet_structure(opts, mconf)

    # parameterless_snippet_structure = __redact_params(snippet_structure)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(parameterless_snippet_structure)

    playbook_output = _snippet_structure_to_string(snippet_structure)

    print("playbook_output: {}".format(playbook_output))

    # ensure list output is not None
    if  playbook_output is None or (type(playbook_output) is str and len(playbook_output) < 1):
        _write_to_playbook("# WARN: No playbook output!\n", opts)
        return

    # final filtering on playbook output
    filtered_output = _filter_final_playbook_output(playbook_output)

    # if filtered output is non-empty string, just use the hash prefix, otherwise use hash prefix + filtered output
    if type(filtered_output) is not str or not bool(filtered_output):
        playbook_output = _playbook_hashes_prefix(_system_level_parameters(opts))
    else:
        playbook_output = "{}\n{}".format(_playbook_hashes_prefix(_system_level_parameters(opts)), filtered_output)

    # write playbook output
    _write_to_playbook(playbook_output, opts)



def _snippet_structure_to_string(s):

    def omit_reason_list(omit_reasons_list):
        return [omission["reason"] for omission in omit_reasons_list]

    # produce simple list of reasons
    omit_reasons = []
    if bool(s["omit_reasons_list"]):
        omit_reasons = omit_reason_list(s["omit_reasons_list"])

    # if we're omitted by run_selector, there's no need to go on
    if "run_selector" in omit_reasons:
        return ""

    num_producing_sub_plans = 0

    # if s just has text, ret = text
    ret = ""
    if "plan_output_text" in s:
        ret = s["plan_output_text"]

    # otherwise if s has a list of other snippet structs
    elif "plan_output_list" in s:
        output_tuple_list = []
        for snip_struct in s["plan_output_list"]:
            snippet_str = _snippet_structure_to_string(snip_struct)
            if type(snippet_str) is str and len(snippet_str) > 0:
                output_tuple_list.append((snip_struct["order"], snippet_str))
                num_producing_sub_plans += snip_struct["num_changed_plans"]

            print("output_tuple_list: {}".format(output_tuple_list))
        ret = _text_from_tuple_list(output_tuple_list)

    # if ret is empty return empty string
    if type(ret) is str and len(ret) < 1:
        return ""

    # return ret if 1) there's no omissions at all or 2) there's an existing hash for this plan AND there are
    #  sub-snippets that managed to produce output (i.e. there was a change which prevented an existing hash
    #  omission in at least one sub-snippet)
    if not bool(omit_reasons) or ("existing_hash" in omit_reasons and num_producing_sub_plans > 0):

        # there should be a plan name for every plan other than the system plan, and there should also be a hash suffix
        # for every non-omitted plan
        if s["plan_name"] is not None:
            return "{}\n{}\n".format(ret, _hash_stanza_suffix(s["plan_name"], s["params"]))
        else:
            return ret

    # otherwise return an empty string
    return ""


def _get_playbook_snippet_structure(opts, plan_tree_struct, snippet_depth=0, plan_name=None, parameters=None, order=MIN_PLAN_ORDER):

    omit_reasons_list = []

    if snippet_depth < 1:
        parameters = _system_level_parameters(opts)

    # --- case I: a system or non-ansible plan
    if "plans" in plan_tree_struct:
        plan_output_list = []
        if snippet_depth > 0:
            if "parameters" in plan_tree_struct:
                print("parameters: {}\n{}".format(parameters, plan_tree_struct["parameters"]))
                parameters = _merge_args(parameters, plan_tree_struct["parameters"])
                # parameters = dict(list(parameters) + list(plan_tree_struct["parameters"]))
        num_changed_plans = 0
        for plan_dict in plan_tree_struct["plans"]:
            plan_dict_snippet_output = _get_playbook_snippet_structure(opts, plan_dict, snippet_depth=snippet_depth + 1, parameters=parameters)
            num_changed_plans += plan_dict_snippet_output["num_changed_plans"]
            if plan_dict_snippet_output is not None:
                plan_output_list.append(plan_dict_snippet_output)

        return dict(
            plan_output_list=plan_output_list,
            omit_reasons_list=omit_reasons_list,
            order=order,
            plan_name=plan_name,
            params=copy.copy(parameters),
            node_type="plans",
            num_changed_plans=num_changed_plans
        )

    # --- case II: an entry in a plans list
    if "plan" in plan_tree_struct:
        num_changed_plans = 0
        record_plan_name = plan_tree_struct["plan"]

        # bail if excluded by run_selectors
        if 'run_selectors' in plan_tree_struct and not run_selector_affirmative(plan_tree_struct['run_selectors']):
            omit_reasons_list.append(
                dict(
                    plan_name=record_plan_name,
                    reason="run_selector"
                )
            )

        if rocket_mode() and plan_hash_filepath_exists(plan=record_plan_name):
            omit_reasons_list.append(
                dict(
                    plan_name=record_plan_name,
                    reason="existing_hash"
                )
            )
        else:
            num_changed_plans += 1

        # index and filepath
        plan_ndx = plan_index(record_plan_name)
        plan_path = plan_filepath(record_plan_name)

        # read plan yaml contents from file
        try:
            fh = open(plan_path, "r")
            raw_yaml_str = fh.read()
            fh.close()
        except TypeError:
            raise PlanFileDoesNotExist(plan_name)

        if "parameters" in plan_tree_struct:
            parameters = _merge_args(parameters, plan_tree_struct["parameters"])
            # parameters = dict(list(parameters) + list(plan_tree_struct["parameters"]))

        # PASS #1 - process the yaml contents to extract params
        try:
            if bool(parameters is not None and type(parameters) is dict and bool(parameters)):
                pass1_rendered_yaml_str = env.from_string(raw_yaml_str).render(parameters)
                template_render_params = copy.copy(parameters)
            else:
                pass1_rendered_yaml_str = env.from_string(raw_yaml_str).render()
                template_render_params = {}
            pass1_yaml_struct = yaml.load(pass1_rendered_yaml_str)
        except yaml.YAMLError as e:
            print(
                "ERR: encountered error parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(str(e),
                                                                                                            raw_yaml_str))
            raise
        except jinja2.TemplateSyntaxError as e:
            print("ERR: Template jinja syntax error ({}) in {}".format(str(e), plan_filepath))
            raise

        # PASS #1 - set any parameters that have not been overriden by a declaration in a higher-level scope
        if bool(
            'parameters' in pass1_yaml_struct and
            type(pass1_yaml_struct['parameters']) is dict and
            bool(pass1_yaml_struct['parameters'])
        ):
            for key, val in six.iteritems(pass1_yaml_struct['parameters']):
                if not bool(key in template_render_params):
                    template_render_params[key] = val

        # PASS #2 - render the yaml, load to yaml_struct
        try:
            if bool(template_render_params):
                pass2_rendered_yaml_str = env.from_string(raw_yaml_str).render(template_render_params)
            else:
                pass2_rendered_yaml_str = env.from_string(raw_yaml_str).render()
            yaml_struct = yaml.load(pass2_rendered_yaml_str)
        except (yaml.parser.ParserError, yaml.parser.ScannerError) as e:
            print("ERR: encountered error({}) parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(type(e), str(e),
                                                                                                              raw_yaml_str))
            raise
        except jinja2.TemplateSyntaxError as e:
            print("ERR: Template jinja syntax error ({}) in {}".format(str(e), plan_filepath))
            raise

        # plan is a corrigible plan, recurse
        if "plans" in yaml_struct:
            return_dict = _get_playbook_snippet_structure(opts, yaml_struct, snippet_depth=snippet_depth + 1, parameters=parameters, order=plan_ndx, plan_name=record_plan_name)
            return_dict["omit_reasons_list"] = omit_reasons_list if not bool(return_dict["omit_reasons_list"]) else list(omit_reasons_list + return_dict["omit_reasons_list"])
            return return_dict

        # plan is an ansible plan, return as str
        return dict(
            plan_name=record_plan_name,
            plan_output_text=pass2_rendered_yaml_str,
            omit_reasons_list=omit_reasons_list,
            order=plan_ndx,
            params=copy.copy(parameters),
            plan_type="plan",
            num_changed_plans=num_changed_plans
        )

    # --- case III: files stanza
    if "files" in plan_tree_struct:
        files_order=MIN_PLAN_ORDER
        if "parameters" in plan_tree_struct["files"]:
            parameters = _merge_args(parameters, plan_tree_struct["files"]["parameters"])
            # parameters = dict(list(parameters) + list(plan_tree_struct["files"]["parameters"]))
            if "order" in plan_tree_struct["files"]["parameters"]:
                files_order = plan_tree_struct["files"]["parameters"]["order"]
        files_output_list = _playbook_from_dict__files(plan_tree_struct["files"], parameters)
        return dict(
            plan_output_text=_text_from_tuple_list(files_output_list),
            omit_reasons_list=omit_reasons_list,
            order=files_order,
            plan_name=plan_name,
            params=copy.copy(parameters),
            plan_type="files",
            num_changed_plans=0
        )

    # --- case IV: inline stanza
    if "inline" in plan_tree_struct:
        if 'ansible' not in plan_tree_struct['inline']:
            raise MalformedInlineAnsibleSnippet()
        return dict(
            plan_output_text=yaml.dump(plan_tree_struct['inline']['ansible']),
            omit_reasons_list=omit_reasons_list,
            order=plan_tree_struct['inline']['order'] if 'order' in plan_tree_struct['inline'] else MIN_PLAN_ORDER,
            plan_name=plan_name,
            params=copy.copy(parameters),
            plan_type="inline",
            num_changed_plans=0
        )

    raise UnknownPlanEncountered()


def _playbook_from_dict__files_list(files_list, params, **kwargs):
    """given the files list and a list of params from an overriding context, return a list containing a tuple
    of the form (x,y) where x is the order number for the plan and y is the playbook output as a string"""

    # insist on sudo
    if 'sudouser' not in params:
        raise NoSudoUserParameterDefined()

    arg_data = (('src', ['source', 'src']),
                ('dest', ['destination', 'dest', 'dst']),
                ('mode', 'mode'),
                ('owner', 'owner'),
                ('group', 'group'))
    
    files = {}
    for f in files_list:
        # print("f: {}".format(f))
        arg_strs = []
        for arg_tuple in arg_data:
            
            ansible_arg_key_str, corrigible_arg_keys = arg_tuple
            #print("key: {}".format(str(corrigible_arg_keys)))
            if (type(corrigible_arg_keys) is not list):
                corrigible_arg_keys = [corrigible_arg_keys]
                
            for corrigible_arg_key in corrigible_arg_keys:
                
                # handle the various acceptable forms of source, dest
                newargstr = None
                if corrigible_arg_key in kwargs:
                    ansible_arg_val_str = kwargs[corrigible_arg_key]

                    if ansible_arg_key_str == 'src':
                        if ('template' in kwargs and _str_bool(kwargs['template'])) or \
                               ('template' in f and _str_bool(f['template'])):
                            with open(os.path.join(temp_exec_dirpath(), ansible_arg_val_str), "r") as sfh:
                                raw_template_contents_str = sfh.read()
                                fh, filepath = tempfile.mkstemp()
                                with open(filepath, 'w') as dfh:
                                    dfh.write(env.from_string(raw_template_contents_str).render(params))
                                ansible_arg_val_str = filepath
                    newargstr = '{}={}'.format(ansible_arg_key_str, ansible_arg_val_str)

                elif corrigible_arg_key in f and newargstr is None:
                    ansible_arg_val_str = f[corrigible_arg_key]

                    if ansible_arg_key_str == 'src':
                        if ('template' in kwargs and _str_bool(kwargs['template'])) or \
                                ('template' in f and _str_bool(f['template'])):

                            with open(os.path.join(temp_exec_dirpath(), ansible_arg_val_str), "r") as sfh:
                                raw_template_contents_str = str(sfh.read().encode('utf-8','ignore'))

                                fh, filepath = tempfile.mkstemp()
                                with open(filepath, 'w') as dfh:
                                    dfh.write(env.from_string(raw_template_contents_str).render(params))

                                ansible_arg_val_str = filepath


                    newargstr = '{}={}'.format(ansible_arg_key_str, ansible_arg_val_str)

                if newargstr is not None:
                    arg_strs.append(newargstr)

        # populate files dict with key: order, val: copy stanzas for that order level
        copy_directive_str = '    - copy: {}\n'.format(" ".join(arg_strs))
        order_int = int(kwargs['order']) if 'order' in kwargs else MIN_PLAN_ORDER
        order_str = str(order_int)
        try:
            files[order_str] += copy_directive_str
        except KeyError:
            tasks_header = '- hosts: all\n  user: {}\n  sudo: True\n  tasks:\n'.format(params['sudouser'])
            files[order_str] = "{}{}".format(tasks_header, copy_directive_str)

    # return files dict in tuple form
    ret = []
    for order_str, txt in six.iteritems(files):
        ret.append((int(order_str), txt))
    return ret
    
    
def _playbook_from_dict__files_dict(files_dict, params):
    """given a files dict and a list of params from an overriding context, return a list containing a tuple
    of the form (x,y) where x is the order number for the plan and y is the playbook output as a string"""
    if "list" not in files_dict:
        raise FilesDictLacksListKey()

    if "parameters" in files_dict and bool(files_dict["parameters"]):
        files_params = files_dict["parameters"]
        return _playbook_from_dict__files_list(files_dict["list"], params, **files_params)
    return _playbook_from_dict__files_list(files_dict["list"], params)
    
    
def _playbook_from_dict__files(files_list, params):
    """given a files list and a list of params from an overriding context, return a list containing a tuple
    of the form (x,y) where x is the order number for the plan and y is the playbook output as a string"""
    if type(files_list) is list and bool(files_list):
        return _playbook_from_dict__files_list(files_list, params)
    elif type(files_list) is dict and bool(files_list):
        return _playbook_from_dict__files_dict(files_list, params)

    
def _str_bool(v):
    """convert a string rep of yes or true to a boolean True, all else to False"""
    if (type(v) is str and v.lower() in ['yes', 'true']) or \
        (type(v) is bool and bool(v)):
        return True
    return False


def _merge_args(args_base, args_adding):
    """add two dicts, return merged version"""
    return dict(list(args_base.items()) + list(args_adding.items()))


def _text_from_tuple_list(*args):
    """given a list of tuples of the form: (order, txt), produce a string containing the text fragments
       ordered according to the order value in the tuples"""

    print("args: {}".format(args))

    retlist = []
    for tuple_list in args:
        for playbook_text_tuple in tuple_list:
            ordernum, playbook_text = playbook_text_tuple
            heapq.heappush(retlist, (ordernum, playbook_text))
    ret = ""
    for plan in sorted(retlist):
        order, txt = plan
        ret += "{}\n".format(txt)

    if not bool(ret):
        return None

    print("returning: {}".format(ret))

    return ret


def _write_to_playbook(content, opts):
    """write content to ansible playbook filepath"""
    with open(ansible_playbook_filepath(opts), "w") as fh:
        fh.write(content)


def _filter_final_playbook_output(raw):
    """for right now, just load as yaml and dump it back out...just a placeholder for possible future use"""
    if type(raw) is not str or not bool(raw):
        print("INFO: no playbook output to filter")
        return
    try:
        as_struct = yaml.load(raw)
        as_string = yaml.dump(as_struct)
        return as_string
    except (yaml.parser.ParserError, yaml.parser.ScannerError) as e:
        print("ERR: encountered error({}) parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(type(e), str(e), raw))


def _playbook_hashes_prefix(params, **kwargs):
    """build the playbook hashes prefix stanza"""
    fetch_hashes_str = ""
    if "fetch_hashes" in kwargs:
        fetch_hashes_str = """
    - name: write listing of hashes dir to file
      shell: /bin/ls {} > /tmp/corrigible_hashes_list_remote
    - name: fetch the hashes files list
      fetch: src=/tmp/corrigible_hashes_list_remote dest=/tmp/corrigible_hashes_list flat=yes
        """.format(hashes_dirpath())

    if 'rootuser' in params:

        return """
- hosts: all
  user: {}
  sudo: True
  tasks:
    - name: ensure hashes dir exists
      file: state=directory path={}
      {}
        """.format(params['rootuser'], hashes_dirpath(), fetch_hashes_str)
    else:
        return """
- hosts: all
  user: {}
  sudo: yes
  tasks:
    - name: ensure hashes dir exists
      file: state=directory path={}
      {}
        """.format(params['rootuser'], hashes_dirpath(), fetch_hashes_str)


def _hash_stanza_suffix(plan_name, params):
    """return a stanza for touching the plan hash file for rocketmode"""
    try:

        ret = """
- hosts: all
  user: {}
  sudo: yes
  tasks:
    - name: touch plan hash file
      shell: touch {}

        """.format(params['rootuser'], plan_hash_filepath(plan_name))
    except KeyError:
        ret = """
- hosts: all
  tasks:
    - name: touch plan hash file
      shell: touch {}

        """.format(plan_hash_filepath(plan_name))
    return ret


def _system_level_parameters(opts):
    mconf = system_config(opts)
    params = mconf['parameters'] if 'parameters' in mconf else {}
    params = dict(list(params.items()) + list(sys_default_parameters().items()) + list(os.environ.items()))
    return params

def __redact_params(snippet_struct):
    """used to reduce the output when debugging, this will convert all params with a redacted str"""
    parameterless_snippet_structure = copy.copy(snippet_struct)
    parameterless_snippet_structure["params"] = "<redacted>"

    if "plan_output_list" in parameterless_snippet_structure:
        redacted_plan_output_list = []
        for plan_output_dict in parameterless_snippet_structure["plan_output_list"]:
            redacted_plan_output_list.append(__redact_params(plan_output_dict))
        parameterless_snippet_structure["plan_output_list"] = redacted_plan_output_list

    return parameterless_snippet_structure



