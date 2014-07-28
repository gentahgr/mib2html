#!/usr/bin/python

try:
    from setuptools import setup
except ImportError:
    from disutils.core import setup

import sys

package_name = 'mib2html'

require_libraries = [ 'jinja2 >= 2.6' ]
if sys.version_info < (2, 7, 0):
    require_libraries.append( 'argparse >= 1.1' )

setup(name=package_name,
      version='0.3',
      description='Pretty html generation from MIB definition',
      author='Gentaro Muramatsu',
      author_email='genta.hgr@gmail.com',
      license = 'MIT License',
      url ='https://github.com/gentahgr/mib2html',
      packages = [ package_name ],
      package_data = { package_name : ['*.html', '*.css' ]},
      include_package_data=True,
      # exclude_package_data = { '': 'todo.txt' },
      install_requires = require_libraries,
      entry_points = {
          "console_scripts" : [
              "mib2html = mib2html:main"
              ]
          }
     )
