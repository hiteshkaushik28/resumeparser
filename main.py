import os
import sys
import xml.etree.cElementTree as ET
import re
from collections import OrderedDict
import json


def read_document(filepath):
    f = open(filepath)
    raw = f.read()
    f.close()
    return raw


def singlevalue(document, block, subterms_dict, parsed_items_dict ):
    retval = OrderedDict()
    get_block_lines = parsed_items_dict["Blocks"].get(block)
    block_doc = "\n".join(get_block_lines)
    if block_doc != "NA":
        for node_tag, pattern_list in subterms_dict.items():
            for pattern in pattern_list:
                regex_pattern = re.compile(r"{}".format(pattern))
                match = regex_pattern.search(block_doc)
                if match is not None and len(match.groups()) > 0 and match.group(1) !="":
                    retval[node_tag] = match.group(1)
                    break

    return retval

# Block info value extractor


def block_value_extractor(document, block, subterms_dict, parsed_items_dict):
    retval = OrderedDict()
    single_block_lines = parsed_items_dict["Blocks"].get(block)
    for line in single_block_lines:
        for node_tag, pattern_string in subterms_dict.items():
            pattern_list = re.split(r",|:", pattern_string[0])
            matches = [pattern for pattern in pattern_list if pattern in line]
            if len(matches):
                info_string = ", ".join(list(matches)) + " "
                numeric_values = re.findall(r"([\d']{4})\s?-?(\d{2}[^\w+])?", line)
                if len(numeric_values):
                    value_list = list(numeric_values[0])
                    info_string = info_string + "-".join([value for value in value_list if value != ""])
                retval[node_tag] = info_string
                break
    return retval


# find if new block has begin
def is_new_block(line, subterms_dict):
    new_block = ""
    first_word_of_line = ""
    regex_pattern = re.compile(r"^[\s]?(\w+)?[:|\s]")
    match = regex_pattern.search(line)
    if match is not None and len(match.groups()) > 0 and match.group(1) != "":
        first_word_of_line = match.group(1)
        if first_word_of_line is not None:
            for node_tag, pattern_list in subterms_dict.items():
                for pattern in pattern_list:
                    if first_word_of_line in pattern:
                        new_block = node_tag
    return new_block

# partition into blocks
def block_extractor(document, block, subterms_dict, parsed_items_dict):
    retval = OrderedDict()
    if document != "NA":
        current_block = ""
        lines = re.split(r'[\n\r]+', document)
        for line in lines:
            new_block = is_new_block(line, subterms_dict)
            if new_block != "":
                current_block = new_block
                continue
            retval[current_block] = retval.get(current_block, []) + [line]
    return retval


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


# process doc as per config file
def parse_doc(document, config):
    parsed_items_dict = OrderedDict()

    for term in config:
        term_name = term.get('Term')
        extraction_proc = term.get('Proc')
        extraction_proc_ref = globals()[extraction_proc]
        block = term.get("Block")
        subterms_dict = OrderedDict()
        for node_tag, pattern_list in term.items()[3:]:
            subterms_dict[node_tag] = pattern_list
            parsed_items_dict[term_name] = extraction_proc_ref(document, block, subterms_dict, parsed_items_dict)
            del parsed_items_dict["Blocks"]
            return parsed_items_dict["Blocks"]

    # MAIN
    if len(sys.argv) != 3:
        print ("Usage: parser <configfile> <datafilesfolder>")
        sys.exit(0)
    final_result = []
    configfile = "./" + sys.argv[1]
    config = read_config(configfile)

    datafilesdir = "./" + sys.argv[2] + "/"
    docs = os.listdir(datafilesdir)

    for filename in docs:
        if os.path.isfile(datafilesdir + filename):
            document = read_document(datafilesdir + filename)
            result = parse_doc(document, config)
            final_result.append(result)

    json_result = json.dumps(final_result, indent=4)
    print("Final Result:\n {}".format(json_result))
