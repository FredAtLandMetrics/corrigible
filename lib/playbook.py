import jinja2
import yaml
import heapq
import copy
import os
import subprocess

from jinja2 import Template

from corrigible.lib.system import system_config
from corrigible.lib.exceptions import PlanFileDoesNotExist, \
                                      PlanOmittedByRunSelector, \
                                      UnknownPlanEncountered, \
                                      FilesSectionEmpty, \
                                      FilesDictLacksListKey, \
                                      NoSudoUserParameterDefined
from corrigible.lib.planfilestack import plan_file_stack_push, \
                                         plan_file_stack_pop, \
                                         plan_file_stack_as_str
from corrigible.lib.plan import plan_index, plan_filepath
from corrigible.lib.selector import run_selector_affirmative
from corrigible.lib.dirpaths import temp_exec_dirpath

jinja2.Environment(autoescape=False)

MAX_PLAN_ORDER = 9999999

def ansible_playbook_filepath(opts):
    try:
        output_filepath = opts["playbook_output_file"]
        assert(output_filepath is not None)
        return output_filepath
    except (AssertionError, KeyError):
        return os.path.join(temp_exec_dirpath(),
                            "provision_{}.playbook".format(opts['system']))

def run_ansible_playbook(**kwargs):
    
    
    environ = _merge_args(os.environ,
                          { 'PATH': '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:' + \
                            '/usr/local/sbin' })
    
    # so all refs to files can start with 'files/'
    os.chdir(temp_exec_dirpath())
    
    subprocess.call(["ansible-playbook","-vvvv",
                     '-i', kwargs['hosts_filepath'],
                     kwargs['playbook_filepath']], env=environ)


def write_ansible_playbook(opts):
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
            
        playbook_output_filepath = ansible_playbook_filepath(opts)
        #print "INFO: writing ansible playbook data to {}".format(playbook_output_filepath)
        try:
            assert(bool(plans))
            with open(ansible_playbook_filepath(opts), "w") as fh:
                order, playbook_output = _playbook_from_list( plans=plans, parameters=params )
                
                playbook_output = _filter_final_playbook_output(playbook_output, opts)
                
                if bool(playbook_output):
                    fh.write(playbook_output)
                else:
                    fh.write("# WARN: No plans found!\n")
        except PlanFileDoesNotExist as e:
            print "ERR: plan referenced for which no file was found: {}, stack: {}".format(str(e), plan_file_stack_as_str())
        except AssertionError:
            print "WARN: no plans defined!"
            
    except TypeError:
        #print "system_config: {}".format(str(mconf))
        if mconf is None:
            print "ERR: No system config, not writing ansible playbook file"
            return
        else:
            raise
        
def _filter_final_playbook_output(raw, opts):
    as_struct = yaml.load(raw)
    as_string = yaml.dump(as_struct)    
    return as_string

def _playbook_from_list(**kwargs):
    try:
        params = kwargs['parameters']
    except KeyError:
        params = {}
    
    try:
        retlist= []
        
        #print "plans({}), parameters({})".format(kwargs['plans'], params)
        playbook_text_tuple_list = []
        for plans_dict in kwargs['plans']:
            
            dopop = False
            if 'plan' in plans_dict:
                plan_file_stack_push(plans_dict['plan'])
                dopop = True
            elif 'files' in plans_dict:
                plan_file_stack_push('files')
                dopop = True
            
            try:
                playbook_text_tuple_list.append(_playbook_from_dict(plans=plans_dict,
                                                                    parameters=params))
            except PlanOmittedByRunSelector:
                pass
            
            if dopop:
                plan_file_stack_pop()
                
        ret = _text_from_tuple_list(*playbook_text_tuple_list)
        
        
        
        return (MAX_PLAN_ORDER, ret)
    except KeyError:
        raise RequiredParameterPlansNotProvided()
   
def _merge_args(args_base, args_adding):
    #print "_merge_args: base({}), adding({})".format(args_base, args_adding)
    ret = copy.copy(args_base)
    for k,y in args_adding.iteritems():
        ret[k] = y
    #print "_merge_args returning {}".format(ret)
    return ret
   
def _text_from_tuple_list(*args):
    retlist = []
    for tuple_list in args:
        #print "tuple_list: {}".format(tuple_list)
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
    
    plan_ndx = plan_index(plan_name)
    plan_path = plan_filepath(plan_name)
    
    #plan_filepath = plan_filepath(plan_name)
    #print "plan path: {}".format(plan_path)
    #print "params({}): {}".format(str(type(params)), params)
    try:
                        
        with open(plan_path, "r") as fh:
            dict_yaml_text = None
            
            raw_yaml_str = fh.read()
            try:
                assert(params is not None and type(params) is dict and bool(params))
                #print "here1!"
                pass1_rendered_yaml_str = Template(raw_yaml_str).render(params)
                #print "here2!"
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
                _, plan_text =  _playbook_from_dict(plans=yaml_struct, parameters=params)
                return [(plan_ndx, "{}\n".format(plan_text))]
            except AssertionError:
                assert(type(yaml_struct) is list and len(yaml_struct) > 0)
                return [(plan_ndx, "{}\n".format(pass2_rendered_yaml_str))]
            
            #if type(yaml_struct) is list and len(yaml_struct) == 1:
                #yaml_struct = yaml_struct[0]
            #print "yaml_struct: {}".format(yaml_struct)
                
            #if 'plans' in yaml_struct.keys() or \
                #'files' in yaml_struct.keys():
                ##print "calling with yaml struct"
                #_, plan_text =  _playbook_from_dict(plans=yaml_struct, parameters=params)
                #return [(plan_ndx, "{}\n".format(plan_text))]
            #else:
                #return [(plan_ndx, "{}\n".format(pass2_rendered_yaml_str))]
            ##return (plan_index, template_text)
    except TypeError:
        raise PlanFileDoesNotExist(plan_name)
    except UnknownPlanEncountered:
        print "encountered error with {}".format(plan_path)
        raise
    except jinja2.exceptions.TemplateSyntaxError:
        #print "ERR: Template syntax error in {}".format(plan_filepath)
        raise        

def _playbook_from_dict__files_list(files_list, params, **kwargs):
    print "files_list: {}".format(files_list)
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
            print "key: {}".format(str(corrigible_arg_keys))
            if (type(corrigible_arg_keys) is not list):
                corrigible_arg_keys = [corrigible_arg_keys]
                
            for corrigible_arg_key in corrigible_arg_keys:
                
                newargstr = None
                try:
                    assert(corrigible_arg_key in kwargs)
                    newargstr = '{}={}'.format(ansible_arg_key_str, kwargs[corrigible_arg_key])
                    break
                except AssertionError:
                    try:
                        assert(corrigible_arg_key in f)
                        assert(newargstr is None)
                        newargstr = '{}={}'.format(ansible_arg_key_str, f[corrigible_arg_key])
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
        
    return ret            
    
    
def _playbook_from_dict__files_dict(files_dict, params):
    try:
        assert("list" in files_dict)
    except AssertionError:
        raise FilesDictLacksListKey()
    #print "cp1"
    try:
        #print "cp2"
        assert("parameters" in files_dict and bool(files_dict["parameters"]))
        files_params = files_dict["parameters"]
        #print "cp3"
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
            params = _merge_args(params, plans_dict['parameters'])
        except KeyError:
            pass
        
        try:
            return _playbook_from_list(plans=plans_dict['plans'],
                                       parameters=params)
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
           
    except KeyError:
        raise RequiredParameterPlansNotProvided()
