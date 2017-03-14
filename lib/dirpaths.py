import os
import tempfile

# the temp execution dirpath
tmp_exec_dirpath = None

def deduce_dirpath(environment_variable_name, **kwargs):
    """if the envvar is defined, return it otherwise return the default"""
    try:
        return os.environ[environment_variable_name]
    except KeyError:
        return kwargs['default'] if 'default' in kwargs else None

def systems_dirpath():
    """returns the dirpath where the systems files will be found"""
    return deduce_dirpath('CORRIGIBLE_SYSTEMS', default='{}/systems'.format(corrigible_path()))

def plans_dirpath():
    """returns the dirpath where the systems files will be found"""
    return deduce_dirpath('CORRIGIBLE_PLANS', default='{}/plans'.format(corrigible_path()))

def files_dirpath():
    """returns the dirpath where the systems files will be found"""
    return deduce_dirpath('CORRIGIBLE_FILES', default='{}/files'.format(corrigible_path()))

def corrigible_path():
    """returns the dirpath where the systems, plans and files directories will be found"""
    return deduce_dirpath('CORRIGIBLE_PATH', default='/usr/local/etc/corrigible')

def hashes_dirpath():
    """returns the dirpath where the plan hashes will be found"""
    return os.environ['CORRIGIBLE_HASHES'] if 'CORRIGIBLE_HASHES' in os.environ else "/corrigible/hashes"

def temp_exec_dirpath():
    """returns the dirpath to the temp execution directory for this process"""
    global tmp_exec_dirpath

    # if the temp exec dirpath is still none, create the directory and symlink the files directory
    if tmp_exec_dirpath is None:
        tmp_exec_dirpath = tempfile.mkdtemp()
        os.symlink(files_dirpath(), os.path.join(tmp_exec_dirpath, os.path.basename(files_dirpath())))
        
    return tmp_exec_dirpath