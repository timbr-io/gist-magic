from urllib2 import urlopen
import re
from itertools import chain

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
