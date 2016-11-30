import os
import re
import heapq
from corrigible.lib.dirpaths import systems_dirpath, plans_dirpath, files_dirpath

def _plan_files_iterator():
    for root, dirnames, filenames in os.walk(plans_dirpath()):
        for fn in filenames:
            yield os.path.abspath(os.path.join(root, fn))

    
_plan_filename_map = None
_plan_filepath_map = None
_plan_sortorder_map = None
def _ensure_plan_filename_map():
    global _plan_filename_map
    global _plan_sortorder_map
    global _plan_filepath_map
    
    if _plan_filename_map is None:
        _plan_filename_map = []
        _plan_sortorder_map = {}
        _plan_filepath_map = {}

        plan_files_dirpath = plans_dirpath()
        plan_iter = _plan_files_iterator()
        for filepath in plan_iter:
            if os.path.isfile(os.path.join(plan_files_dirpath,filepath)):

                plan_match = re.search(r"^(\d+)\_(.*)\.plan\.yml$", os.path.basename(filepath))
                if plan_match:
                    sort_order = int(plan_match.group(1))
                    plan_name = plan_match.group(2)
                    
                    _plan_sortorder_map[plan_name] = sort_order
                    
                    
                    _plan_filepath_map[plan_name] = filepath
                    
                    heapq.heappush(_plan_filename_map,
                                   (sort_order,
                                    plan_name,
                                    filepath))
                                   
                ansible_match = re.search(r"^(\d+)\_(.*)\.ansible\.yml$", os.path.basename(filepath))
                if ansible_match:
                    sort_order = int(ansible_match.group(1))
                    plan_name = ansible_match.group(2)
                    
                    _plan_sortorder_map[plan_name] = sort_order
                    
                    _plan_filepath_map[plan_name] = filepath
                    
                    heapq.heappush(_plan_filename_map,
                                   (sort_order,
                                    plan_name,
                                    filepath))
                    
                    
    return _plan_filename_map

def plan_filename_map():
    _ensure_plan_filename_map()
    return _plan_filename_map

def plan_sortorder_map():
    _ensure_plan_filename_map()
    return _plan_sortorder_map

def plan_index(plan_name):
    global _plan_sortorder_map
    _ensure_plan_filename_map()
    try:
        return plan_sortorder_map()[plan_name]
    except KeyError:
        pass

def plan_filepath(plan_name):
    global _plan_filepath_map
    _ensure_plan_filename_map()
    try:
        return os.path.abspath(_plan_filepath_map[plan_name])
    except KeyError:
        return None
