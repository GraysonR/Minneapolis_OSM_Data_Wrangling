"""File to read an Open Street Map xml file and clean it.

This module has code to clean a .osm file and turn it into a json file. The
functions can be used individually or the function process_map can take in a
.osm file and return a cleaned .json file.


Attributes:
    PROBLEMCHARS (regex): Compiled regular expression to determine if there
        are any characters that would not work or be problematic when
        trying to structure the data.
    CREATED (list): List of strings that correspond to information in a XML
        elements attribute section about who added the data.

"""
import xml.etree.cElementTree as ET
import re
import codecs
import json

PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\.{}\t\r\n]')
CREATED = ["version", "changeset", "timestamp", "user", "uid"]


def in_city_limits(lat, lon):
    """Determines if a node is within the Minneapolis city boundaries.

    Args:
        lat (float): The latitude of the point.
        long (float): The longitude of the point.

    Returns:
        bool: True if latitude and longitude are within the city boundaries
            and False otherwise.
    boundaries.
    """
    if lat <= 45.05125 and lat >= 44.889787:
        if lon <= -93.193794 and lon >= -93.329437:
            return True

    return False

def clean_value(value):
    """Cleans string.

    Cleans the value of a k-tag fixing: misspelling, unnecessary capitalization.
    Also, if the value contains any problem characters or a ':', then the
    information was most likely entered incorrectly or in a manner that is
    inconsistent with OSM standards and is therfore ignored.

    Args:
        value (str): Value from a k-tag of an element in the osm data.

    Returns:
        str: Cleaned string.
        None: Value contains problem characters.
    """
    if PROBLEMCHARS.search(value) != None or ':' in value:
        return None

    if value == 'CHURCH':
        return 'place_of_worship'
    elif value == 'parking_enterance':
        return 'parking_entrance'

    return value

def shape_k_tag(element, node):
    """Cleans the k-tags of an element.

    Adds fields and subfields to a dictionary corresponding to speicific
    information. (e.g. address information and amentiy information)

    Args:
        element: The XML element beind cleaned.
        node (dict): The dictionary containing the new structured and cleaned
            information from element.

    Returns:
        dict: An updated node dictionary.
    """
    # Lists to hold specific special fields
    addr = []
    node_refs = []
    metcouncil = []

    # Iterate through tags and nds of an element
    for child in element:
        if child.tag == 'tag':
            if PROBLEMCHARS.search(child.attrib['k']) is None:
                if ":" in child.attrib["k"]:

                    # Special K tags with important sub fields

                    # Address information
                    if child.attrib['k'].startswith('addr:'):
                        if 'addr:state' == child.attrib["k"]:
                            addr.append(("state", "MN"))
                        elif ':' not in child.attrib['k'][5:]:
                            addr.append((child.attrib['k'][5:],
                                         child.attrib['v']))

                    # Metcouncil data from the city of MN
                    elif child.attrib['k'].startswith('metcouncil:'):
                        _len = len('metcouncil:')
                        if ':' not in child.attrib['k'][_len:]:
                            metcouncil.append((child.attrib['k'][_len:],
                                               child.attrib['v']))

                # All other k tags
                else:
                    value = clean_value(child.attrib['v'])

                    if value:
                        node[child.attrib['k']] = value

        elif child.tag == 'nd':
            node_refs.append(child.attrib['ref'])

    if metcouncil:
        node['metcouncil'] = dict(metcouncil)
    if addr:
        node['address'] = dict(addr)
    if node_refs:
        node['node_refs'] = node_refs

    return node

def shape_element(element):
    """Cleans an individual element in an XML tree."""
    node = {}

    if element.tag == "node" or element.tag == "way":
        # Latitude and longitude of point
        lat = lon = None
        try:
            lat = float(element.attrib["lat"])
            lon = float(element.attrib["lon"])

            # GEO 2D data
            node["pos"] = [lat, lon]
        except:
            pass

        # Lat is positive and lon is neg, so if they exist they won't be equal
        if (lat != lon and in_city_limits(lat, lon)) or lat == lon:
            # Type of node
            node['type'] = element.tag

            # Attributes of element
            created_tuples = []
            for key, value in element.attrib.items():
                if key in ['lat', 'lon']:
                    continue # Pos data already added
                elif key in CREATED:
                    created_tuples.append((key, value))
                else:
                    node[key] = value

            # Shape and store children tags
            node = shape_k_tag(element, node)

            # Created dict
            node["created"] = dict(created_tuples)

            return node

    return None

def process_map(file_in):
    """Cleans map data and stores to a file.

    Receives a .osm file and goes node-by-node cleaning element and
    possibly adding it to the clean .json file with the same name as the .osm
    file.

    Args:
        file_in (str): name of the file containing the data to be cleaned.
    """
    file_out = "{0}.json".format(file_in[:-4])
    data = []

    # Store JSON ouput
    with codecs.open(file_out, "w") as writer:
        for _, element in ET.iterparse(file_in):
            # Clean element
            element = shape_element(element)
            if element:
                data.append(element)
                writer.write(json.dumps(element) + "\n")
