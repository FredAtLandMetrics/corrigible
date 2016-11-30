import os
import subprocess
import jinja2
import jinjatag
ShellExtension = jinjatag.JinjaTag()
env = jinja2.Environment(autoescape=False, extensions=[ShellExtension])
ShellExtension.init()

@jinjatag.simple_tag
def shell(cmd, chdir=".", **kwargs):

    original_dirpath = os.getcwd()
    new_dirpath = os.environ["CORRIGIBLE_PATH"]
    if chdir != ".":
        if chdir[0] == "/":
            new_dirpath = chdir
        else:
            new_dirpath = os.path.join(new_dirpath, chdir)
    os.chdir(new_dirpath)

    output = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE).communicate()[0].rstrip()

    os.chdir(original_dirpath)

    return "'{}'".format(output)

