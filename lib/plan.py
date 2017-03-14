import os
import re
from .dirpaths import systems_dirpath, plans_dirpath, files_dirpath


_plan_filepath_dict = None
_plan_sortorder_dict = None


def plan_index(plan_name):
    """given a valid plan name, returns the order as given by the numeric prefix on the filename, else return None"""
    _ensure_plan_indexes_created()
    try:
        return _plan_sortorder_dict[plan_name]
    except KeyError:
        return None


def plan_filepath(plan_name):
    """given a valid plan name, return the abs filepath for that plan, else return None"""
    _ensure_plan_indexes_created()
    try:
        return os.path.abspath(_plan_filepath_dict[plan_name])
    except KeyError:
        return None


def _plan_files_iterator():
    """an iterator over the filenames in the plans directory, yields an abs path to a plan at each iteration"""
    for root, dirnames, filenames in os.walk(plans_dirpath()):
        for fn in filenames:
            yield os.path.abspath(os.path.join(root, fn))

    
def _ensure_plan_indexes_created():
    """if they don't already exist, creates indexes, one that maps plan names to sort-order and another
    that maps plan names to abs filepaths"""

    global _plan_sortorder_dict
    global _plan_filepath_dict
    
    if _plan_sortorder_dict is None:
        _plan_sortorder_dict = {}
        _plan_filepath_dict = {}

        plan_files_dirpath = plans_dirpath()
        plan_iter = _plan_files_iterator()
        for filepath in plan_iter:
            if os.path.isfile(os.path.join(plan_files_dirpath,filepath)):

                plan_match = re.search(r"^(\d+)\_(.*)\.plan\.yml$", os.path.basename(filepath))
                if plan_match:
                    sort_order = int(plan_match.group(1))
                    plan_name = plan_match.group(2)
                    
                    _plan_sortorder_dict[plan_name] = sort_order
                    
                    
                    _plan_filepath_dict[plan_name] = filepath
                    
                ansible_match = re.search(r"^(\d+)\_(.*)\.ansible\.yml$", os.path.basename(filepath))
                if ansible_match:
                    sort_order = int(ansible_match.group(1))
                    plan_name = ansible_match.group(2)
                    
                    _plan_sortorder_dict[plan_name] = sort_order
                    
                    _plan_filepath_dict[plan_name] = filepath
                    
