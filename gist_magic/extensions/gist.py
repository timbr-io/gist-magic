from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython import get_ipython

import argparse

from pygithub3 import Github
from pygithub3.resources.gists import Gist
import os
import shlex
from itertools import chain

from IPython.display import publish_display_data
from .pretty import PrettyGist, PrettyGistList, build_display_data



# The class MUST call this class decorator at creation time
@magics_class
class GistMagics(Magics):
    def __init__(self, shell):
        super(GistMagics, self).__init__(shell)
        if os.environ.get("GITHUB_ACCESS_TOKEN") is not None:
            self._token = os.environ.get("GITHUB_ACCESS_TOKEN")
            self.gh = Github(token=self._token)
            self.preset_id = None

        self._parser = self.generate_parser()



    def generate_parser(self):
        parser = argparse.ArgumentParser(prog="gist")

        subparsers = parser.add_subparsers()
        token_parser = subparsers.add_parser("token", help="Register a Github token for authentication")
        token_parser.add_argument("github_token", help="Github access token")
        token_parser.set_defaults(fn=self.token)
        list_parser = subparsers.add_parser("list", help="List current user's gists (or recent public gists if token is not set)")
        list_parser.set_defaults(fn=self.list)
        delete_parser = subparsers.add_parser("delete", help="Delete gist specified by id")
        delete_parser.add_argument("delete_gist_id", help="ID of gist to delete")
        delete_parser.set_defaults(fn=self.delete)
        preset_parser = subparsers.add_parser("preset", help="Create or register a preset gist as active")
        preset_parser.add_argument("preset_gist_id", help="ID of gist preset to select", default=None)
        preset_parser.set_defaults(fn=self.preset)

        show_parser = subparsers.add_parser("show", help="Show (or update) a gist")
        show_parser.add_argument("gist_id", help="ID of gist to load/update", nargs="?")
        show_parser.add_argument("--no-display", action="store_false", dest="display")
        show_parser.add_argument("--no-eval", action="store_false", dest="evaluate")
        show_parser.add_argument("-f", "--file", help="Name of the gist file to create / update")
        show_parser.set_defaults(fn=self.show_or_update)

        return parser

    @line_cell_magic
    def gist(self, line, cell=None):
        try:
            input_args = shlex.split(line)
            if len(input_args) > 0 and input_args[0] not in ["token", "list", "delete", "preset"]:
                input_args.insert(0, "show")
            elif len(input_args) == 0:
                input_args.insert(0, "list")
            args, extra = self._parser.parse_known_args(input_args)
            args.fn(cell=cell, **vars(args))
        except SystemExit, se:
            pass

    def preset(self, preset_gist_id=None, cell=None, **kwargs):
        if cell is None:
            if preset_gist_id is None:
                # create an empty gist and output the id
                self.create("%%gist preset\n# gist ids\n", filename="preset.txt") # -> prints the id
            else:
                self.preset_id = preset_gist_id
                pretty_gist = self.show(preset_gist_id)
        else:
            # execute as a cell magic
            for line in cell.splitlines():
                try:
                    if not line.strip().startswith("#"):
                        self.show(line, display=False, evaluate=True)
                except:
                    print "Unable to load snippet with id: %s" % line

    def token(self, github_token, **kwargs):
        self._token = github_token
        self.gh = Github(token=self._token)

    def list(self, **kwargs):
        gists = self.gh.gists.list()
        gists_list = PrettyGistList(list(gists.iterator()))
        publish_display_data(build_display_data(gists_list))
        return gists_list

    def show_or_update(self, gist_id=None, cell=None, display=True,
                       evaluate=True, filename="snippet.py", **kwargs):
        if cell is not None:
            if gist_id is None:
                return self.create(cell, filename=filename)
            else:
                return self.update(gist_id, cell, filename=filename)
        else:
            return self.show(gist_id, display, evaluate)

    def show(self, gist_id, display=True, evaluate=True, **kwargs):
        gist = self.gh.gists.get(gist_id)
        pretty_gist = PrettyGist(gist)
        if display:
            publish_display_data(build_display_data(pretty_gist))
        if evaluate:
            get_ipython().run_cell(pretty_gist.content)
        if not display:
            return pretty_gist

    def create(self, cell, filename="snippet.py"):
        assert cell is not None
        config = dict(description='', public=False,
                      files={filename: {'content': cell}})
        gist = self.gh.gists.create(config)
        # TODO: check if we are on a preset and, if so, append this id to the it
        print("gist id: %s" % gist.id)

    def delete(self, gist_id):
        try:
            self.gh.gists.delete(gist_id)
            print("Deleted gist %s" % gist_id)
            # TODO: also delete the gist id line from the preset if we're on one
        except Exception, e:
            print("Could not delete gist %s" % line)

    def update(self, gist_id, cell, filename="snippet.py"):
        assert cell is not None
        config = dict(description='', public=False,
                          files={filename: {'content': cell}})
        gist = self.gh.gists.update(gist_id, config)
