# from jinja2 import nodes
# from jinja2.ext import Extension
# from jinja2.exceptions import TemplateSyntaxError
import subprocess
import jinja2
import jinjatag
ShellExtension = jinjatag.JinjaTag()
env = jinja2.Environment(autoescape=False, extensions=[ShellExtension])
ShellExtension.init()

@jinjatag.simple_tag
def shell(cmd, **kwargs):
    output = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE).communicate()[0].rstrip()
    return "'{}'".format(output)

# class ShellExtension(Extension):
#
#     tags = set(['shell'])
#
#     def parse(self, parser):
#
#         stream = parser.stream
#         tag = stream.next()  # this stores the 'shell' keyword
#
#         pieces = []
#         while not stream.current.test_any('block_end', 'name:as'):
#             pieces.append(stream.next())
#
#         cmd = ""
#         if bool(pieces):
#             cmd = "".join([b.value for b in pieces])
#
#         print "cmd: {}".format(cmd)
#
#         lineno = stream.current.lineno
#         # return nodes.CallBlock(
#         #     self.call_method(self, '_get_shell_output', cmd), [], [], []
#         # ).set_lineno(lineno)
#         #return nodes.Output([self.call_method('_get_shell_output', args=[nodes.Const(cmd)], kwargs={})]).set_lineno(lineno)
#         return nodes.Const("test")
#
#     @classmethod
#     def _get_shell_output(cls, cmd, *args, **kwargs):
#         print "cmd1: {}".format(cmd)
#         return 'doh'
