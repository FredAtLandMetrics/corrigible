# run selectors
#
#   a simple way to call a system file and selectively include or exclude code.
#
#   NOTE: this feature can probably be removed in a future version in favor of using different system files
#         to do different things, which is how usage has tended to go anyway.
#
def run_selector_affirmative(selectors):
    """return whether to include a plan based on run selector information. default to True if no run selector applies."""

    # includes
    if 'include' in selectors and bool(selectors['include']):
        if _run_selector_include_affirmative(selectors['include']):
            return True

    # excludes
    if 'exclude' in selectors and bool(selectors['exclude']):
        if _run_selector_exclude_affirmative(selectors['exclude']):
            return False

    # default to True
    return True


_run_selectors = None
def set_run_selectors_list(rslist):
    """sets the run selectors list for the process"""
    global _run_selectors
    _run_selectors = rslist


def get_run_selectors_list():
    """returns the run selectors list"""
    global _run_selectors
    return _run_selectors


def _run_selector_include_affirmative(include_selectors):
    """given an include list of selectors from a run selector record,
          if one of the selectors is ALL, return True
          if instead, any one of the selectors is in the run selectors list for this process, return True
          otherwise return False
    """
    # handle non-list include_selectors param
    if (type(include_selectors) is not list):
        return _run_selector_exclude_affirmative([include_selectors])

    # if one of the selectors is ALL, return True
    if "ALL" in include_selectors:
        return True

    # default to false if run_selectors_list is None
    run_selectors_list = get_run_selectors_list()
    if run_selectors_list is None:
        return False

    # return true if the intersection of the two lists contains any members
    return bool(list(set(include_selectors) & set(run_selectors_list)))

def _run_selector_exclude_affirmative(exclude_selectors):
    """given an exclude list of selectors from a run selector record,
        if one of the selectors is ALL, return True
        if instead, any one of the selectors is in the run selectors list for this process, return True
        otherwise return False
    """

    # handle non-list exclude_selectors list
    if (type(exclude_selectors) is not list):
        return _run_selector_exclude_affirmative([exclude_selectors])

    # if one of the selectors is ALL, return True
    if "ALL" in exclude_selectors:
        return True

    # default to false if run_selectors_list is None
    run_selectors_list = get_run_selectors_list()
    if run_selectors_list is None:
        return False

    # return true if the intersection of the two lists contains any members
    return bool(list(set(exclude_selectors) & set(run_selectors_list)))


