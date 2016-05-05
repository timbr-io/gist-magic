from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from pygithub3 import Github
import os
import shlex

# The class MUST call this class decorator at creation time
@magics_class
class GistMagics(Magics):
    def __init__(self, shell):
        super(GistMagics, self).__init__(shell)
        if os.environ.get("GITHUB_ACCESS_TOKEN") is not None:
            self._token = os.environ.get("GITHUB_ACCESS_TOKEN")
            self.gh = Github(token=self._token)

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
            else:
                # assume we have been passed a gist id
                self.show(args[0])
        else:
            # run as a cell magic
            if len(args) > 0:
                self.update(args[0], cell)
            else:
                self.create(cell)

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
    def show(self, line):
        gist = self.gh.gists.get(line)
        if "snippet.py" in gist.files:
            print(gist.files["snippet.py"].content)
        else:
            fname = gist.files.keys()[0]
            print "%s: \n" % fname
            print(gist.files[fname].content)

    @cell_magic('gist_create')
    def create(self, cell):
        assert cell is not None
        config = dict(description='test gist', public=False,
                      files={'snippet.py': {'content': cell}})
        gist = self.gh.gists.create(config)
        print("gist id: %s" % gist.id)

    @line_magic('gist_delete')
    def delete(self, line):
        try:
            self.gh.gists.delete(line)
            print("Deleted gist %s" % line)
        except Exception, e:
            print("Could not delete gist %s" % line)

    @line_cell_magic('gist_update')
    def update(self, line, cell=None):
        assert cell is not None
        config = dict(description='test gist', public=False,
                          files={'snippet.py': {'content': cell}})
        gist = self.gh.gists.update(line, config)


def load_ipython_extension(ip):
    ip.register_magics(GistMagics)
