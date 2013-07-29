=====================================
Developement environment for mib2html
=====================================

Directory structure
-------------------

::

  mib2html/
    setup.py : setuptools script
    todo.txt : development memo
    mib2html/
      \*.py : source codes
      \*.css, \*.html : templates

    dist/ : generated distribution package is stored here
    test/ : test script is to be created here
    venv/
      bin/activate : activate script for venv
 
    build/ : temporary directory for installation (automatically generated)
    mib2html.egg-info/ : temporary directory for package building (automatically generated)
    work/  : various sample files for testing

    .git/ : source code management directory

Typical commands
----------------

Beginning of the work
^^^^^^^^^^^^^^^^^^^^^^

Enable virtual environment.

  $ . venv/bin/activate

Note: activate is not executable because it shall be parsed in the current shell.

Regiter packages into python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  $ python setup.py install

Use following command for development use.

  $ python setup.py develop

The development installation creates a symbolic link to the working environment
instead of copying files into the package directory.


Create redistributable package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  $ python setup sdist

Note: bdist_egg generates platform-dependent egg binary.

list managed files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  $ git ls-files

convet this file into html
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  $ rst2html.py dev_environment.rst > dev_environment.html

