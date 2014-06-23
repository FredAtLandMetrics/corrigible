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
    return envvar_cap_var('CORRIGIBLE_MACHINES',default='/usr/local/etc/corrigible/machines')

def directives_dirpath():
    return envvar_cap_var('CORRIGIBLE_DIRECTIVES',default='/usr/local/etc/corrigible/directives')

def files_dirpath():
    return envvar_cap_var('CORRIGIBLE_FILES',default='/usr/local/etc/corrigible/files')
