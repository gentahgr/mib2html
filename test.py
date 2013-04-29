#!/usr/bin/python
# -*- coding: utf-8 -*-
"""test script for mib2html
"""

import mib2html as mh

xml_filename="lldp_mib.xml"

def test():
    mib = mh.read_mib_xml(xml_filename)

    mib_index = mh.build_index(mib)
    root_oid, root_node = mh.find_root(mib,mib_index)

    print "root_oid: ", root_oid
    print "root_name: ", root_node

    root_level, tree = mh.build_tree_index(mib, root_oid)

    print "root_level: ", root_level
    
    for (t,v) in sorted(tree.iteritems()):
        print "{}\t{}".format(t,v)

def test2():
    print "create_oid_suffix_str"
    for f in [0,1,2,3,26,29]:
        print mh.create_oid_suffix_str(f)

test2()
