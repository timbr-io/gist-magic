from urllib2 import urlopen
import re
from itertools import chain

import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension
_md = markdown.Markdown(extensions=[GithubFlavoredMarkdownExtension()])

def build_display_data(obj):
    output = {"text/plain": repr(obj)}
    methods = dir(obj)
    if "_repr_html_" in methods:
        output["text/html"] = obj._repr_html_()
    if "_repr_javascript_" in methods:
        output["application/javascript"] = obj._repr_javascript_()
    return output


class PrettyGist(object):
    def __init__(self, g, compact=False, display=True):
        self.gist = g
        self.compact = compact
        self.display = display

    @property
    def content(self):
        if "preset.txt" in self.gist.files:
            return self.gist.files["preset.txt"].content
        elif "snippet.py" in self.gist.files:
            return self.gist.files["snippet.py"].content
        else:
            fname = self.gist.files.keys()[0]
            return self.gist.files[fname].content

    def __repr__(self):
        header_params = {
            "preset": "PRESET" if "preset.txt" in self.gist.files else "GIST",
            "p_flag": "P" if "preset.txt" in self.gist.files else "",
            "r_flag": "R" if "README.md" in self.gist.files else "",
            "s_flag": "S" if "snippet.py" in self.gist.files else "",
            "gist_id": self.gist.id,
            "url": self.gist.html_url,
            "description": self.gist.description
        }

        if header_params["description"] == "":
            header_params["description"] = "No description provided"

        output = "{preset:<7} {p_flag:<2}{r_flag:<2}{s_flag:<2}{gist_id} [{description:60}]\n{url}".format(**header_params)

        if not self.compact:
            output += "\n\n"
            if "snippet.py" in self.gist.files:
                output += self.gist.files["snippet.py"].content
            elif "preset.txt" in self.gist.files:
                output += self.gist.files["preset.txt"].content
            else:
                fname = self.gist.files.keys()[0]
                output += "{}: \n".format(fname)
                output += self.gist.files[fname].content

        return output

    def _repr_html_(self):
        if self.display:
            try:
              owner = self.gist.owner["login"]
            except AttributeError:
              owner = 'anonymous'

            url = "https://gist.github.com/%s/%s.js" % (owner, self.gist.id)
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
        else:
            return ""

    # def _repr_javascript_(self):
    #     return 'console.log("<PrettyGist/>")'

class PrettyGistList(object):
    def __init__(self, gists):
        self.gists = gists

    def __repr__(self):
        return "\n".join([repr(PrettyGist(gist, compact=True)) for gist in self.gists])
