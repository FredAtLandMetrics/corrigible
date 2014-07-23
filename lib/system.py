_system_conf = None
def system_config(opts):
    global _system_conf
    try:
        if _system_conf is None:
            system_name = opts["system"]
            plan_file_stack_push(system_name)
            system_config_filepath = os.path.join(systems_dirpath(), "{}.meta".format(system_name))
            #print "INFO: loading system config for: {}, at {}".format(system_name, system_config_filepath)
            with open (system_config_filepath, "r") as system_def_fh: 
                rendered_system_def_str = Template(system_def_fh.read()).render(**os.environ)
                
                rendered_system_def_str = _filter_system_def(rendered_system_def_str, opts)
                #print "rendered_system_def_str: {}".format(rendered_system_def_str)
                _system_conf = yaml.load(rendered_system_def_str)
                
    except IOError:
        print "\nERR: system config not found at: {}, system_config will be None\n".format(system_config_filepath)
    return _system_conf
    
def _filter_system_def(raw, opts):
    system_conf = yaml.load(raw)
    
    hosts_list = system_conf['hosts']
    #print "hosts_list: {}".format(str(hosts_list))
    new_hosts_list = []
    for host in hosts_list:
        #print "host: {}".format(str(host))
        if 'run_selectors' in host and not _run_selector_affirmative(host['run_selectors']):
            continue
        new_hosts_list.append(host)
    system_conf['hosts'] = new_hosts_list    
    #print "pre-dump"
    as_string = yaml.dump(system_conf)    
    #print "as_string: {}".format(as_string)
    return as_string

