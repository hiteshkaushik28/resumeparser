import os, sys
import xml.etree.cElementTree as ET
import re
from collections import OrderedDict
import json


# Reading the config xml file

def read_config(configfile):
    tree = ET.parse(configfile)
    root = tree.getroot()
    config = []
    for child in root:
        term = OrderedDict()
        term["Term"] = child.get('name', "")
        for level1 in child:
            term["Method"] = level1.get('name', "")
            term["Section"] = level1.get('section', "")
            for level2 in level1:
                term[level2.tag] = term.get(level2.tag, []) + [level2.text]

        config.append(term)
    json_result = json.dumps(config, indent=4)
    # print("Specifications:\n {}".format(json_result))
    return config
