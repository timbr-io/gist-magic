from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython import get_ipython

from pygithub3 import Github
from pygithub3.resources.gists import Gist
import os
import shlex
import re
from urllib2 import urlopen
from itertools import chain

from IPython.display import publish_display_data

def build_display_data(obj):
    output = {"text/plain": repr(obj)}
    methods = dir(obj)
    if "_repr_html_" in methods:
        output["text/html"] = obj._repr_html_()
    if "_repr_javascript_" in methods:
        output["application/javascript"] = obj._repr_javascript_()
    return output

class PrettyGist(object):
    def __init__(self, g):
        self.gist = g

    def __repr__(self):
        if "snippet.py" in self.gist.files:
            return self.gist.files["snippet.py"].content
        elif "preset.txt" in self.gist.files:
            return self.gist.files["preset.txt"].content
        else:
            fname = self.gist.files.keys()[0]
            print "%s: \n" % fname
            return self.gist.files[fname].content

    def _repr_html_(self):
        url = "https://gist.github.com/%s/%s.js" % (self.gist.owner["login"], self.gist.id)
        resp = urlopen(url)
        jsdata = resp.read()
        matches = [re.findall(r"document\.write\([\'\"](.+)[\'\"]\)", line, re.DOTALL) for line in jsdata.splitlines()]
        output = [re.sub(r"<\\/(\w+)>", r"</\1>", m.decode("string_escape")) for m in chain(*matches)]
        output.append("""
<style>
.rendered_html th, .rendered_html td, .rendered_html tr {
  border: 0px;
}
</style>
""")
        return "\n".join(output)

    # def _repr_javascript_(self):
    #     return 'console.log("<PrettyGist/>")'

# The class MUST call this class decorator at creation time
@magics_class
class GistMagics(Magics):
    def __init__(self, shell):
        super(GistMagics, self).__init__(shell)
        if os.environ.get("GITHUB_ACCESS_TOKEN") is not None:
            self._token = os.environ.get("GITHUB_ACCESS_TOKEN")
            self.gh = Github(token=self._token)
            self.preset_id = None

    @line_cell_magic
    def gist(self, line, cell=None):
        # TODO: lots of cleanup and error handling
        args = shlex.split(line)
        if cell is None:
            # run as a line magic
            assert len(args) > 0 # there better be a subcommand or gist id
            if args[0] == "list":
                if len(args) > 1:
                    self.list(args[1])
                else:
                    self.list("")
            elif args[0] == "token":
                self.token(args[1])
            elif args[0] == "list":
                self.list()
            elif args[0] == "delete":
                self.delete(args[1])
            elif args[0] == "preset":
                try:
                    self.preset(args[1])
                except IndexError, ie:
                    self.preset()
            else:
                # assume we have been passed a gist id
                self.show(args[0])
        else:
            # run as a cell magic
            if len(args) > 0:
                self.update(args[0], cell)
            else:
                self.create(cell)

    @line_cell_magic('gist_preset')
    def preset(self, line=None, cell=None):
        args = shlex.split(line)
        if cell is None:
            if len(args) == 0:
                # create an empty gist and output the id
                self.create("%%gist preset\n# gist ids\n", filename="preset.txt") # -> prints the id
            else:
                self.preset_id = args[0]
                pretty_gist = self.show(args[0])
        else:
            # execute as a cell magic
            for line in cell.splitlines():
                try:
                    self.show(line, display=False, evaluate=True)
                except:
                    print "Unable to load snippet with id: %s" % line

    @line_magic('gist_token')
    def token(self, line):
        self._token = line
        self.gh = Github(token=self._token)

    @line_magic('gist_list')
    def list(self, line=None):
        gists = self.gh.gists.list()
        for gist in gists.iterator():
            print "%s %s" % (gist.id, gist.html_url)

    @line_magic('gist_show')
    def show(self, line, display=True, evaluate=True):
        gist = self.gh.gists.get(line)
        pretty_gist = PrettyGist(gist)
        if display:
            publish_display_data(build_display_data(pretty_gist))
        if evaluate:
            get_ipython().run_cell(repr(pretty_gist)) # repr PrettyGist -> gist code
        if not display:
            return pretty_gist

    @cell_magic('gist_create')
    def create(self, cell, filename="snippet.py"):
        assert cell is not None
        config = dict(description='', public=False,
                      files={filename: {'content': cell}})
        gist = self.gh.gists.create(config)
        # TODO: check if we are on a preset and, if so, append this id to the it
        print("gist id: %s" % gist.id)

    @line_magic('gist_delete')
    def delete(self, line):
        try:
            self.gh.gists.delete(line)
            print("Deleted gist %s" % line)
            # TODO: also delete the gist id line from the preset if we're on one
        except Exception, e:
            print("Could not delete gist %s" % line)

    @line_cell_magic('gist_update')
    def update(self, line, cell=None):
        assert cell is not None
        config = dict(description='test gist', public=False,
                          files={'snippet.py': {'content': cell}})
        gist = self.gh.gists.update(line, config)
