from setuptools import setup

setup(name='gist-magic',
      version='0.2.1',
      description='IPython magics to work with gists',
      url='https://github.com/pramukta/gist-magic',
      author='Pramukta Kumar',
      author_email='pramukta.kumar@timbr.io',
      license='MIT',
      packages=['gist_magic', 'gist_magic.extensions'],
      zip_safe=False,
      # entry_points = {
      #   'console_scripts': [
      #       ]
      #   },
      install_requires=[
          "ipython",
          "pygithub3",
          "markdown",
          "py-gfm"
        ]
      )
