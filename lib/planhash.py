# a module for working with plan-hashes
#
# the idea behind planhashes is that, for any plans that do not need to be re-run once they have been completed, we
# can store hashes to indicate that the plan has been run and that future iterations can be skipped

import hashlib
import os
from .plan import plan_filepath
from .dirpaths import hashes_dirpath


_hash_filepaths = None


def plan_hash_filepath(plan_name):
    """returns a filepath for a planhash on the remote machine"""
    filepath = plan_filepath(plan_name)
    return os.path.join(hashes_dirpath(), "{}.{}".format(os.path.basename(filepath), _plan_hash_str(filepath)))


def plan_hash_filepath_exists(**kwargs):
    """checks to see if the plan hash filepath exists (i.e. if the plan in its current form has already been included in the playbook)"""
    global _hash_filepaths

    # read the hash filepaths from file if _hash_filepaths is None
    if _hash_filepaths is None:
        with open('/tmp/corrigible_hashes_list', 'rb') as fh:
            _hash_filepaths = fh.read().split('\n')

    # return true if the plan hash filepath exists in _hsh_filepaths
    return bool(os.path.basename(plan_hash_filepath(kwargs['plan'])) in _hash_filepaths)


def _plan_hash_str(fn):
    """returns a hash digest for a file, ideally a super-unique one"""
    # from: http://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
    afile = open(fn, 'rb')
    hasher = hashlib.sha256()
    blocksize = 65536
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    ret = hasher.hexdigest()
    afile.close()
    return ret


