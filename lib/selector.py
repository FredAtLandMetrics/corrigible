# run selectors
#
#   a simple way to call a system file and selectively include or exclude code.
#
#   NOTE: this feature can probably be removed in a future version in favor of using different system files
#         to do different things, which is how usage has tended to go anyway.
#
def run_selector_affirmative(selectors):
    """return whether to include a plan based on run selector information. default to True if no run selector applies."""

    # gather include and exclude selectors
    include_selectors = selectors['include'] if 'include' in selectors and bool(selectors['include']) else []
    exclude_selectors = selectors['exclude'] if 'exclude' in selectors and bool(selectors['exclude']) else []

    # if no run selectors, only return false for exclude selector lists with ALL
    run_selectors_list = get_run_selectors_list()
    if run_selectors_list is None:
        return False if 'ALL' in exclude_selectors else True

    # if ALL in exclude selectors return True only if there is an intersection between include selectors
    #  and run selectors
    if 'ALL' in exclude_selectors:
        return bool(list(set(include_selectors) & set(run_selectors_list)))

    # if ALL in include selectors return False only if there is an intersection between exclude selectors
    #  and run selectors
    if 'ALL' in include_selectors:
        return not bool(list(set(exclude_selectors) & set(run_selectors_list)))

    # return False if intersection between exclude selectors and run selectors
    if bool(list(set(exclude_selectors) & set(run_selectors_list))):
        return False

    # return False if include selectors is not empty and there is no intersection between include and
    # run_selectors
    if bool(include_selectors):
        return bool(list(set(include_selectors) & set(run_selectors_list)))

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

