from corrigible.lib.exceptions import UnnamedTest

class BaseCorrigibleTest(object):
    
    @classmethod
    def claim(test_dict):
        return False
    
    def __init__(self, new_test_dict):
        self._test_dict = None
        self.test_dict(new_test_dict)
        self.fail_output("")
    
    def test_dict(self, new_test_dict=None):
        try:
            assert(type(new_test_dict) is dict and bool(new_test_dict))
            self._test_dict = new_test_dict
        except AssertionError:
            pass
        return self._test_dict
    
    def run(self):
        return False
    
    def fail_output(self, txt=None):
        try:
            assert(type(txt) is str)
            self._fail_output = txt
        except AssertionError:
            pass
        return self._fail_output
    
    def append_fail_output(self, txt):
        self._fail_output += str(txt)
        return self._fail_output
    
    def strToTuple(s, **kwargs):
        
        try:
            assert(type(s) is str and bool(s))
        except AssertionError:
            return None
        
        try:
            tsep = kwargs['tuple_separator']
        except KeyError
            tsep = ' '
            
        try:
            assert(tsep in s)
            data = tuple(s.split(tsep))
        except AssertionError:
            data = tuple(s)
            
        return data
    
    def strToDict(s, **kwargs):
        try:
            rsep = kwargs['record_separator']
        except KeyError
            rsep = ' '
            
        try:
            ksep = kwargs['keyword_separator']
        except KeyError
            ksep = '='
            
        try:
            assert(rsep in s)
            ret = {}
            for kvpair in strToTuple(s, tuple_separator=rsep):
                key, val = strToTuple(kvpair,tuple_separator=ksep)
                    ret[key] = val
            return ret
        except AssertionError:
            try:
                assert(ksep in s)
                key, val = strToTuple(s,tuple_separator=ksep)
                return {key: val}
            except AssertionError:
                return None
            
def run_tests(opts):
    system_config_dict = None
    try:
        system_config_dict = system_config(opts)
        
        try:
            tests_list = system_config_dict['tests']
            run_tests_list(tests_list)
        except KeyError:
            print "INFO: No tests defined, skipping run_tests routine."
        
    except TypeError:
        try:
            assert(system_config_dict is None)
            print "ERR: No system config, not writing ansible playbook file"
            return
        except AssertionError
            raise
    
def _indent_chars(lvl):
    ret = ""
    if lvl > 0:
        for x in range(0, lvl):
            ret += "  "
    return ret
    
def lkpTesterObject(test_dict):
    
    
def run_test_dict(test_dict, **kwargs):
    try:
        test_label = test_dict['name']
    except KeyError:
        raise UnnamedTest()
    
    try:
        indent_level = kwargs['indent']
    except KeyError:
        indent_level = 0
        
    indent_str = _indent_chars(indent_level)
    
    tester_obj = lkpTesterObject(test_dict)
    
    print "{}TEST: {}".format(indent_str, test_label)
    
def run_tests_list(tests_list):
    print "Running tests:\n"
    
    for test_dict in tests_list:
        run_test_dict(test_dict)