# -*- coding: utf-8 -*-

import jinja2
import yaml
import heapq
import copy
import os
import subprocess
import tempfile
import traceback

from jinja2 import Template

from corrigible.lib.system import system_config
from corrigible.lib.exceptions import \
    PlanFileDoesNotExist, \
    PlanOmittedByRunSelector, \
    UnknownPlanEncountered, \
    FilesSectionEmpty, \
    FilesDictLacksListKey, \
    NoSudoUserParameterDefined, \
    UnparseablePlanFile, \
    DuplicatePlanInRocketMode, \
    RequiredParameterPlansNotProvided, \
    MalformedInlineAnsibleSnippet
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

jinja2.Environment(autoescape=False)

MAX_PLAN_ORDER = 9999999


def ansible_playbook_filepath(opts):
    """returns a filepath to the ansible playbook that is the corrigible output"""
    try:
        output_filepath = opts["playbook_output_file"]
        assert(output_filepath is not None)
        return output_filepath
    except (AssertionError, KeyError):
        return os.path.join(temp_exec_dirpath(),
                            "provision_{}.playbook".format(opts['system']))


def run_ansible_playbook(**kwargs):
    """run the specified ansible playbook"""
    try:
        environ = _merge_args(os.environ, {'PATH': os.environ["SAFE_CORRIGIBLE_PATH"]})
    except KeyError:
        environ = _merge_args(
            os.environ,
            {'PATH': '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'}
        )
    
    # so all refs to files can start with 'files/'
    os.chdir(temp_exec_dirpath())
    
    subprocess.call(
        ["ansible-playbook", "-vvvv", '-i', kwargs['hosts_filepath'], kwargs['playbook_filepath']],
        env=environ
    )


def run_hashes_fetch_playbook(opts):
    """fetch rocketmode hashes from remote machine"""
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
            print "ERR: plan referenced for which no file was found: {}, stack: {}".\
                format(str(e), plan_file_stack_as_str())
        except AssertionError:
            print "WARN: no plans defined!"
    except TypeError:
        if mconf is None:
            print "ERR: No system config, not writing ansible playbook file"
            return
        else:
            raise
    

def write_ansible_playbook(opts):
    """main corrigible output function, writes ansible playbook"""

    try:
        mconf = system_config(opts)
    except TypeError:
        print "ERR: No system config, not writing ansible playbook file"
        return

    try:
        plans = mconf['plans']
    except KeyError:
        plans = {}

    # assemble params
    try:
        params = mconf['parameters']
    except KeyError:
        params = {}
    params = dict(params.items() + sys_default_parameters().items() + os.environ.items())

    if not bool(plans):
        print "WARN: no plans defined!"
        return

    # get the list output from the plans list
    try:
        list_output = _playbook_from_list(plans=plans, parameters=params)
    except PlanFileDoesNotExist as e:
        print "ERR: plan referenced for which no file was found: {}, stack: {}".\
            format(str(e), plan_file_stack_as_str())
        return

    # ensure list output is not None
    if list_output is None:
        __write_to_playbook("# WARN: No playbook output!\n", opts)
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
    __write_to_playbook(playbook_output, opts)


def __write_to_playbook(content, opts):
    """write content to ansible playbook filepath"""
    with open(ansible_playbook_filepath(opts), "w") as fh:
        fh.write(content)


def _filter_final_playbook_output(raw):
    """for right now, just load as yaml and dump it back out...just a placeholder for possible future use"""
    try:
        assert(type(raw) is str and bool(raw))
        as_struct = yaml.load(raw)
        as_string = yaml.dump(as_struct) 
        return as_string
    except (yaml.ParserError, yaml.ScannerError) as e:
        print "ERR: encountered error parsing playbook output:\n\nERR:\n{}\n\nRAW YAML INPUT:\n{}".format(str(e), raw)
    except AssertionError:
        print "INFO: no playbook output to filter"


def _playbook_from_list(**kwargs):
    """produces playbook output from a plans list (as in what results from a yaml load of a plan file)"""

    try:
        params = kwargs['parameters']
    except KeyError:
        params = {}

    # validate plans list parameter
    try:
        plans_list = kwargs["plans"]
    except KeyError:
        raise RequiredParameterPlansNotProvided()

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

        try:

            # build parameters to be passed into _playbook_from_dict, giving precedent to plan ref params, if present
            playbook_params = params
            if 'parameters' in plans_dict and type(plans_dict['parameters']) is dict:
                playbook_params = dict(playbook_params.items() + plans_dict['parameters'].items())

            # get output from _playbook_from_dict and add to playbook_text_tuple_list
            playbook_dict_tuple = _playbook_from_dict(plans=plans_dict,
                                                      parameters=playbook_params)
            if playbook_dict_tuple is not None:
                playbook_text_tuple_list.append(playbook_dict_tuple)

        except (PlanOmittedByRunSelector, DuplicatePlanInRocketMode):
            pass

        # pop file ref from the plan file stack
        if dopop:
            plan_file_stack_pop()

    # return text ordered using tuple list
    return _text_from_tuple_list(*playbook_text_tuple_list)


def _merge_args(args_base, args_adding):
    """add two dicts, return merged version"""
    return dict(args_base.items() + args_adding.items())


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
    
    if rocket_mode() and plan_hash_filepath_exists(plan=plan_name):
        raise DuplicatePlanInRocketMode()
    
    plan_ndx = plan_index(plan_name)
    plan_path = plan_filepath(plan_name)
    
    try:
                        
        with open(plan_path, "r") as fh:
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
                assert('parameters' in pass1_yaml_struct and \
                       type(pass1_yaml_struct['parameters']) is dict and \
                       bool(pass1_yaml_struct['parameters']))
                for key,val in pass1_yaml_struct['parameters'].iteritems():
                    try:
                        assert(key in template_render_params)
                    except AssertionError:
                        template_render_params[key] = val
            except AssertionError:
                pass
                
            #print "template_render_params: {}".format(str(template_render_params))
                
            try:
                assert(bool(template_render_params))
                pass2_rendered_yaml_str = Template(raw_yaml_str).render(template_render_params)
            except AssertionError:
                pass2_rendered_yaml_str = Template(raw_yaml_str).render()
            
            yaml_struct = yaml.load(pass2_rendered_yaml_str)
        
            # so, now it's either a rendered ansible yml or a rendered plan yml
            try:
                assert(type(yaml_struct) is dict and 'plans' in yaml_struct)
                
                playbook_dict_output = _playbook_from_dict(plans=yaml_struct, parameters=params)
                try:
                    assert(playbook_dict_output is not None)
                    _, plan_text = playbook_dict_output
                    return [(plan_ndx, "{}\n{}\n".format(plan_text,_hash_stanza_suffix(plan_name, params)))]
                except AssertionError:
                    return None
            except AssertionError:
                try:
                    assert(type(yaml_struct) is list and len(yaml_struct) > 0)
                    return [(plan_ndx, "{}\n{}\n".format(pass2_rendered_yaml_str,_hash_stanza_suffix(plan_name, params)))]
                except AssertionError:
                    raise UnparseablePlanFile()
    except TypeError:
        raise PlanFileDoesNotExist(plan_name)
    except UnknownPlanEncountered:
        print "encountered error with {}".format(plan_path)
        raise
    except jinja2.exceptions.TemplateSyntaxError:
        #print "ERR: Template syntax error in {}".format(plan_filepath)
        raise        

def _str_bool(v):
    try:
        assert((type(v) is str and v.lower() in ['yes','true']) or
               (type(v) is bool and bool(v)))
        return True
    except AssertionError:
        return False

def _playbook_from_dict__files_list(files_list, params, **kwargs):
    #print "files_list: {}".format(files_list)
    try:
        assert('sudouser' in params)
    except AssertionError:
        raise NoSudoUserParameterDefined()
    
    tasks_header = '- hosts: all\n  user: {}\n  sudo: True\n  tasks:\n'.format(params['sudouser'])
    
    output_prefix = '    - copy: '
    output_suffix = '\n'
    
    arg_data = (('src', ['source', 'src']),
                ('dest', ['destination', 'dest', 'dst']),
                ('mode', 'mode'),
                ('owner', 'owner'),
                ('group', 'group'))
    
    files = {}
    for f in files_list:
        print "f: {}".format(f)
        arg_strs = []
        for arg_tuple in arg_data:
            
            ansible_arg_key_str, corrigible_arg_keys = arg_tuple
            #print "key: {}".format(str(corrigible_arg_keys))
            if (type(corrigible_arg_keys) is not list):
                corrigible_arg_keys = [corrigible_arg_keys]
                
            for corrigible_arg_key in corrigible_arg_keys:
                
                newargstr = None
                try:
                    assert(corrigible_arg_key in kwargs)
                    ansible_arg_val_str = kwargs[corrigible_arg_key]
                    
                    try:
                        assert(ansible_arg_key_str == 'src')
                        assert(('template' in kwargs and _str_bool(kwargs['template'])) or
                               ('template' in f and _str_bool(f['template'])))
                        
                        # HERE!!!
                        print "Got Template...params: {}".format(params)
                        with open(os.path.join(temp_exec_dirpath(), ansible_arg_val_str), "r") as sfh:
                            raw_template_contents_str = sfh.read()
                            fh, filepath = tempfile.mkstemp()
                            with open(filepath, 'w') as dfh:
                                dfh.write(Template(raw_template_contents_str).render(params))
                            ansible_arg_val_str = filepath
                        
                    except AssertionError:
                        pass
                    
                    except Exception as e:
                        print(
                            'unhandled exception encountered processing files list: ' +
                            '{}, {}\n{}'. \
                                format(
                                    str(e.__class__.__name__), 
                                    str(e.args),
                                    traceback.format_exc(),
                                )
                        )
                    
                    newargstr = '{}={}'.format(ansible_arg_key_str, ansible_arg_val_str)
                    break
                except AssertionError:
                    try:
                        assert(corrigible_arg_key in f)
                        assert(newargstr is None)
                        ansible_arg_val_str = f[corrigible_arg_key]
                        
                        try:
                            assert(ansible_arg_key_str == 'src')
                            assert(('template' in kwargs and _str_bool(kwargs['template'])) or
                                ('template' in f and _str_bool(f['template'])))
                            
                            # HERE!!!
                            with open(os.path.join(temp_exec_dirpath(), ansible_arg_val_str), "r") as sfh:
                                raw_template_contents_str = sfh.read().encode('utf-8','ignore')
                                fh, filepath = tempfile.mkstemp()
                                with open(filepath, 'w') as dfh:
                                    dfh.write(Template(raw_template_contents_str).render(params))
                                
                                ansible_arg_val_str = filepath
                            
                        except AssertionError:
                            pass
                         
                        except Exception as e:
                            print(
                                'unhandled exception encountered processing files list: ' +
                                '{}, {}\n{}'. \
                                    format(
                                        str(e.__class__.__name__), 
                                        str(e.args),
                                        traceback.format_exc(),
                                    )
                            )
                        
                        newargstr = '{}={}'.format(ansible_arg_key_str, ansible_arg_val_str)
                    except AssertionError:
                        continue   # I know, I know...it seems more explicit
                    
                if newargstr is not None:
                    arg_strs.append(newargstr)
        try:
            assert(len(arg_strs) > 0)
        except AssertionError:
            continue
        
        txt = output_prefix + " ".join(arg_strs) + output_suffix
        
        order = '0'
        try:
            order = kwargs['order']
        except KeyError:
            try:
                order = f['order']
            except KeyError:
                pass
        order_as_str = str(order)
        
        try:
            files[order_as_str] += txt
        except KeyError:
            files[order_as_str] = "{}{}".format(tasks_header, txt)
        
    ret = []
    for order_as_str, txt in files.iteritems():
        ret.append((int(order_as_str), txt))
        
    print "RET: {}".format(str(ret))
        
    return tuple(ret)            
    
    
def _playbook_from_dict__files_dict(files_dict, params):
    try:
        assert("list" in files_dict)
    except AssertionError:
        raise FilesDictLacksListKey()
    try:
        assert("parameters" in files_dict and bool(files_dict["parameters"]))
        files_params = files_dict["parameters"]
        return _playbook_from_dict__files_list(files_dict["list"], params, **files_params)
    except AssertionError:
        return _playbook_from_dict__files_list(files_dict["list"], params)
    
    
    
def _playbook_from_dict__files(files_list, params):
    
    #print "params: {}".format(params)
    try:
        assert(type(files_list) is list and bool(files_list))
        return _playbook_from_dict__files_list(files_list, params)
    except AssertionError:
        assert(type(files_list) is dict and bool(files_list))
        return _playbook_from_dict__files_dict(files_list, params)
    except Exception:
        raise FilesSectionEmpty()
    
def _playbook_from_dict__inline(snippet, order):
    return [(order, yaml.dump(snippet))]

def _playbook_from_dict(**kwargs):
    
    try:
        params = kwargs['parameters']
    except KeyError:
        params = {}    
    
    try:
        plans_dict = kwargs['plans']
        #print "plans({}), parameters({})".format(kwargs['plans'], params)
        
        try:
            params = _merge_args(plans_dict['parameters'], params)
        except KeyError:
            pass
        
        try:
            playbook_output =  _playbook_from_list(plans=plans_dict['plans'], parameters=params)
            return MAX_PLAN_ORDER, playbook_output
        except KeyError:
            
            # handle plan type: plan file
            try:
                plan_name = plans_dict['plan']
                #print "plan name: {}".format(plan_name)
                
                if 'run_selectors' in plans_dict and \
                   not run_selector_affirmative(plans_dict['run_selectors']):
                    raise PlanOmittedByRunSelector()
                
                return _playbook_from_dict__plan(plan_name, params)
            except KeyError:
                
                try:
                    
                    # handle plan type: files
                    files_list = plans_dict['files']
                    #print "files_list: {}".format(str(files_list))
                    ret = _playbook_from_dict__files(files_list, params)
                    #print "ret: {}".format(ret)
                    return ret
                except KeyError:
                    
                    try:
                        
                        print "plans dict: {}".format(plans_dict)
                        inline_snippet_container = plans_dict['inline']
                        try:
                            assert('ansible' in inline_snippet_container)
                            try:
                                order = inline_snippet_container['order']
                            except KeyError:
                                order = 0
                                
                            return _playbook_from_dict__inline(inline_snippet_container['ansible'], order)
                            
                        except AssertionError:
                            raise MalformedInlineAnsibleSnippet()
                        
                        
                        # return snippets as list of (order, ansible string)
                    except KeyError:    
                        raise UnknownPlanEncountered()
            except UnparseablePlanFile as e:
                print "ERR: unparseable plan encountered: {}, stack: {}".format(str(e), plan_file_stack_as_str())
           
    except KeyError:
        raise RequiredParameterPlansNotProvided()


def _playbook_hashes_prefix(params, **kwargs):
    """build the playbook hashes prefix stanza"""
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

        """.format(params['rootuser'], plan_hash_filepath(plan=plan_name))
    except KeyError:
        ret = """
- hosts: all
  tasks:
    - name: touch plan hash file
      shell: touch {}

        """.format(plan_hash_filepath(plan=plan_name))
    return ret


