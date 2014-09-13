# -*- coding: utf-8 -*-

import jinja2
import yaml
import copy
import os
import subprocess
import tempfile

from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError
from heapq import heappush, heappop
from corrigible.lib.system import system_config, system_config_filepath
from corrigible.lib.exceptions import \
    PlanFileDoesNotExist, \
    PlanOmittedByRunSelector, \
    UnknownPlanEncountered, \
    FilesSectionEmpty, \
    FilesDictLacksListKey, \
    NoSudoUserParameterDefined, \
    UnparseablePlanFile, \
    DuplicatePlanInRocketMode, \
    RequiredParameterContainerFilepathStackNotProvided, \
    RequiredParameterPlansNotProvided, \
    RequiredParameterCallDepthNotProvided, \
    RequiredParameterRunSelectorAffirmativeNotProvided, \
    IncomprehensiblePlanDict, \
    RequiredParameterOrderNotDefined
from corrigible.lib.planfilestack import \
    plan_file_stack_push, \
    plan_file_stack_pop, \
    plan_file_stack_as_str
from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.lib.selector import run_selector_affirmative
from corrigible.lib.dirpaths import temp_exec_dirpath, hashes_dirpath
from corrigible.lib.sys_default_params import sys_default_parameters
from corrigible.lib.planhash import plan_hash_filepath, plan_hash_filepath_exists
from corrigible.lib.rocketmode import rocket_mode
from yaml.scanner import MarkedYAMLError, ScannerError

jinja2.Environment(autoescape=False)

MAX_PLAN_ORDER = 9999999
_snippet_dicts = []


def ansible_playbook_filepath(opts):

    """return the filepath to the output ansible playbook"""

    try:
        output_filepath = opts["playbook_output_file"]
        assert(output_filepath is not None)
        return output_filepath
    except (AssertionError, KeyError):
        return os.path.join(temp_exec_dirpath(),
                            "provision_{}.playbook".format(opts['system']))


def run_ansible_playbook(**kwargs):

    """run ansible-plabook using the hosts and playbook filepaths provided in kwargs"""
    
    try:
        environ = _merge_args(os.environ, {'PATH': os.environ["SAFE_CORRIGIBLE_PATH"]})
    except KeyError:
        environ = _merge_args(
            os.environ,
            {
                'PATH': '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'
            }
        )
    
    # so all refs to files can start with 'files/'
    os.chdir(temp_exec_dirpath())
    
    subprocess.call(
        [
            "ansible-playbook",
            "-vvvv",
            '-i',
            kwargs['hosts_filepath'],
            kwargs['playbook_filepath']
        ],
        env=environ
    )


def write_ansible_playbook(opts):

    """using the plans list provided in opts, produce an ansible playbook yaml file"""

    mconf = None
    try:
        mconf = system_config(opts)
        
        try:
            plans = mconf['plans']
        except KeyError:
            plans = {}
            
        try:
            params = mconf['parameters']
        except KeyError:
            params = {}
        print "params(write_ansible_playbook(pre)): {}\n".format(params)

        params = dict(params.items() + sys_default_parameters().items() + os.environ.items())
        print "params(write_ansible_playbook): {}\n".format(params)
        try:
            assert(bool(plans))
            with open(ansible_playbook_filepath(opts), "w") as fh:
                
                _gen_playbook_from_list(
                    plans=plans,
                    parameters=params,
                    container_filepath_stack=[system_config_filepath()],
                    call_depth=0
                )
                playbook_output = build_playbook_string_from_snippets()
                
                try:
                    assert(playbook_output is not None)

                    try:
                        filtered_output = _filter_final_playbook_output(playbook_output)
                        assert(type(filtered_output) is str and bool(filtered_output))
                        playbook_output = "{}\n{}".format(
                            _playbook_hashes_prefix(params),
                            filtered_output
                        )
                    except AssertionError:
                        playbook_output = _playbook_hashes_prefix(params)
                    
                    if bool(playbook_output):
                        fh.write(playbook_output)
                    else:
                        fh.write("# WARN: No plans found!\n")
                except AssertionError:
                    fh.write("# WARN: No playbook output!\n")
        except PlanFileDoesNotExist as e:
            msg = "ERR: plan referenced for which no file was found: {}, stack: {}"
            print msg.format(str(e), plan_file_stack_as_str())
        except AssertionError:
            print "WARN: no plans defined!"
            
    except TypeError:
        if mconf is None:
            print "ERR: No system config, not writing ansible playbook file"
            return
        else:
            raise

_rs_exclusion_list = None
def _run_selector_exclusion_list():
    global _snippet_dicts
    global _rs_exclusion_list
    if _rs_exclusion_list is None:
        _rs_exclusion_list = []
        for snippet in _snippet_dicts:
            if not bool(snippet['run_selector_affirmative']):
                _rs_exclusion_list.append(snippet['container_filepath_stack'])
    print "excluding: {}".format(_rs_exclusion_list)
    return _rs_exclusion_list

def _prohibited_by_run_selector(filepath_stack):
    exclude_stack_list = _run_selector_exclusion_list()
    for exclude_stack in  exclude_stack_list:
        if len(filepath_stack) < len(exclude_stack):
            continue
        prohibited = True
        for ndx in range(len(exclude_stack)):
            if not bool(exclude_stack[ndx] == filepath_stack[ndx]):
                prohibited = False
                break
        if prohibited:
            return True
    return False

def build_playbook_string_from_snippets(**kwargs):
    global _snippet_dicts
    try:
        snippet_list = kwargs['snippets']
    except KeyError:
        snippet_list = _snippet_dicts

    print "snippet list: {}".format(snippet_list)

    snippet_heap = []
    for snippet in snippet_list:
        if not _prohibited_by_run_selector(snippet['container_filepath_stack']):
            heappush(snippet_heap, (snippet['order'], snippet['snippet_txt']))

    return "\n".join([x[1] for x in [heappop(snippet_heap) for i in range(len(snippet_heap))]])


def run_hashes_fetch_playbook(opts):
    mconf = None
    try:
        mconf = system_config(opts)
        try:
            plans = mconf['plans']
        except KeyError:
            plans = {}

        try:
            params = mconf['parameters']
        except KeyError:
            params = {}

        params = dict(params.items() + sys_default_parameters().items() + os.environ.items())
        try:
            assert(bool(plans))
            with open(ansible_playbook_filepath(opts), "w") as fh:
                playbook_output = _playbook_hashes_prefix(params, fetch_hashes=True)
                fh.write(playbook_output)
        except PlanFileDoesNotExist as e:
            print "ERR: plan referenced for which no file was found: {}, stack: {}". \
                format(str(e), plan_file_stack_as_str())
        except AssertionError:
            print "WARN: no plans defined!"
    except TypeError:
        if mconf is None:
            print "ERR: No system config, not writing ansible playbook file"
            return
        else:
            raise


def _gen_playbook_from_list(**kwargs):
    """call _gen_playbook_from_dict on each dicts in the plan list"""
    try:
        params = kwargs['parameters']
    except KeyError:
        params = {}
    
    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()

    try:
        container_filepath_stack = kwargs['container_filepath_stack']
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    try:
        plans_list = kwargs['plans']
    except KeyError:
        raise RequiredParameterPlansNotProvided()

    for plans_dict in plans_list:

        dopop = False
        if 'plan' in plans_dict:
            plan_file_stack_push(plans_dict['plan'])
            dopop = True
        elif 'files' in plans_dict:
            plan_file_stack_push('files')
            dopop = True

        try:
            _gen_playbook_from_dict(
                plans=plans_dict,
                parameters=params,
                call_depth=int(call_depth+1),
                container_filepath_stack=container_filepath_stack
            )
        except PlanOmittedByRunSelector:
            pass

        if dopop:
            plan_file_stack_pop()


def _gen_playbook_from_dict(**kwargs):
    """call one of several generator functions, dependant on included kwargs"""
    try:
        params = kwargs['parameters']
    except KeyError:
        params = {}

    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()

    try:
        plans_dict = kwargs['plans']
    except KeyError:
        raise RequiredParameterPlansNotProvided()

    try:
        container_filepath_stack = kwargs['container_filepath_stack']
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    try:
        params = _merge_args(plans_dict['parameters'], params)
    except KeyError:
        pass

    print "params(_gen_playbook_from_dict): {}".format(params)

    if 'plan' in plans_dict:
        _gen_playbook_from_dict__plan(
            plans_dict['plan'],
            params,
            call_depth=int(call_depth+1),
            run_selector_affirmative=_plan_dict_run_selector_affirmative(plans_dict),
            container_filepath_stack=container_filepath_stack
        )
    elif 'files' in plans_dict:
        _gen_playbook_from_dict__files(
            plans_dict['files'],
            params,
            call_depth=int(call_depth+1),
            container_filepath_stack=container_filepath_stack
        )
    elif 'inline' in plans_dict:
        inline_snippet_container = plans_dict['inline']
        _gen_playbook_from_dict__inline(
            inline_snippet_container['ansible'],
            _extract_order(inline_snippet_container),
            call_depth=int(call_depth+1),
            container_filepath_stack=container_filepath_stack
        )
    else:
        raise IncomprehensiblePlanDict()


def _gen_playbook_from_dict__plan(plan_name, params, **kwargs):

    """if plan is an ansible playbook, append a snippet to the snippets list. If it is a plan file, then
        grab parameters from the plan as needed and call _gen_playbook_from_list on the plans list"""

    try:
        runsel_affirmative = kwargs['run_selector_affirmative']
    except KeyError:
        raise RequiredParameterRunSelectorAffirmativeNotProvided()

    try:
        container_filepath_stack = copy.copy(kwargs['container_filepath_stack'])
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()

    if rocket_mode() and plan_hash_filepath_exists(plan=plan_name):
        raise DuplicatePlanInRocketMode()

    # determine path and index
    plan_ndx = plan_index(plan_name)
    plan_path = plan_filepath(plan_name)

    # we switched files, append to container filepath stack
    container_filepath_stack.append(plan_path)

    try:
                        
        with open(plan_path, "r") as fh:

            # -------------------------------------------------------------------------
            # read parameters from template and use that plus any provided params to
            # divine parameter struct to be used to render the template
            # -------------------------------------------------------------------------
            raw_yaml_str = fh.read()
            try:
                assert(params is not None and type(params) is dict and bool(params))
                pass1_rendered_yaml_str = Template(raw_yaml_str).render(params)
                template_render_params = copy.copy(params)
            except AssertionError:
                pass1_rendered_yaml_str = Template(raw_yaml_str).render()
                template_render_params = {}
                
            pass1_yaml_struct = yaml.load(pass1_rendered_yaml_str)
            
            try:
                assert('parameters' in pass1_yaml_struct and
                       type(pass1_yaml_struct['parameters']) is dict and
                       bool(pass1_yaml_struct['parameters']))
                for key, val in pass1_yaml_struct['parameters'].iteritems():
                    try:
                        assert(key in template_render_params)
                    except AssertionError:
                        template_render_params[key] = val
            except AssertionError:
                pass
                
            # -------------------------------------------------------------------------
            # render the template using the params, generate the yaml_struct
            # -------------------------------------------------------------------------
            try:
                assert(bool(template_render_params))
                pass2_rendered_yaml_str = Template(raw_yaml_str).render(template_render_params)
            except AssertionError:
                pass2_rendered_yaml_str = Template(raw_yaml_str).render()
            
            yaml_struct = yaml.load(pass2_rendered_yaml_str)
        
            # -------------------------------------------------------------------------
            # detect whether this is an ansible playbook or a corrigible plan.
            # handle accordingly
            # -------------------------------------------------------------------------
            try:
                # case 1: corrigible plan
                assert(type(yaml_struct) is dict and 'plans' in yaml_struct)
                _gen_playbook_from_list(
                    plans=yaml_struct['plans'],
                    parameters=params,
                    call_depth=int(call_depth+1),
                    container_filepath_stack=container_filepath_stack
                )
            except AssertionError:
                try:

                    # case 2: ansible
                    assert(type(yaml_struct) is list and len(yaml_struct) > 0)
                    _append_snippet_dict(
                        {
                            "snippet_txt": "{}\n{}\n".format(
                                pass2_rendered_yaml_str,
                                _touch_hash_stanza_suffix(plan_name, params)
                            ),
                            "order": plan_ndx,
                            "run_selector_affirmative": runsel_affirmative,
                            "container_filepath_stack": container_filepath_stack,
                            "call_depth": call_depth
                        }
                    )

                except AssertionError:
                    raise UnparseablePlanFile()

    except TypeError:
        raise PlanFileDoesNotExist(plan_name)
    except UnknownPlanEncountered:
        print "encountered error with {}".format(plan_path)
        raise
    except TemplateSyntaxError:
        raise


def _gen_playbook_from_dict__files_list(files_list, params, **kwargs):

    """append a snippet to the snippets list for each file in the list"""

    try:
        assert('sudouser' in params)
    except AssertionError:
        print "params: {}".format(params)
        raise NoSudoUserParameterDefined()
    
    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()
        
    try:
        container_filepath_stack = kwargs['container_filepath_stack']
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    tasks_header = '- hosts: all\n  user: {}\n  sudo: True\n  tasks:\n'.format(params['sudouser'])

    # append a snippet for each file in the files list
    for f in files_list:

        copy_args = _copy_directive_argstr(params, _merge_args(f, kwargs))
        copy_directive_txt = "{}    - copy: {}\n".format(tasks_header, copy_args)

        try:
            order_as_str = str(kwargs['order'])
        except KeyError:
            try:
                order_as_str = str(f['order'])
            except KeyError:
                order_as_str = '0'
        order = int(order_as_str)

        _append_snippet_dict(
            {
                "snippet_txt": copy_directive_txt,
                "order": order,
                "run_selector_affirmative": True,
                "container_filepath_stack": container_filepath_stack,
                "call_depth": call_depth
            }
        )


def _gen_playbook_from_dict__files_dict(files_dict, params, **kwargs):

    """call _gen_playbook_from_dict__files_list method on the 'list' attribute of the files dict"""

    try:
        assert("list" in files_dict)
    except AssertionError:
        raise FilesDictLacksListKey()

    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()

    try:
        container_filepath_stack = kwargs['container_filepath_stack']
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    try:
        assert("parameters" in files_dict and bool(files_dict["parameters"]))
        files_params = files_dict["parameters"]
        files_params['call_depth'] = int(call_depth+1)
        files_params['container_filepath_stack'] = container_filepath_stack
        return _gen_playbook_from_dict__files_list(files_dict["list"], params, **files_params)
    except AssertionError:
        return _gen_playbook_from_dict__files_list(
            files_dict["list"],
            params,
            call_depth=int(call_depth+1),
            container_filepath_stack=container_filepath_stack
        )
    
    
def _gen_playbook_from_dict__files(files_list, params, **kwargs):

    """call _gen_playbook_from_dict__files_list if files_list is a list, otherwise call
    _gen_playbook_from_dict__files_dict"""

    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()

    try:
        container_filepath_stack = kwargs['container_filepath_stack']
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    if type(files_list) is list and bool(files_list):
        return _gen_playbook_from_dict__files_list(
            files_list,
            params,
            call_depth=int(call_depth+1),
            container_filepath_stack=container_filepath_stack
        )
    elif type(files_list) is dict and bool(files_list):
        return _gen_playbook_from_dict__files_dict(
            files_list,
            params,
            call_depth=int(call_depth+1),
            container_filepath_stack=container_filepath_stack
        )
    else:
        raise FilesSectionEmpty()

    # try:
    #     assert(type(files_list) is list and bool(files_list))
    #     return _gen_playbook_from_dict__files_list(
    #         files_list,
    #         params,
    #         call_depth=int(call_depth+1),
    #         container_filepath_stack=container_filepath_stack
    #     )
    # except AssertionError:
    #     assert(type(files_list) is dict and bool(files_list))
    #     return _gen_playbook_from_dict__files_dict(
    #         files_list,
    #         params,
    #         call_depth=int(call_depth+1),
    #         container_filepath_stack=container_filepath_stack
    #     )
    # except Exception:
    #     raise FilesSectionEmpty()


def _gen_playbook_from_dict__inline(snippet, order, **kwargs):

    """append a snippet to the snippets list for the inline ansible snippet"""

    try:
        call_depth = kwargs['call_depth']
    except KeyError:
        raise RequiredParameterCallDepthNotProvided()

    try:
        container_filepath_stack = kwargs['container_filepath_stack']
    except KeyError:
        raise RequiredParameterContainerFilepathStackNotProvided()

    _append_snippet_dict(
        {
            "snippet_txt": yaml.dump(snippet),
            "order": order,
            "run_selector_affirmative": True,
            "container_filepath_stack": container_filepath_stack,
            "call_depth": call_depth
        }
    )


def _merge_args(args_base, args_adding):
    ret = dict(args_base.items() + args_adding.items())
    return ret


def _text_from_tuple_list(*args):
    retlist = []
    for tuple_list in args:
        #print "tuple_list: {}".format(tuple_list)
        for playbook_text_tuple in tuple_list:
            ordernum, playbook_text = playbook_text_tuple
            heappush(retlist, (ordernum, playbook_text))
    ret = ""
    for plan in sorted(retlist):
        order, txt = plan
        ret += "{}\n".format(txt)

    if not bool(ret):
        return None

    return ret


def _touch_hash_stanza_suffix(plan_name, params):
    try:

        ret = """
- hosts: all
  user: {}
  sudo: yes
  tasks:
    - name: touch plan hash file
      shell: touch {}

        """.format(params['rootuser'], plan_hash_filepath(plan=plan_name))
    except KeyError:
        ret = """
- hosts: all
  tasks:
    - name: touch plan hash file
      shell: touch {}

        """.format(plan_hash_filepath(plan=plan_name))
    return ret


def _str_bool(v):
    try:
        assert((type(v) is str and v.lower() in ['yes', 'true']) or
               (type(v) is bool and bool(v)))
        return True
    except AssertionError:
        return False


def _playbook_hashes_prefix(params, **kwargs):

    print "DBG: params: {}".format(params)

    try:
        assert(bool(kwargs['fetch_hashes']))
        fetch_hashes_str = """
    - name: write listing of hashes dir to file
      shell: /bin/ls {} > /tmp/corrigible_hashes_list_remote
    - name: fetch the hashes files list
      fetch: src=/tmp/corrigible_hashes_list_remote dest=/tmp/corrigible_hashes_list flat=yes
        """.format(hashes_dirpath())
    except (AssertionError, KeyError):
        fetch_hashes_str = ""

    try:
        ret = """
- hosts: all
  user: {}
  sudo: True
  tasks:
    - name: ensure hashes dir exists
      file: state=directory path={}
      {}
        """.format(params['rootuser'], hashes_dirpath(), fetch_hashes_str)
        return ret
    except KeyError:
        ret = """
- hosts: all
  tasks:
    - name: ensure hashes dir exists
      file: state=directory path={}
      {}
        """.format(hashes_dirpath(), fetch_hashes_str)
        return ret


def _filter_final_playbook_output(raw):
    try:
        assert(type(raw) is str and bool(raw))
        as_struct = yaml.load(raw)
        as_string = yaml.dump(as_struct)
        return as_string
    except (MarkedYAMLError, ScannerError) as e:
        print "ERR: encountered error parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(str(e), raw)
    except AssertionError:
        print "INFO: no playbook output to filter"


def _append_snippet_dict(d):
    global _snippet_dicts
    if type(d) is not list:
        d = [d]
    for dx in d:

        try:
            assert('order' in dx)
        except AssertionError:
            raise RequiredParameterOrderNotDefined()

        _snippet_dicts.append(dx)


def _plan_dict_run_selector_affirmative(plans_dict):
    # return bool(
    #     'run_selectors' in plans_dict and
    #     not run_selector_affirmative(plans_dict['run_selectors'])
    # )
    try:
        return bool(run_selector_affirmative(plans_dict['run_selectors']))
    except:
        return True  # default to true


def _extract_order(d, default=0):
    try:
        return d['order']
    except KeyError:
        return default


def _copy_directive_argstr(params, files_list_item):
    arg_data = (('src', ['source', 'src']),
                ('dest', ['destination', 'dest', 'dst']),
                ('mode', 'mode'),
                ('owner', 'owner'),
                ('group', 'group'))
    argstr_list = []
    for arg_tuple in arg_data:

        ansible_arg_key_str, corrigible_arg_keys = arg_tuple

        if type(corrigible_arg_keys) is not list:
            corrigible_arg_keys = [corrigible_arg_keys]

        for corrigible_arg_key in corrigible_arg_keys:
            try:
                ansible_arg_val_str = files_list_item[corrigible_arg_key]
            except KeyError:
                continue

            # if this is the src param and template mode is on, render the src file as a template
            # and substitute the new file for the requested file in the argstr
            has_template = bool('template' in files_list_item and _str_bool(files_list_item['template']))
            if ansible_arg_key_str == 'src' and has_template:

                with open(os.path.join(temp_exec_dirpath(), ansible_arg_val_str), "r") as sfh:
                    raw_template_contents_str = sfh.read().encode('utf-8', 'ignore')
                    fh, filepath = tempfile.mkstemp()
                    with open(filepath, 'w') as dfh:
                        dfh.write(Template(raw_template_contents_str).render(params))

                    ansible_arg_val_str = filepath

            newargstr = '{}={}'.format(ansible_arg_key_str, ansible_arg_val_str)
            if newargstr is not None:
                argstr_list.append(newargstr)

    if bool(argstr_list):
        return " ".join(argstr_list)

    return None
