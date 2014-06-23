import os
import re
import heapq
from corrigible.lib.dirpaths import machines_dirpath, directives_dirpath, files_dirpath

_directive_filename_map = None
_directive_filepath_map = None
_directive_sortorder_map = None
def _ensure_directive_filename_map():
    global _directive_filename_map
    global _directive_sortorder_map
    global _directive_filepath_map
    
    print "_ensure_directive_filename_map entered"
    
    if _directive_filename_map is None:
        _directive_filename_map = []
        _directive_sortorder_map = {}
        _directive_filepath_map = {}
        #directive_files_dirpath = os.path.join(os.path.dirname(__file__),
                                            #'..',
                                            #'provision',
                                            #'directives')
        directive_files_dirpath = directives_dirpath()
        print "directive files dirpath: {}".format(directive_files_dirpath)
        for filename in os.listdir(directive_files_dirpath):
            print "listdir result: {}".format(filename)
            if os.path.isfile(os.path.join(directive_files_dirpath,filename)):
                print "examining: {}".format(filename)
                
                directive_match = re.search(r"^(\d+)\_(.*)\.directive\.yml$", filename)
                if directive_match:
                    sort_order = int(directive_match.group(1))
                    directive_name = directive_match.group(2)
                    
                    print "sort_order: {}, directive_name: {}".format(sort_order, directive_name)
                    
                    _directive_sortorder_map[directive_name] = sort_order
                    
                    
                    print "adding directive filepath[{}]: {}".format(directive_name, os.path.join(directive_files_dirpath, filename))
                    _directive_filepath_map[directive_name] = \
                        os.path.join(directive_files_dirpath, filename)
                    
                    heapq.heappush(_directive_filename_map,
                                   (sort_order,
                                    directive_name,
                                    os.path.join(directive_files_dirpath, filename)))
                                   
                ansible_match = re.search(r"^(\d+)\_(.*)\.ansible\.yml$", filename)
                if ansible_match:
                    sort_order = int(ansible_match.group(1))
                    directive_name = ansible_match.group(2)
                    
                    print "sort_order: {}, directive_name: {}".format(sort_order, directive_name)
                    
                    _directive_sortorder_map[directive_name] = sort_order
                    
                    print "adding ansible filepath[{}]: {}".format(directive_name, os.path.join(directive_files_dirpath, filename))
                    _directive_filepath_map[directive_name] = \
                        os.path.join(directive_files_dirpath, filename)
                    
                    heapq.heappush(_directive_filename_map,
                                   (sort_order,
                                    directive_name,
                                    os.path.join(directive_files_dirpath, filename)))
                    
                    
    return _directive_filename_map

def directive_filename_map():
    _ensure_directive_filename_map()
    return _directive_filename_map()

def directive_sortorder_map():
    _ensure_directive_filename_map()
    return _directive_sortorder_map

def directive_index(directive_name):
    global _directive_sortorder_map
    _ensure_directive_filename_map()
    try:
        return directive_sortorder_map()[directive_name]
    except KeyError:
        pass

def directive_filepath(directive_name):
    global _directive_filepath_map
    print "directive_filepath entered (directive: {})".format(directive_name)
    _ensure_directive_filename_map()
    try:
        return directive_filename_map()[directive_name]
    except KeyError:
        pass
