_plan_name_stack = []
def plan_file_stack_push(plan_name):
    _plan_name_stack.append(plan_name)
    
def plan_file_stack_pop():
    _plan_name_stack.pop()
    
def plan_file_stack_as_str():
    return ">".join(_plan_name_stack)

