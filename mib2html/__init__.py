#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2013, Gentaro Muramatsu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
"""
convert MIB to HTML
===================

Architecture
------------
MIB definition file ==(smidump)==> Input formatXML ==(*this tool*)==> HTML

Output format can be configured by changing template file.
i.e. template engine is used for the last stage.
tenjin and jinja2 are candidates.



XML format
----------
http://www.ibr.cs.tu-bs.de/projects/nmrg/smi.xsd

Software Design
---------------

1. Read xml with xml.etree module
2. scan the data and build index
   - root node 
   - name - oid mapping and vise versa
   - shortened name

3. pass the XML tree and the index to a template engine

mib structure
-------------
(module)
    (identity) <- root node name
(imports)*
(typedefs)*
(nodes)*
    node
    { name, oid, status }
    scalar
        access
        description

(notifications)*
(groups)*
(compliances)*
"""

from xml.etree import ElementTree as et
import jinja2
from jinja2.utils import Markup
from itertools import count, izip
import re
import sys

# Common exception

class InvalidMibError(RuntimeError):
    pass


# functions

def read_mib_xml(filename):
    """Read XML generated by smidump and return XML DOM tree
    return ElementTree:

    exceptions:
        IOError
    """
    return et.parse(filename)

def oid_str2tuple(oid_str):
    """convert oid (dot-separated number sequence) to tuple
    input:
        oid (BaseString)
    return:
        oid (tuple)
    exceptions:
        ValueError (non-numeric character is in oid_str)
    """
    return tuple( int(n) for n in oid_str.split(".") )

def oidlen(oid_str):
    return oid_str.count(".") + 1

# preprocess functions for mib xml

def build_index(dom):
    """parse index table for all elements having oid attribute

    1. build cross reference for oid and node name

    input:
        dom: ElementTree
    return:
        dict
            mib_name: (oid,Element)
            oid: (mib_name,Element)
    """
    result = {}
    for node in dom.iterfind(".//*[@oid]"):
        oid = node.get("oid")
        name = node.get("name")
        # result[oid] = (name,node)
        result[name] = (oid,node)

    # add Textual Convention name with dummy oid
    for node in dom.iterfind("typedefs/typedef"):
        name = node.get("name")
        result[name] = (u"0",node)

    for node in dom.iterfind(u"imports/import"):
        # exclude standard SMIv2 imports
        if node.get(u"module") not in [u"SNMPv2-SMI", u"SNMPv2-TC"]:
            name = node.get(u"name")
            result[name] = (u"0",node)

    return result

def build_mib_node_array(dom):
    """Build sorted array of oid nodes 
    input:
        dom: ElementTree
    result:
        array of (oid(tuple), node) sorted by oid
    """
    mib_array = []
    for node in dom.iterfind(".//*[@oid]"):
        oid = node.get("oid")
        tag = node.tag

        if tag not in ["row", "column"]:
            # exclude table content
            mib_array.append( (oid_str2tuple(oid), node) )

    mib_array.sort(cmp= lambda x,y: cmp( x[0], y[0] ))
    return mib_array


def build_tree_index(dom,root):
    """build index for tree drawing
    input:
        dom: (ElementTree)
        root: root oid to calculate base level (string)
    result:
        (rootlevel,treeindex) : (integer, dict)
        treeindex: (tuple) -> (integer)
    """
    rootlevel = oidlen(root) - 1
    ttree = {}
    for node in dom.iterfind(".//*[@oid]"):
        oid = node.get("oid")
        toid = oid_str2tuple(oid)
        curlevel = len( toid )
        for lvl in xrange(rootlevel, curlevel):
            key = toid[rootlevel-1:lvl] 
            if ttree.has_key(key):
                ttree[key] = max( ttree[key], toid[lvl] )
            else:
                ttree[key] = toid[lvl]
            # print "{}.{} [{}:{}]/ {} = {}".format( toid, curlevel, rootlevel - 1, lvl, toid[rootlevel-1:lvl], toid[lvl])
    return (rootlevel, ttree)


def find_identity(dom,index):
    """find identity name
    return identity name

    input:
        dom: mib (ElementTree)
        index: mib index generated by build_index (dict)
    exceptions:
        InvalidMibError

    module/identity[@node] : name of root node
    """
    identity = dom.find("./module/identity[@node]")
    if identity is None:
        raise InvalidMibError("identity")

    identityName = identity.get("node")
    if identityName not in index:
        raise InvalidMibError("identity[@node]")

    return identityName

# prepare template

'''
filters/functions can use same context as template by decorating with contextfilter/contextfunction
'''

def prepare_context(mib, opts):
    """Build context dict for rendering

        mib : XML data read from MIB
        opts: commandline options (Namespace object generated by argparse)
    """

    # build various indicies from mib(xml ElementTree)
    mib_index = build_index(mib)
    mib_array = build_mib_node_array(mib)

    identity_name = find_identity(mib, mib_index)
    identity_oid  = mib_index[identity_name][0]

    root_oid  = ".".join( [str(i) for i in mib_array[0][0] ]) if opts.fromTop else identity_oid
    root_oidlist = root_oid.split(u".")
    
    # adjust root level
    if opts.rootShiftLevel > 0:
        root_oidlist = root_oidlist[:-opts.rootShiftLevel]

    root_oid = u".".join(root_oidlist)
    root_oid_prefix = u".".join(root_oidlist[:-1]) + u"."

    oid_prefix_level, ttree = build_tree_index(mib, root_oid)


    return {
            u"mib": mib,             # ElementTree
            u"root": root_oid,       # string
            u"identity": identity_oid,       # string
            u"identity_name": identity_name, # string
            u"index": mib_index,     # string -> (string{oid}, Element{node} )
            u"tree_index": ttree,
            u"oid_prefix_level": oid_prefix_level,
            u"mib_array": mib_array,
            u"root_oid_prefix": root_oid_prefix,
            u"root_oid_prefix_len": len(root_oid_prefix),
            }

def build_argparser():
    """build parser for commandline argument.

       This function use 'argparse' standard module introduced from python v2.7
    """
    import argparse

    def _positiveInt(s):
        """Accept positive interger values only"""

        v = int(s)
        if v < 0:
            raise argparse.ArgumentTypeError( "{} is not a positive integer.".format(s))
        return v

    parser = argparse.ArgumentParser(description='Generate HTML document from MIB(SMIv2) definition')

    parser.add_argument('mibxml', help='MIB file or XML file(converted by smidump)')
    parser.add_argument('-k', dest="forceMibParse", help='continue conversion forcely even when MIB error is detected (smidump option)', action='store_true')
    parser.add_argument('-r', dest="fromTop", help='set top oid as oid abbreviation root. Default root is identity oid', action='store_true' );
    parser.add_argument('-D', dest="templateException", help='change behavior for undefined object in templates (For template debugging only)', choices=['normal', 'debug', 'strict' ])
    parser.add_argument('-s', metavar="root_level_offset", dest="rootShiftLevel", help='offset of root oid level (default: 0)', type=_positiveInt, default=0 );
    return parser

def prepare_filters():
    return {
            u"format_syntax":   fl_format_syntax,
            u"calc_indent":     fl_calc_oid_indent,
            u"short_oid":       fl_short_oid,
            u"format_desc":     fl_format_description,
            u"linkage_suffix":  fl_linkage_suffix,
            u"parse_typedef":   fl_parse_typedef,
            u"parse_scalar":    fl_parse_scalar,
            u"parse_table":     fl_parse_table,
            u"parse_table_toc": fl_parse_table_toc,
            u"parse_row":       fl_parse_row,
            u"l":               fl_hyperlink,
            }
            

# jinja filter functions

def fl_format_syntax(node):
    """create string expression of syntax (mib data type)
    input:
        node: an Element which as "syntax" child element
    return:
        string
    """
    syntag = node.find("syntax")
    if syntag is None:
        # ignore gracefully
        return ''

    typetag = syntag[0]
    if typetag.tag == "type":
        # type
        mod_name = typetag.get("module")
        name = typetag.get("name")
        return name
    elif typetag.tag == "typedef":
        types = fl_parse_typedef(typetag)
        return types[0][1]
    else:
        raise InvalidMibError("syntax for {} has no type or typedef node".format(node.get("name")))

def fl_parse_typedef(typetag):
    '''Parse "typedef" node
    input:
        typetag : an Element of "typedef" node
    return:
        list of tuple
        [ (param1, value1), (param2, value2),...]
        most significant elemnt shall be the fist element of the list.
        The value of the first element is shown for short-form.
    exception:
        TypeError: if XML element type is not "typedef"
    '''

    # check node type (assertion)
    if typetag.tag != "typedef":
        raise TypeError("The specified node is not typedef Element. type: {}".format( typetag.tag ))

    result=[]

    basetype = typetag.get(u"basetype")
    if basetype == u"Enumeration":
        result.append( (u"Enumeration", u"/ ".join(
            [ u"{}({})".format( num.get("name"), num.get("number")) for num in typetag.iterfind("namednumber") ]
            )))

    elif basetype == "Bits":
        result.append( ("Bits", u"| ".join( reversed(
            [ u"{}({})".format( num.get("name"), num.get("number")) for num in typetag.iterfind("namednumber") ]
            ))))
    else:
        parent = typetag.find("parent")
        ranges = typetag.findall("range")
        if ranges:
            # VALUE_TYPE(a..b, c..d)
            range_str = []
    
            # value type part
            range_str.append( basetype if parent is None else parent.get("name") )
    
            # value range part
            range_str.append( u" (" )
            range_str.append( u", ".join(
                [ "{} .. {}".format(r.get("min"),r.get("max")) for r in ranges ]
            ))
            range_str.append( u")" )
            result.append( (u"Type(Range)", u"".join(range_str)) )
        else:
            # Type field is provided for regular types only
            # No type field added for Enumeration or Bits because they are redundant
            # No type field added for ranged values because data type is already indicated with ranges
            result.append( (u"Type", basetype if parent is None else parent.get("name") ))

    # status of the type
    result.append( (u"status", typetag.get(u"status", u"current")))

    # other information
    for fields in [u"default", u"format", u"units", u"description", u"reference" ]:
        value = typetag.findtext(fields)
        if value is not None:
            result.append( (fields, value) )

    return result

_access_cnv_table = [
        {
        "noaccess": "not-accessible",
        "notifyonly": "accessible-for-notify",
        "readonly": "read-only",
        "readwrite": "read-write"
        },
        {
        "noaccess": "not-accessible",
        "notifyonly": "accessible-for-notify",
        "readonly": "read-only",
        "readwrite": "read-create"
        }
]

def _convert_access(access, t=0):
    """Convert access attribute in libsmi to stnadard SMIv2 style

        access: access (in libsmi name)
        t: conversion type
            0: SMIv2 scalar/fixed row table
            1: SMIv2 tablec(row creation)
    """
    return _access_cnv_table[t][access]


def fl_parse_scalar(node,rowcreate=False):
    """parse for scalar
    input:
        node: (Element)
    return:
        list of tuple
        [ (param1, value1), (param2, value2),...]
        most significant elemnt shall be the fist element of the list.
    exception:
        TypeError: if XML element type is not "typedef"
        InvalidMibError : if scalar node has no syntax
    """

    # check node type (assertion)
    """
    # skip type check because this routine is applicable for "column" of table
    if node.tag != "scalar":
        raise TypeError(u"The specified node is not scalar Element. type: {}".format( node.tag ))
    """

    result=[]

    result.append( (u"oid", node.get(u"oid")))
    syntax_node = node.find(u"syntax/*")
    if syntax_node is not None:
        if syntax_node.tag == u"type":
            result.append( ( u"type", syntax_node.get(u"name")) )
        elif syntax_node.tag == u"typedef":
            # append fields of typedef to scalar except for status field
            result += [ pair for pair in fl_parse_typedef(syntax_node) if pair[0] != u"status" ]
        else:
            raise InvalidMibError( u"Invalid syntax tag for scalar node: {}".format(node.get(u"name") ))
    else:
        raise InvalidMibError( u"No syntax tag for scalar node: {}".format(node.get(u"name") ))

    # add attributes
    result.append( (u"status", node.get(u"status", u"current")))

    # add max-access
    value = node.findtext(u"access")
    c_flag = 0 if rowcreate is None else 1
    if value is not None:
        result.append( (u"max-access", _convert_access( value, c_flag )) )

    # other information
    for fields in [ u"default", u"format", u"units", u"description", u"reference" ]:
        value = node.findtext(fields)
        if value is not None:
            result.append( (fields, value) )

    return result

def fl_parse_table(node):
    """parse table #1 : description part

    Two individual parsers are provided for table type
    #1. parser for field of table element
    #2. builder for column and index info

    input:
        node: (Table Element)
    return:
        [(field,value),(field,value)]

    """

    result = [
        (u"oid", node.get(u"oid")),
        (u"status", node.get(u"status", u"current"))
        ]

    # other information
    for fields in [ u"description", u"referene" ]:
        value = node.findtext(fields)
        if value is not None:
            result.append( (fields, value) )

    return result

def fl_parse_table_toc(node):
    """parse table #2 : column list part
    input:
        node: (Table Element)
    return:
        tuple of list: (last_oid, index_number, column_name )
    """
    if node.tag != u"table":
        raise TypeError(u"The specified node is not a table Element. type: {}".format( node.tag ))

    # build index dict
    index_dict = {}
    for index_node, i in izip( node.iterfind(u"row/linkage/index"), count(1)):
        index_dict[index_node.get(u"name")] = i

    # print >>sys.stderr, "Node: {}".format( node.get("name"))
    # print >>sys.stderr, index_dict

    columns = []
    # build column list
    for cl in node.iterfind(u"row/column"):
        c_oid = cl.get(u"oid")
        c_oid_n = c_oid[ c_oid.rindex(u".")+1:]

        c_name = cl.get(u"name")
        c_index = index_dict.get(c_name, 0)

        columns.append( (c_oid_n, c_index, c_name) )

    return columns

def fl_parse_row(node):
    """parse for row

    because main index is shown in table node,
    no special drawing is not provided for row element.

    input:
        node: (Element)
    return:
        list of tuple
        [ (param1, value1), (param2, value2),...]
        most significant elemnt shall be the fist element of the list.
    """
    result = [
        (u"oid", node.get(u"oid")),
        (u"status", node.get(u"status", u"current")),
        ]

    # other information
    for fields in [ u"description", u"referene" ]:
        value = node.findtext(fields)
        if value is not None:
            result.append( (fields, value) )

    return result

@jinja2.contextfilter
def fl_calc_oid_indent(ctx, oid_str):
    """calculate in dent depth and tree structure info
    input:
        ctx: context of the template
        oid_str: oid string
    return:
        a list of flags
        example:
          [0,1,1,0,2]
            0: vertical line through the cell
            1: no line
            2: vertical line through the cell (with horizontal line)
            3: vertical line to the cell (with horizontal line)
    """
    # extract variables from the context
    oid_prefix_level = ctx.parent[u"oid_prefix_level"]
    ttree = ctx.parent[u"tree_index"]

    oid = oid_str2tuple(oid_str)
    cur_level= len(oid)
    result = []
    for depth in xrange(oid_prefix_level, cur_level):
        val = oid[depth]
        pattern = 0 if ttree[ oid[oid_prefix_level-1:depth] ] > val else 1
        pattern += 0 if depth + 1 < cur_level else 2
        result.append( pattern )
        # print >>sys.stderr, "d={}, ttree{} = {}, v = {} -> {}".format(
        #        depth, oid[oid_prefix_level-1:depth], ttree[ oid[oid_prefix_level-1:depth] ], val, pattern )
    return result

@jinja2.contextfilter
def fl_short_oid(ctx, oid_str):
    """Shorten oid string

    example:
       root: 1.3.6.9.9
       1.3.6.9.9.1.2.3.4 -> ..(9).1.2.3.4

    input:
        ctx: template context
         - root_oid_prefix, root_oid_prefix_len
        oid_str: oid for root node (string)

    return:
        shortened oid (string)
    """

    root_oid_prefix = ctx.parent[u"root_oid_prefix"]
    oid_prefix_len  = ctx.parent[u"root_oid_prefix_len"]

    if oid_str.startswith(root_oid_prefix):
        oid_list = oid_str[oid_prefix_len:].split(u".")
        # print >>sys.stderr, "oid_str={}, oid_list={}, oid_prefix={}, len={}".format( oid_str, oid_list, root_oid_prefix, oid_prefix_len )
        return u"..({}).".format(oid_list[0]) + u".".join(oid_list[1:])

def create_oid_suffix_str(num):
    """
    """
    basestr = u'.' + u'.'.join(chr(n) for n in xrange( ord('a'), ord('z')+1 )) + u'.*'
    if num > 27:
        num = 27
    return basestr[:num * 2]

       
def fl_linkage_suffix(row):
    """create oid suffix suitable for linkage
    """
    augment = row.find("linkage/augments")
    if augment is not None:
        return ".*"
    linkages = row.findall("linkage/index")
    # print >>sys.stderr, "Linkages: {}, {}".format(row.get("name"),len(linkages))
    return create_oid_suffix_str(len(linkages))

_re_hyperlink_target = re.compile( r"[A-Za-z_][0-9A-Za-z_]*" )

@jinja2.contextfilter
def fl_hyperlink(ctx, in_str):
    """
    Add intra-file hyperlink for identifier

    Hyperlink_name : l_<name_of_identifier>
    e.g. abcDefGhi => l_abcDefGhi

    input:
        ctx : context
        index : hyperlnk

    return:
        Markup string

    """
    lookup = ctx.parent[u"index"]

    result = []
    current_pos = 0 # position of the last processed string
    match_result = _re_hyperlink_target.search(in_str, current_pos)
    while match_result:
        start_p = match_result.start()
        end_p   = match_result.end()
        if in_str[start_p:end_p] in lookup:
            # create hyperlink
            result.append( in_str[current_pos:start_p] )
            result.append( Markup(u'<a href="#l_{0}">{0}</a>' ).format( in_str[start_p:end_p] ))
            current_pos = end_p

        # next search from the last match position
        match_result = _re_hyperlink_target.search( in_str, end_p )

    result.append( in_str[current_pos:] )
    return Markup(u"").join( result )


@jinja2.contextfilter
def fl_format_description(ctx, desc_str, chain=fl_hyperlink):
    """Format description in SMIv2 MIB file for HTML output
    Type of result is Markup instead of string in order to avoid auto-escape.

    input:
        desc_str: description string (unicode_str)
    return:
        Markup including <p> tag
    """
    mline = [ line.strip() for line in desc_str.split("\n")]

    # print >>sys.stderr, mline
    # print >>sys.stderr, "mline={}, len={}\n".format( len(mline), len(desc_str))
    if len(mline) == 1:
        return chain(ctx, mline[0])

    def paragraph(lines):
        ll = []
        for l in lines:
            if l == "":
                if len(ll) > 0:
                    yield ll
                ll = []
            else:
                ll.append( l )
        if len(ll) > 0:
            yield ll
        
    # multiline
    return Markup(u"").join(
            [ Markup( u"<p>{}</p>\n" ).format( 
                Markup(u"<br />").join(
                [ chain( ctx, line ) for line in para ] ))
                for para in paragraph( mline )
            ])

def mib2xmlpipe( mibfile, force=False ):
    """Convert MIB file to XML and returns file handle

        Return None in case of conversion failure.
    """
    ENV_MIB2XML = "mib2xml"
    CMD_MIB2XML = "smidump"

    # get smidump command name

    import os, subprocess, shlex
    command = os.environ[ENV_MIB2XML] if os.environ.has_key(ENV_MIB2XML) else CMD_MIB2XML
    command += " -f xml "
    if force:
        command += "-k "
    command_line = shlex.split( command )
    command_line.append(mibfile)

    try:
        return subprocess.Popen( command_line, stdout=subprocess.PIPE )

    except OSError:
        return None

def callwithxml( filename, callback, force=False ):
    """Prepare XML file handle for parser.
        Just open the specified file when XML is directly given.
        Otherwise, try conversion from MIB to XML.

        callback function must take 1 argument, and accept file object and file name.

        return: return type of the callback function
        dependency: environment variable MIB2XMLTOOL override default 'smidump'.
    """

    mibp = None

    if not filename.endswith( ".xml" ):
        # assume given file is MIB
        mibp = mib2xmlpipe(filename, force)
        if mibp != None:
            try:
                return callback( mibp.stdout )
            finally:
                mibp.poll()

    return callback( filename )

def isEtree13Installed():
    "Check if proper version of ElementTree library is installed"

    from distutils.version import StrictVersion

    if StrictVersion(et.VERSION) < StrictVersion('1.3.0'):
        return False

    return True

def main():

    import textwrap

    if not isEtree13Installed():
        print >> sys.stderr, textwrap.dedent( """\
        Error: ELementTree library is older than expected.

        ElementTree 1.3 or newer, which is accompanied with Python 2.7,
        is required.
        """ )
        return 31


    parser = build_argparser()
    options = parser.parse_args()

    # We don't have to take error cases into account
    # because parse_args aborts program execution with error messages.
    # when given command line options are inappropriate

    filename = options.mibxml

    try:
        mib = callwithxml( filename, read_mib_xml, force=options.forceMibParse)
        # mib = read_mib_xml(filename)
    except (IOError):
        print >> sys.stderr, "Failed to open XML file: {}".format(filename)
        return 1

    except et.ParseError as e:
        print >> sys.stderr, textwrap.dedent( """\
        Parse Error : {}
        This tool accept MIB file or xml-formatted MIB file translated from MIB(SMI) file.

        Confirm if smidump command is in the search path
        or explicitly specified by "mib2xml" environment variable
        if you specified MIB file.

        Confirm if specified file is valid XML format
        compatible with smidump output
        if you specified xml file.

        smidump command is available as a part of libsmi
        http://www.ibr.cs.tu-bs.de/projects/libsmi/
        """ ).format(e.message)
        return 3

    try:
        # prepare
        undefinedPolicy = jinja2.Undefined
        if options.templateException == "strict":
            undefinedPolicy = jinja2.StrictUndefined
        elif options.templateException == "debug":
            undefinedPolicy = jinja2.DebugUndefined

        template_env = jinja2.Environment(autoescape=True,
                loader=jinja2.PackageLoader(__name__, package_path=""),
                undefined=undefinedPolicy)
        for key, func in prepare_filters().iteritems():
            template_env.filters[ key ] = func

        template = template_env.get_template("template.html")
        print template.render(**(prepare_context(mib, options)) )

    except InvalidMibError as e :
        print >> sys.stderr, "MIB XML is invalid: {}".format(e.message)
        return 5

    return 0
    
if __name__ == '__main__':
    sys.exit( main())
