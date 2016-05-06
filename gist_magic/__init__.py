from .extensions.gist import GistMagics

def load_ipython_extension(ip):
    ip.register_magics(GistMagics)
