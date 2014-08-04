import pkgutil
import inspect

import corrigible

from corrigible.lib.exceptions import UnnamedTest

class BaseCorrigibleTest(object):
    
    @classmethod
    def claim(cls, test_dict):
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
    
    def str_to_tuple(self, s, **kwargs):
        
        try:
            assert(type(s) is str and bool(s))
        except AssertionError:
            return None
        
        try:
            tsep = kwargs['tuple_separator']
        except KeyError:
            tsep = ' '
            
        try:
            assert(tsep in s)
            data = tuple(s.split(tsep))
        except AssertionError:
            data = tuple(s)
            
        return data
    
    def str_to_dict(self, s, **kwargs):
        try:
            rsep = kwargs['record_separator']
        except KeyError:
            rsep = ' '
            
        try:
            ksep = kwargs['keyword_separator']
        except KeyError:
            ksep = '='
            
        try:
            assert(rsep in s)
            ret = {}
            for kvpair in self.str_to_tuple(s, tuple_separator=rsep):
                key, val = self.str_to_tuple(kvpair,tuple_separator=ksep)
                ret[key] = val
            return ret
        except AssertionError:
            try:
                assert(ksep in s)
                key, val = self.str_to_tuple(s,tuple_separator=ksep)
                return {key: val}
            except AssertionError:
                return None

_registered_tests = None
def update_registered_tests():
    global _registered_tests
    _registered_tests = []
    package = corrigible.lib.tests
    for loader, name, ispkg in pkgutil.iter_modules(path=package.__path__):
        handlers_module = loader.find_module(name).load_module(name)
        for tester_classname, tester_class in inspect.getmembers(handlers_module, inspect.isclass):
            if issubclass(tester_class, BaseCorrigibleTest):
                _registered_tests.append(tester_class)
                
def lookup_registered_tester(test_dict):
    global _registered_tests
    try:
        assert(_registered_tests is None)
        update_registered_tests()
    except AssertionError:
        pass
    
    for t in _registered_tests:
        try:
            assert(t.claim(test_dict))
            return t
        except AssertionError:
            pass
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
        except AssertionError:
            raise
    
def _indent_chars(lvl):
    ret = ""
    if lvl > 0:
        for x in range(0, lvl):
            ret += "  "
    return ret
        
    
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
    
    tester_class = lookup_registered_tester(test_dict)
    tester_obj = tester_class(test_dict)
    
    try:
        assert(tester_obj.run())
        result = "[OK]"
        failed = False
    except AssertionError:
        result = "[FAIL]"
        failed = True
    
    print "{}TEST: {}".format(indent_str, test_label, result)
    
    if failed:
        print tester_obj.fail_output()
    
def run_tests_list(tests_list):
    print "Running tests:\n"
    
    failed = False
    fail_output = []
    for test_dict in tests_list:
        try:
            assert(run_test_dict(test_dict))
        except AssertionError:
            failed = True