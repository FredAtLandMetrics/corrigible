from corrigible.lib.tests import BaseCorrigibleTest

class FileTest(BaseCorrigibleTest):
    
    @classmethod
    def claim(test_dict):
        return ('file' in test_dict)
    
    def run(self):
        
        try:
            testrec = strToDict(self.test_dict()['file'])
        except KeyError:
            self.fail_output("ERR: test_dict does not contain key: _file_")
            return False
        except Exception as e:
            self.fail_output("ERR: unable to convert str to dict({})".format(str(self.test_dict()['file'])))
            return False
        
        try:
            assert('path' in testrec)
        except AssertionError:
            self.fail_output("ERR: path is a required parameter of the _file_ test")
            return False
        
        try:
            assert(testrec['status'] in testrec)
            if testrec['status'] in ['present','exists']:
                try:
                    assert(os.path.isfile(testrec['path']))
                except AssertionError:
                    self.fail_output("ERR: file does not exist")
                    return False
            elif testrec['status'] in ['absent']:
                try:
                    assert(os.path.isfile(testrec['path']))
                    self.fail_output("ERR: file exists")
                    return False
                except AssertionError:
                    pass
            else:
                self.fail_output("ERR: file exists")
        except AssertionError:
            pass
            
        return True