# a simple plan stack to be used for troubleshooting unparseable plans

_plan_name_stack = []

def plan_file_stack_push(plan_name):
    """pushes a plan name onto the stack"""
    global _plan_name_stack
    _plan_name_stack.append(plan_name)
    
def plan_file_stack_pop():
    """pops a plan name off the stack"""
    global _plan_name_stack
    _plan_name_stack.pop()
    
def plan_file_stack_as_str():
    """returns a string representation of the plan name stack"""
    return ">".join(_plan_name_stack)

