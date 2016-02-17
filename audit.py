"""Quick and dirty auditing of raw XML to understand the problems, limitations,
and structure of the data.


Attributes:
    STREET_TYPES_RE (regex): Compile regular expression to get the last word in
        a street name. AKA-The street type.
    CREATED (list): List of strings that correspond to information in a XML
        elements attribute section about who added the data.
    FULL_STREET_NAMES (list): List of standard street name endings.
"""


import xml.etree.cElementTree as ET
from collections import Counter, defaultdict
from sets import Set
import re
import pprint
import time

STREET_TYPE_RE = re.compile(r'\b\S+\.?$', re.IGNORECASE)
FULL_STREET_NAMES = ["Street", "Avenue", "Boulevard", "Drive", "Court",
    "Place", "Square", "Lane", "Road", "Trail", "Parkway", "Commons", "Mall",
    "Terrace"]


def audit_street_type(filename):
    street_types = Counter()

    with open(filename, "r") as f:

        # Iterate over elemnts
        for _, elem in ET.iterparse(f, events=("start",)):
            if elem.tag == 'node' or elem.tag == 'way':
                # Iterate over tags for an element
                for tag in elem.iter("tag"):
                    if tag.attrib["k"] == 'addr:street':
                        # Last word/letters of street address
                        m = STREET_TYPE_RE.search(tag.attrib["v"])
                        if m:
                            # Add ending to dictionary
                            street_type = m.group()
                            if street_type not in FULL_STREET_NAMES:
                                street_types[street_type] += 1

    return street_types

def audit_node_tag_types(filename):
    tag_types = Counter()

    with open(filename, "r") as f:
        for _, elem in ET.iterparse(f, events=("start",)):
            if elem.tag == 'node':
                # Iterate over tags for an element
                for tag in elem.iter("tag"):
                    tag_types[tag.attrib["k"]] += 1

    return tag_types

def auit_addr_tag_types(filename):
    tag_types = defaultdict(Set)

    with open(filename, "r") as f:
        for _, elem in ET.iterparse(f, events=("start",)):
            if elem.tag == 'node':
                # Iterate over tags for an element
                for tag in elem.iter("tag"):
                    if "addr" in tag.attrib["k"]:
                        if tag.attrib["k"] in tag_types:
                            if tag.attrib["v"] not in tag_types[tag.attrib["k"]]:
                                tag_types[tag.attrib["k"]].append(tag.attrib["v"])
                        else:
                            tag_types[tag.attrib["k"]] = [tag.attrib["v"]]

    return tag_types

def audit_state_mn_zip(filename):
    zips = []
    for n in range(1,10): zips.append("5540" + str(n))
    for n in range(10, 89): zips.append("554" + str(n))

    states = Set()

    _in = 0
    not_in = 0

    with open(filename, "r") as f:
        for _, elem in ET.iterparse(f, events=("start",)):
            if elem.tag == 'node':
                # Iterate over tags for an element
                for tag in elem.iter("tag"):
                    if "addr:postcode" == tag.attrib["k"]:
                        value = tag.attrib["v"]
                        if value in zips:
                            _in += 1
                        else:
                            not_in += 1

                    elif "addr:state" == tag.attrib["k"]:
                        states.add(tag.attrib["v"])

    print (_in, not_in, states)

def audit_amenity_tag(filename):
    tag_types = Counter()

    with open(filename, "r") as f:
        for _, elem in ET.iterparse(f, events=("start",)):
            if elem.tag == 'node':
                # Iterate over tags for an element
                for tag in elem.iter("tag"):
                    if "amenity" in tag.attrib["k"]:
                        tag_types[tag.attrib["v"]] += 1

    return tag_types
