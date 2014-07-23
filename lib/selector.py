def run_selector_affirmative(selectors):
    try:
        assert(_run_selector_include_affirmative(selectors['include']))
        return True
    except (AssertionError, KeyError):
        try:
            assert(_run_selector_exclude_affirmative(selectors['exclude']))
            return False
        except (AssertionError, KeyError):
            return True

_run_selectors = None
def set_run_selectors_list(rslist):
    global _run_selectors
    _run_selectors = rslist

def get_run_selectors_list():
    global _run_selectors
    return _run_selectors

def _run_selector_include_affirmative(include_selectors):

    if (type(include_selectors) is not list):
        return _run_selector_exclude_affirmative([include_selectors])

    try:
        run_selectors = get_run_selectors_list()
        #print('_run_selector_include_affirmative - include_selectors: {}'.format(str(include_selectors)))
        #print('_run_selector_include_affirmative - run_selectors: {}'.format(str(run_selectors)))
        
        for sel in include_selectors:
            if sel == 'ALL':
                return True
            if sel in run_selectors:
                return True
        return False
    except TypeError:
        return False

def _run_selector_exclude_affirmative(exclude_selectors):
    
    if (type(exclude_selectors) is not list):
        return _run_selector_exclude_affirmative([exclude_selectors])
    
    try:
        run_selectors = get_run_selectors_list()
        #print('_run_selector_exclude_affirmative - exclude_selectors: {}'.format(str(exclude_selectors)))
        #print('_run_selector_exclude_affirmative - run_selectors: {}'.format(str(run_selectors)))
        for sel in exclude_selectors:
            if str(sel) == 'ALL':
                return True
            if str(sel) in run_selectors:
                return True
        return False
    except TypeError:
        return False


