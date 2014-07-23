import os
import re
import heapq
from corrigible.lib.dirpaths import systems_dirpath, plans_dirpath, files_dirpath

_plan_filename_map = None
_plan_filepath_map = None
_plan_sortorder_map = None
def _ensure_plan_filename_map():
    global _plan_filename_map
    global _plan_sortorder_map
    global _plan_filepath_map
    
    #print "_ensure_plan_filename_map entered"
    
    if _plan_filename_map is None:
        _plan_filename_map = []
        _plan_sortorder_map = {}
        _plan_filepath_map = {}
        #plan_files_dirpath = os.path.join(os.path.dirname(__file__),
                                            #'..',
                                            #'provision',
                                            #'plans')
        plan_files_dirpath = plans_dirpath()
        #print "plan files dirpath: {}".format(plan_files_dirpath)
        for filename in os.listdir(plan_files_dirpath):
            #print "listdir result: {}".format(filename)
            if os.path.isfile(os.path.join(plan_files_dirpath,filename)):
                #print "examining: {}".format(filename)
                
                plan_match = re.search(r"^(\d+)\_(.*)\.plan\.yml$", filename)
                if plan_match:
                    sort_order = int(plan_match.group(1))
                    plan_name = plan_match.group(2)
                    
                    #print "sort_order: {}, plan_name: {}".format(sort_order, plan_name)
                    
                    _plan_sortorder_map[plan_name] = sort_order
                    
                    
                    #print "adding plan filepath[{}]: {}".format(plan_name, os.path.join(plan_files_dirpath, filename))
                    _plan_filepath_map[plan_name] = \
                        os.path.join(plan_files_dirpath, filename)
                    
                    heapq.heappush(_plan_filename_map,
                                   (sort_order,
                                    plan_name,
                                    os.path.join(plan_files_dirpath, filename)))
                                   
                ansible_match = re.search(r"^(\d+)\_(.*)\.ansible\.yml$", filename)
                if ansible_match:
                    sort_order = int(ansible_match.group(1))
                    plan_name = ansible_match.group(2)
                    
                    #print "sort_order: {}, plan_name: {}".format(sort_order, plan_name)
                    
                    _plan_sortorder_map[plan_name] = sort_order
                    
                    #print "adding ansible filepath[{}]: {}".format(plan_name, os.path.join(plan_files_dirpath, filename))
                    _plan_filepath_map[plan_name] = \
                        os.path.join(plan_files_dirpath, filename)
                    
                    heapq.heappush(_plan_filename_map,
                                   (sort_order,
                                    plan_name,
                                    os.path.join(plan_files_dirpath, filename)))
                    
                    
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
    #print "plan_filepath entered (plan: {})".format(plan_name)
    _ensure_plan_filename_map()
    try:
        return os.path.abspath(_plan_filepath_map[plan_name])
    except KeyError:
        return None
