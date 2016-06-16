# gist-magic
An Jupyter magic interface for working sharing code as Gists
---

gist-magic adds "magic" functions to a Jupyter Notebook that allow users to save code cells as Gists, group cells together, and quickly execute python from saved gists. 

## Installation 

```bash
pip install gist-magic
```

## Usage

The magics are designed to be used inside a Jupyter Notebook, and each of the examples below assume they're being run within a notebook environment.

### Loading the extension

```
%reload_ext gist_magic
```

### Setting access tokens

Gist-magic uses your github account's Personal Access Token in order to save gists to your account. Before you can save any code, you'll need to register a token.

```
%gist token <personal access token>
```

### Listing your Gists 

```
%gist list [--limit N]
```

### Insert a Gist 

```
%gist <gist_id> [--evaluate --no-display]
```


### Save a cell as a gist 

```
%%gist [<id>] [-f snippet.py -d 'a happy description']
```

### Delete a gist

```
%gist delete <id>
```

## Presets

A preset is a special way to group gists together so that many gists can be pulled into a notebook and evaulated at once. Once a preset has been registered in a notebook, all saved gists will be attached to that preset unless the gist is given a name other than "snippet.py". 

### Allocating a Preset 

Creates a new preset and prints its ID to the cell output.

```
%gist preset
```

### Activate a preset

In order for a preset to be used you must activate the preset id. 

```
%gist preset id -> activate that preset (evaluate all the gists in it)
```

