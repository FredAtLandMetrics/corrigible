import os

def envvar_cap_var(environment_variable_name, **kwargs):
    try:
        return os.environ[environment_variable_name]
    except KeyError:
        try:
            return kwargs['default']
        except KeyError:
            return None
    
def machines_dirpath():
    return envvar_cap_var('CORRIGIBLE_MACHINES',default='{}/machines'.format(corrigible_path()))

def directives_dirpath():
    return envvar_cap_var('CORRIGIBLE_DIRECTIVES',default='{}/directives'.format(corrigible_path()))

def files_dirpath():
    return envvar_cap_var('CORRIGIBLE_FILES',default='{}/files'.format(corrigible_path()))

def corrigible_path():
    return envvar_cap_var('CORRIGIBLE_PATH',default='/usr/local/etc/corrigible')