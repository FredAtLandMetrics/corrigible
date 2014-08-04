from corrigible.lib.test import BaseCorrigibleTest

class ProcessTest(BaseCorrigibleTest):
    
    @classmethod
    def claim(cls, test_dict):
        return ('process' in test_dict)
    
    def run(self):
        
        try:
            testrec = strToDict(self.test_dict()['process'])
        except KeyError:
            self.fail_output("ERR: test_dict does not contain key: _process_")
            return False
        except Exception as e:
            self.fail_output("ERR: unable to convert str to dict({})".format(str(self.test_dict()['process'])))
            return False
        
        return False