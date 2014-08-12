import os
import tempfile

def envvar_cap_var(environment_variable_name, **kwargs):
    try:
        return os.environ[environment_variable_name]
    except KeyError:
        try:
            return kwargs['default']
        except KeyError:
            return None
    
def systems_dirpath():
    return envvar_cap_var('CORRIGIBLE_SYSTEMS',default='{}/systems'.format(corrigible_path()))

def plans_dirpath():
    return envvar_cap_var('CORRIGIBLE_PLANS',default='{}/plans'.format(corrigible_path()))

def files_dirpath():
    return envvar_cap_var('CORRIGIBLE_FILES',default='{}/files'.format(corrigible_path()))

def corrigible_path():
    return envvar_cap_var('CORRIGIBLE_PATH',default='/usr/local/etc/corrigible')

def hashes_dirpath():
    try:
        return os.environ['CORRIGIBLE_HASHES']
    except KeyError:
        return "/corrigible/hashes"


_temp_exec_dir = None
def temp_exec_dirpath():
    global _temp_exec_dir
    if _temp_exec_dir is None:
        _temp_exec_dir = tempfile.mkdtemp()
        os.symlink(files_dirpath(),
                   os.path.join(_temp_exec_dir,os.path.basename(files_dirpath())))
    return _temp_exec_dir