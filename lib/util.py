import copy

def merge_hash(args_base, args_adding):
    #print "_merge_args: base({}), adding({})".format(args_base, args_adding)
    ret = copy.copy(args_base)
    for k,y in args_adding.iteritems():
        ret[k] = y
    #print "_merge_args returning {}".format(ret)
    return ret
