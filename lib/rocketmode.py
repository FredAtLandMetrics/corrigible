_rocket_mode = False

def rocket_mode(*args):
    global _rocket_mode
    if type(args) is tuple and len(args) > 0:
        _rocket_mode = args[0]
    print("DBG: rocket_mode returning: {}".format(_rocket_mode))
    return _rocket_mode