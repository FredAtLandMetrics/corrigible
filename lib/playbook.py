# -*- coding: utf-8 -*-

import jinja2
import yaml
import heapq
import copy
import os
import subprocess
import tempfile
import six

from .system import system_config
from .exceptions import \
    PlanFileDoesNotExist, \
    PlanOmittedByRunSelector, \
    UnknownPlanEncountered, \
    FilesDictLacksListKey, \
    NoSudoUserParameterDefined, \
    UnparseablePlanFile, \
    DuplicatePlanInRocketMode, \
    RequiredParameterPlansNotProvided, \
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

    # get plans and params
    plans = mconf['plans'] if 'plans' in mconf else {}
    params = mconf['parameters'] if 'parameters' in mconf else {}
    params = dict(list(params.items()) + list(sys_default_parameters().items()) + list(os.environ.items()))

    if not bool(plans):
        print("WARN: no plans defined!")
        return

    # get the list output from the plans list
    try:
        list_output = _playbook_from_list(plans=plans, parameters=params)
    except PlanFileDoesNotExist as e:
        print("ERR: plan referenced for which no file was found: {}, stack: {}".\
            format(str(e), plan_file_stack_as_str()))
        return

    # ensure list output is not None
    if list_output is None:
        _write_to_playbook("# WARN: No playbook output!\n", opts)
        return

    # final filtering on playbook output
    playbook_output = list_output
    filtered_output = _filter_final_playbook_output(playbook_output)

    # if filtered output is non-empty string, just use the hash prefix, otherwise use hash prefix + filtered output
    if type(filtered_output) is not str or not bool(filtered_output):
        playbook_output = _playbook_hashes_prefix(params)
    else:
        playbook_output = "{}\n{}".format(_playbook_hashes_prefix(params), filtered_output)

    # write playbook output
    _write_to_playbook(playbook_output, opts)


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
    except (yaml.ParserError, yaml.ScannerError) as e:
        print("ERR: encountered error parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(str(e), raw))


def _playbook_from_list(**kwargs):
    """produces playbook output from a plans list (as in what results from a yaml load of a plan file)"""

    params = kwargs['parameters'] if 'parameters' in kwargs else {}

    # validate plans list parameter
    try:
        plans_list = kwargs["plans"]
    except KeyError:
        raise RequiredParameterPlansNotProvided()

    # build a list of tuples of the form: (sort_order, post-processed ansible directives as string)
    playbook_text_tuple_list = []
    for plans_dict in plans_list:

        # push file ref to the plan file stack
        dopop = False
        if 'plan' in plans_dict:
            plan_file_stack_push(plans_dict['plan'])
            dopop = True
        elif 'files' in plans_dict:
            plan_file_stack_push('files')
            dopop = True

        # build parameters to be passed into _playbook_from_dict, giving precedent to plan ref params, if present
        playbook_params = params
        if 'parameters' in plans_dict and type(plans_dict['parameters']) is dict:
            playbook_params = dict(list(playbook_params.items()) + list(plans_dict['parameters'].items()))

        playbook_dict_tuple = None
        try:
            # get output from _playbook_from_dict and add to playbook_text_tuple_list
            playbook_dict_tuple = _playbook_from_dict(plans=plans_dict, parameters=playbook_params)
        except (PlanOmittedByRunSelector, DuplicatePlanInRocketMode):
            pass

        if playbook_dict_tuple is not None:
            playbook_text_tuple_list.append(playbook_dict_tuple)

        # pop file ref from the plan file stack
        if dopop:
            plan_file_stack_pop()

    # return text ordered using tuple list
    return _text_from_tuple_list(*playbook_text_tuple_list)


def _merge_args(args_base, args_adding):
    """add two dicts, return merged version"""
    return dict(list(args_base.items()) + list(args_adding.items()))


def _text_from_tuple_list(*args):
    """given a list of tuples of the form: (order, txt), produce a string containing the text fragments
       ordered according to the order value in the tuples"""
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
        
    return ret


def _playbook_from_dict__plan(plan_name, params):
    """given a plan name and any params from an overriding context, return a list containing a tuple
    of the form (x,y) where x is the order number for the plan and y is the playbook output as a string"""

    # raise an exception if rocket mode is on and plan, in its current form, has already been run at some point in
    # the past
    if rocket_mode() and plan_hash_filepath_exists(plan=plan_name):
        raise DuplicatePlanInRocketMode

    # index and filepath
    plan_ndx = plan_index(plan_name)
    plan_path = plan_filepath(plan_name)

    # read plan yaml contents from file
    try:
        fh = open(plan_path, "r")
        raw_yaml_str = fh.read()
        fh.close()
    except TypeError:
        raise PlanFileDoesNotExist(plan_name)

    # PASS #1 - process the yaml contents to extract params
    try:
        if bool(params is not None and type(params) is dict and bool(params)):
            pass1_rendered_yaml_str = env.from_string(raw_yaml_str).render(params)
            template_render_params = copy.copy(params)
        else:
            pass1_rendered_yaml_str = env.from_string(raw_yaml_str).render()
            template_render_params = {}
        pass1_yaml_struct = yaml.load(pass1_rendered_yaml_str)
    except yaml.YAMLError as e:
        print("ERR: encountered error parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(str(e), raw_yaml_str))
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

    # PASS #2 - render the yaml
    try:
        if bool(template_render_params):
            pass2_rendered_yaml_str = env.from_string(raw_yaml_str).render(template_render_params)
        else:
            pass2_rendered_yaml_str = env.from_string(raw_yaml_str).render()
        yaml_struct = yaml.load(pass2_rendered_yaml_str)
    except (yaml.ParserError, yaml.ScannerError) as e:
        print("ERR: encountered error parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(str(e), raw_yaml_str))
        raise
    except jinja2.TemplateSyntaxError as e:
        print("ERR: Template jinja syntax error ({}) in {}".format(str(e), plan_filepath))
        raise

    # process as either a corrigible plan or an ansible playbook
    if bool(type(yaml_struct) is dict and 'plans' in yaml_struct):

        # corrigible plan, recurse and add rocket mode hash suffix
        playbook_dict_output = _playbook_from_dict(plans=yaml_struct, parameters=params)

        if bool(playbook_dict_output is not None):
            _, plan_text = playbook_dict_output[0]
            return [(plan_ndx, "{}\n{}\n".format(plan_text, _hash_stanza_suffix(plan_name, params)))]
        else:
            return None
    else:

        # ansible plan, add rocket mode hash suffix
        if bool(type(yaml_struct) is list and len(yaml_struct) > 0):
            return [(plan_ndx, "{}\n{}\n".format(pass2_rendered_yaml_str, _hash_stanza_suffix(plan_name, params)))]
        else:
            raise UnparseablePlanFile()


def _str_bool(v):
    """convert a string rep of yes or true to a boolean True, all else to False"""
    if (type(v) is str and v.lower() in ['yes', 'true']) or \
        (type(v) is bool and bool(v)):
        return True
    return False


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
    return tuple(ret)
    
    
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

    
def _playbook_from_dict__inline(snippet, order):
    """given a snippet in dict form and an order int, return a list containing a tuple
    of the form (x,y) where x is the order number for the plan and y is the playbook output as a string"""
    return [(order, yaml.dump(snippet))]

def _playbook_from_dict(plans, parameters):
    """given a dict containing plans, plan, files, or inline key, return a list containing a tuple
        of the form (x,y) where x is the order of the playbook snippet and y is the playbook snippet as str"""

    # if parameters defined in plans dict, merge with processed_parameters from overriding contexts
    processed_parameters = parameters if 'parameters' not in plans else _merge_args(plans['parameters'], parameters)

    if 'plans' in plans:
        return [(MAX_PLAN_ORDER, _playbook_from_list(plans=plans['plans'], parameters=processed_parameters))]

    # handle plan type: plan file
    if 'plan' in plans:
        if 'run_selectors' in plans and not run_selector_affirmative(plans['run_selectors']):
            raise PlanOmittedByRunSelector()
        try:
            return _playbook_from_dict__plan(plans['plan'], processed_parameters)
        except UnparseablePlanFile as e:
            print("ERR: unparseable plan encountered: {}, stack: {}".format(str(e), plan_file_stack_as_str()))
            raise

    elif 'files' in plans:
        return _playbook_from_dict__files(plans['files'], processed_parameters)

    elif 'inline' in plans:
        if 'ansible' not in plans['inline']:
            raise MalformedInlineAnsibleSnippet()
        return _playbook_from_dict__inline(
            plans['inline']['ansible'],
            plans['inline']['order'] if 'order' in plans['inline'] else MIN_PLAN_ORDER
        )
    else:
        raise UnknownPlanEncountered()


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


