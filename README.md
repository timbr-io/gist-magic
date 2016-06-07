# gist-magic
IPython magic interface to Gists

```
%reload_ext gist_magic

%gist token <personal access token>

%gist list [--limit 5]

%gist <gist_id> [--evaluate --no-display]

%%gist [<id>] [-f README.md -d 'a happy description']
post this code

%gist preset -> allocate a preset -> id

%gist preset id -> activate that preset (evaluate all the gists in it)

%gist delete <id>
