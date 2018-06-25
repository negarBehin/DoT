#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Oct 05, 2015    
##################################################################

# Merge Diameter dictionary with DoT dictionary 
import sys
from xml.etree import ElementTree

# Merge the input dictionaries and write the outpt to a file      
def merge_dictionaries(in_files, out_file):
    xml_element_tree = None
    for in_file in in_files:
        # Get the root
        data = ElementTree.parse(in_file).getroot()
        # Get all elements under dictionary tag and add them
        # to xml_element_tree
        for element in data.iter('dictionary'):
            if xml_element_tree is None:
                xml_element_tree = data 
            else:
                xml_element_tree.extend(element) 
    if xml_element_tree is not None:
        # Write xml_element_tree to output file
        mergesource = open(out_file,"w")
        mergesource.write(ElementTree.tostring(xml_element_tree))
        mergesource.close()
        
if __name__ == "__main__":
    # Get the inputs file and output filename from arguments
    # passed in run time
    try:
        in_files = (sys.argv[1],sys.argv[2])
        out_file = sys.argv[3]
        
    # Set the inputs file and output filename to defaults if
    # an exception occured when trying to get the runn-time args
    except:
        in_files = ("dictDiameter.xml","dictDoT.xml")
        out_file = "mergeDic.xml"        
    merge_dictionaries(in_files,out_file)
