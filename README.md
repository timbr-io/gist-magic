# gist-magic
IPython magic interface to Gists

```
%reload_ext gist_magic
%gist token <personal access token>
%gist list

%gist <gist_id> [--evaluate --no-display]
%%gist [<id>] -f README.md
post this code

%gist preset -> allocate a preset -> id

%gist preset id -> activate that preset (evaluate all the gists in it)

%gist delete <id>
