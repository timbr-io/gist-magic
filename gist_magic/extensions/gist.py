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

from IPython.core.formatters import DisplayFormatter

def publish_to_display(obj):
    output, _ = DisplayFormatter().format(obj)
    publish_display_data(output)


# The class MUST call this class decorator at creation time
@magics_class
class GistMagics(Magics):
    def __init__(self, shell):
        super(GistMagics, self).__init__(shell)
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
        list_parser.add_argument("-l", "--limit", help="number of gist to list", default=-1)
        list_parser.set_defaults(fn=self.list)
        delete_parser = subparsers.add_parser("delete", help="Delete gist specified by id")
        delete_parser.add_argument("gist_id", help="ID of gist to delete")
        delete_parser.set_defaults(fn=self.delete)
        preset_parser = subparsers.add_parser("preset", help="Create or register a preset gist as active")
        preset_parser.add_argument("preset_gist_id", help="ID of gist preset to select", default=None, nargs="?")
        preset_parser.add_argument("--no-display", action="store_false", dest="display")
        preset_parser.set_defaults(fn=self.preset)
        insert_parser = subparsers.add_parser("insert", help="Insert snippet code into this cell")
        insert_parser.add_argument("gist_id", help="ID of gist to insert")
        insert_parser.add_argument("-f", "--filename", help="name of the gist file to insert", default="snippet.py")
        insert_parser.add_argument("-a", "--append", help="Insert a new cell rather than replacing the content of the current one",
                                   action="store_false", dest="replace")
        insert_parser.set_defaults(fn=self.insert)

        show_parser = subparsers.add_parser("show", help="Show (or update) a gist")
        show_parser.add_argument("gist_id", help="ID of gist to load/update", nargs="?")
        show_parser.add_argument("--no-display", action="store_false", dest="display")
        show_parser.add_argument("-e", "--evaluate", action="store_true")
        show_parser.add_argument("-f", "--filename", help="Name of the gist file to create / update")
        show_parser.add_argument("-d", "--description", help="a description for the gist", default="")
        show_parser.set_defaults(fn=self.show_or_update)

        return parser

    @line_cell_magic
    def gist(self, line, cell=None):
        try:
            input_args = shlex.split(line)
            if len(input_args) == 0 or input_args[0] not in ["token", "list", "delete", "preset", "insert"]:
                input_args.insert(0, "show")
            args, extra = self._parser.parse_known_args(input_args)
            return args.fn(cell=cell, **vars(args))
        except SystemExit, se:
            pass

    def preset(self, preset_gist_id=None, cell=None, display=True, **kwargs):
        if cell is None:
            if preset_gist_id is None:
                # create an empty gist and output the id
                self.create("%%gist preset\n# gist ids\n", filename="preset.txt") # -> prints the id
            else:
                self.preset_id = preset_gist_id
                pretty_gist = self.show(preset_gist_id, evaluate=True)
                if display == True:
                  return pretty_gist
                else:
                  return None
        else:
            # execute as a cell magic
            for line in cell.splitlines():
                try:
                    gist_id = line.split("#", 2)[0]
                    if len(gist_id) > 0:
                        self.show(gist_id, display=False, evaluate=True)
                except Exception as e:
                    print("Unable to load snippet with id: %s" % gist_id)
                    print(str(e))


    def token(self, github_token, **kwargs):
        self._token = github_token
        self.gh = Github(token=self._token)

    def list(self, limit=-1, **kwargs):
        try:
          assert self._token is not None
          gists = self.gh.gists.list()
          gists_list = PrettyGistList(list(gists.iterator())[:int(limit)])
          return gists_list
        except AssertionError:
          print("No token defined. Unable to list gists")
        

    def show_or_update(self, gist_id=None, cell=None, display=True,
                       evaluate=True, filename="snippet.py", description='', **kwargs):
        if cell is not None:
            if gist_id is None:
                return self.create(cell, filename=filename, description=description)
            else:
                return self.update(gist_id, cell, filename=filename)
        else:
            if gist_id is not None:
                return self.show(gist_id, display, evaluate)
            else:
                return self.list()

    def show(self, gist_id, display=True, evaluate=False, **kwargs):
        gist = self.gh.gists.get(gist_id)
        pretty_gist = PrettyGist(gist, display=display)
        if evaluate:
            get_ipython().run_cell(pretty_gist.content)
        return pretty_gist

    def insert(self, gist_id, filename="snippet.py", replace=True, **kwargs):
        gist = self.gh.gists.get(gist_id)
        if filename in gist.files:
            get_ipython().set_next_input(gist.files[filename].content, replace=replace)
        else:
            print("{} file not found in gist with id {}".format(filename, gist_id))

    def create(self, cell, filename="snippet.py", description=''):
        try:
            assert cell is not None
            assert self._token is not None
            config = dict(description=description, public=False, files={})
            config['files'][filename or 'snippet.py'] = {'content': cell}

            gist = self.gh.gists.create(config)
            self.add_to_preset(gist.id)
            print("gist id: %s" % gist.id)
            return gist.id
        except AssertionError:
          print("No token defined. Unable to create gists.") 

    def delete(self, gist_id, **kwargs):
        try:
            self.gh.gists.delete(gist_id)
            print("Deleted gist %s" % gist_id)
            self.remove_from_preset(gist_id)
        except Exception as e:
            print("Could not delete gist %s" % gist_id)

    def update(self, gist_id, cell, filename="snippet.py"):
        try:
            assert cell is not None
            assert self._token is not None
          
            gist = self.gh.gists.get(gist_id)
            config = { 
                "description": gist.description,
                "public": gist.public,
                "files": {}
            }
            config["files"][filename or 'snippet.py'] = {"content": cell}
          
            self.gh.gists.update(gist_id, config)
        except AssertionError:
          print("No token defined. Unable to update gists or add them to presets")

    def add_to_preset(self, gist_id):
        if self.preset_id is not None:
            preset_gist = self.gh.gists.get(self.preset_id)
            preset_content = preset_gist.files["preset.txt"].content + "\n{}".format(gist_id)
            self.update(preset_gist.id, preset_content, filename="preset.txt")

    def remove_from_preset(self, gist_id):
        if self.preset_id is not None:
            preset_gist = self.gh.gists.get(self.preset_id)
            preset_content = preset_gist.files["preset.txt"].content + "\n{}".format(gist_id)
            preset_lines = [line for line in preset_content.splitlines() if not line.startswith(gist_id)]
            new_preset_content = "\n".join(preset_lines)
            if new_preset_content != preset_content:
                self.update(preset_gist.id, new_preset_content, filename="preset.txt")
