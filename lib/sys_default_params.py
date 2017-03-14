# this module allows for the definition of any variables that need to be provided to the system files by corrigible

import os

def sys_default_parameters():
    """returns a dict of corrigible system variables to be made available to the templating engine for the system and
        plan files"""
    return { 'sys_local_user': os.environ['USER'] }
