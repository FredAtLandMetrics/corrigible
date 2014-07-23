import jinja2
import yaml
import heapq

from jinja2 import Template

from corrigible.lib.system import system_config
from corrigible.lib.exceptions import PlanFileDoesNotExist, \
                                      PlanOmittedByRunSelector, \
                                      UnknownPlanEncountered
from corrigible.lib.planfilestack import plan_file_stack_push, plan_file_stack_pop
from corrigible.lib.plan import plan_index, plan_filepath
jinja2.Environment(autoescape=False)

MAX_DIRECTIVE_ORDER = 9999999

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
            if 'item' in plans_dict:
                plan_file_stack_push(plans_dict['item'])
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
        
        
        
        return (MAX_DIRECTIVE_ORDER, ret)
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
    for item in sorted(retlist):
        order, txt = item
        ret += "{}\n".format(txt)
        
    if not bool(ret):
        return None
        
    return ret
      
def _playbook_from_dict__plan(plan_name, params):      
    plan_ndx = plan_index(plan_name)
    #plan_filepath = plan_filepath(plan_name)
    plan_path = plan_filepath(plan_name)
    print "plan path: {}".format(plan_path)
    try:
                        
        with open(plan_path, "r") as fh:
            dict_yaml_text = None
            if params:
                #print "params!: {}".format(params)
                initial_template_text = fh.read()
                #print "init temp txt: {}".format(initial_template_text)
                dict_yaml_text = Template(initial_template_text).render(params)
                #print "cp -after"
            else:
                dict_yaml_text = Template(fh.read()).render()

            yaml_struct = yaml.load(dict_yaml_text)
            if type(yaml_struct) is list and len(yaml_struct) == 1:
                yaml_struct = yaml_struct[0]
                
            if 'plans' in yaml_struct.keys() or \
                'files' in yaml_struct.keys():
                #print "calling with yaml struct"
                _, plan_text =  _playbook_from_dict(plans=yaml_struct, parameters=params)
                return [(plan_ndx, "{}\n".format(plan_text))]
            else:
                return [(plan_ndx, "{}\n".format(dict_yaml_text))]
            #return (plan_index, template_text)
    except TypeError:
        raise PlanFileDoesNotExist(plan_name)
    except UnknownPlanEncountered:
        print "encountered error with {}".format(plan_path)
        raise
    except jinja2.exceptions.TemplateSyntaxError:
        #print "ERR: Template syntax error in {}".format(plan_filepath)
        raise        
    
def _playbook_from_dict__files(files_list, params):
    
    #print "params: {}".format(params)
    
    assert(bool(files_list))
    
    tasks_header = '- hosts: all\n  user: {}\n  sudo: True\n  tasks:\n'.format(params['sudouser'])
    
    files = {}
    for f in files_list:
        
        txt = '    - copy: src={} dest={}'.format(f['source'], f['destination'])
        if 'mode' in f:
            txt += ' mode={}'.format(str(f['mode']))
        if 'owner' in f:
            txt += ' owner={}'.format(str(f['owner']))
        if 'group' in f:
            txt += ' group={}'.format(str(f['group']))
        txt += '\n'
        
        order = '0'
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
            
            try:
                plan_name = plans_dict['item']
                print "plan name: {}".format(plan_name)
                
                if 'run_selectors' in plans_dict and \
                   not _run_selector_affirmative(plans_dict['run_selectors']):
                    raise PlanOmittedByRunSelector()
                
                return _playbook_from_dict__plan(plan_name, params)
            except KeyError:
                try:
                    print "FILES!!!"
                    files_list = plans_dict['files']
                    print "files_list: {}".format(str(files_list))
                    return _playbook_from_dict__files(files_list, params)
                except KeyError:
                    raise UnknownPlanEncountered()
           
    except KeyError:
        raise RequiredParameterPlansNotProvided()
