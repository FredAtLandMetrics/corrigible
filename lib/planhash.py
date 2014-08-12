import hashlib
import os
from corrigible.lib.plan import plan_filepath
from corrigible.lib.dirpaths import hashes_dirpath

# from: http://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
def _hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

def plan_hash_str(fn):
    return _hashfile(open(fn, 'rb'), hashlib.sha256())

def plan_hash_filepath(**kwargs):
    try:
        return os.path.join(hashes_dirpath(),"{}.{}".format(os.path.basename(kwargs['filepath']), plan_hash_str(kwargs['filepath'])))
    except KeyError:
        try:
            p_filepath = plan_filepath(kwargs['plan'])
            return os.path.join(hashes_dirpath(),"{}.{}".format(os.path.basename(p_filepath), plan_hash_str(p_filepath)))
        except KeyError:
            return None
        