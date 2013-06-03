#!/usr/bin/python

try:
    from setuptools import setup
except ImportError:
    from disutils.core import setup

package_name = 'mib2html'

setup(name=package_name,
      version='0.1',
      description='Pretty html generation from MIB definition',
      author='Gentaro Muramatsu',
      author_email='genta.hgr@gmail.com',
      license = 'MIT License',
      url ='TO BE DETERMINED',
      packages = [ package_name ],
      package_data = { '' : ['*.html', '*.css' ]},
      exclude_package_data = { '': 'todo.txt' },
      install_requires = [ 'jinja2 >= 2.6' ],
      entry_points = {
          "console_scripts" : [
              "mib2html_entry = mib2html:main"
              ]
          }
     )
