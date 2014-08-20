# mib2html

Document generator from MIB file

## Introduction

MIB is an SNMP interface definition file.
It is written in SMIv2 syntax.

Althoug the MIB format can describe full information
for SNMP interface as well as human readable description,
it is not easy to grasp the whole structure of the MIB definition.

Each MIB object is identified by oid (Object identifier),
which ensure uniqueness of the oid by its hierarchal structure,
identifying the full oid for each object needs following
reference chain because each id for object is defined
by parent-child relashonship.

This tool convert a MIB definition file into an HTML file.
It starts with a tree structure table with quick description,
and detailed description for each object follows the table
with full oid.

## Requirements

This tool relies on the following tools.

* [Python 2.x](http://www.python.org) (2.7 or later)
* [jinja2](http://jinja.pocoo.org/)
* smidump, which is a part of [libsmi](http://www.ibr.cs.tu-bs.de/projects/libsmi/) library

"jinja2" can be installed by assistance of python package sysem such as  `easy_install` or `pip`.

For MacOS X, libsmi can be installed as "libsmi" package of [Homebrew](http://brew.sh/).

For MS Windows, a compiled binary is found here. [download/WIN32](https://www.ibr.cs.tu-bs.de/projects/libsmi/download/WIN32/)

## How to use

```
$ mib2html [options] MIB-FILE-NAME > output.html
```

mib2html accepts MIB file (SMIv2 format) and XML format convetered by smidump.
When MIB file is given, mib2html use `smidump` to parse it.

Generated HTML file is printed in its standard output. It can be redirected to a file or anther program.

### options

* `-k` continue to generate output even if given MIB contain errors
* `-r` use first node as base oid instead of identification oid.
* `-s level_offset` adjust oid abbreviation level

### environment variable

`mib2xml` specify conversion software from MIB to XML.
When `mib2xml` is defined, mib2html calls it with `-f xml` option.
`smidump` in `PATH` is used by default when this variable is not defined.

```
bash$ export mib2xml=/path/to/smidump
```
