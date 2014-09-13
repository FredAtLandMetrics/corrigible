def run_selector_affirmative(selectors):
    ret = False
    try:
        assert(bool(_run_selector_include_affirmative(selectors['include'])))
        ret = True   # true if specifically included
    except (AssertionError, KeyError):
        try:
            assert(bool(_run_selector_exclude_affirmative(selectors['exclude'])))
            ret = False  # false if specifically excluded
        except (AssertionError, KeyError):
            ret = True   # default true

    print "run_selector_affirmative returning: {}".format(ret)
    return ret

_run_selectors = None
def set_run_selectors_list(rslist):
    global _run_selectors
    _run_selectors = rslist

def get_run_selectors_list():
    global _run_selectors
    return _run_selectors

def _run_selector_include_affirmative(include_selectors):

    if (type(include_selectors) is not list):
        return _run_selector_include_affirmative([include_selectors])

    ret = False
    try:
        run_selectors = get_run_selectors_list()
        print('_run_selector_include_affirmative - include_selectors: {}'.format(str(include_selectors)))
        # print('_run_selector_include_affirmative - exclude_selectors: {}'.format(str(exclude_selectors)))
        print('_run_selector_include_affirmative - run_selectors: {}'.format(str(run_selectors)))

        for sel in include_selectors:
            if sel == 'ALL':
                ret = True
            if sel in run_selectors:
                ret = True

    except TypeError:
        pass
    print "_run_selector_include_affirmative returning: {}".format(ret)
    return ret

def _run_selector_exclude_affirmative(exclude_selectors):
    
    if (type(exclude_selectors) is not list):
        return _run_selector_exclude_affirmative([exclude_selectors])

    ret = False
    try:
        run_selectors = get_run_selectors_list()
        print('_run_selector_exclude_affirmative - exclude_selectors: {}'.format(str(exclude_selectors)))
        print('_run_selector_exclude_affirmative - run_selectors: {}'.format(str(run_selectors)))
        for sel in exclude_selectors:
            if str(sel) == 'ALL':
                ret = True
            if str(sel) in run_selectors:
                ret = True
    except TypeError:
        pass
    print "_run_selector_exclude_affirmative returning: {}".format(ret)
    return ret


