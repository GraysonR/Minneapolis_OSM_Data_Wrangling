"""File to read an Open Street Map xml file and clean it.

This module has code to clean a .osm file and turn it into a json file. The
functions can be used individually or the function process_map can take in a
.osm file and return a cleaned .json file.


Attributes:
    PROBLEMCHARS (regex): Compiled regular expression to determine if there
        are any characters that would not work or be problematic when
        trying to structure the data.
    STREET_TYPES_RE (regex): Compile regular expression to get the last word in
        a street name. AKA-The street type.
    CITY_NAMES (list): List of acceptable city names for a node/way to be in.
    CREATED (list): List of strings that correspond to information in a XML
        elements attribute section about who added the data.
    POSTCODES (list): List of acceptable Minneapolis post codes.
    STREET_DICT (dict): Dictionary to transform non-normal street endings to
        more standardized endings.
"""
import xml.etree.cElementTree as ET
import re
import codecs
import json

PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\.{}\t\r\n]')
CITY_NAMES = ["Minneapolis", "Saint Paul", "Minneapolis, MN", "St. Paul"]
CREATED = ["version", "changeset", "timestamp", "user", "uid"]
POSTCODES = ["55401", "55402", "55403", "55404", "55405", "55406", "55407",
             "55408", "55409"]
POSTCODES += ["554" + str(x) for x in range(10, 89)]
STREET_TYPES = {"ave": "Avenue", "av": "Avenue", "blvd" : "Boulevard",
                "boulivard" : "Boulevard", "ct": "Court", "dr": "Drive",
                "e": "East", "ln": "Lane", "n": "North", "ne": "Northeast",
                "nw": "Northwest", "northwest`": "Northwest", "pkwy": "Parkway",
                "pl": "Plaza", "rd": "Road", "s": "South", "se": "Southeast",
                "sw": "Southwest", "street": "Street", "st": "Street",
                "trl": "Trail", "ter": "Terrace", "terr": "Terrace",
                "w": "West"}


def in_city_limits(lat, lon):
    """Determines if a node is within the Minneapolis city boundaries.

    Args:
        lat (float): The latitude of the point.
        long (float): The longitude of the point.

    Returns:
        bool: True if latitude and longitude are within the city boundaries
            and False otherwise.
    """
    if lat <= 45.05125 and lat >= 44.889787:
        if lon <= -93.193794 and lon >= -93.329437:
            return True

    return False

def clean_street_field(value):
    """Makes sure the street name is formated correctly.

    Args:
        value (str): The original street name.

    Returns:
        str: Same string or updated string depending on how it was originally
            formated.
    """

    street = value.split(' ')
    value = ''

    for word in street:
        # Space between words
        if len(value) != 0:
            value += ' '

        temp_word = word.lower()
        temp_word.replace('.', ' ')

        if temp_word in STREET_TYPES.keys():
            value += STREET_TYPES[temp_word]
        else:
            value += word

    return value

def clean_k_value(value):
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

def clean_subfield_tags(key, value):
    """Cleans and structures the subfields of a k-tag.

    Args:
        key (str): The key string of the subfield.
        value (str): The value associated with the key.

    Returns:
        (int, str, str): Number to specify which dictionary it goes in (addr or
            metcouncil), the key in the dictionary, and the value for that key.
    """
    if key.startswith('addr:'):
        # Deals with inconsistent state entered
        if key == 'addr:state':
            if 'w' not in str.lower(value):
                return (0, 'state', 'MN')

        elif key == 'addr:postcode':
            if value.isdigit() and len(value) >= 5:
                if len(value) == 10 and value[:6] in POSTCODES:
                    return (0, 'postcode', value[:6])
                elif len(value) == 5 and value in POSTCODES:
                    return (0, 'postcode', value)

        elif key == 'addr:street':
            return (0, 'street', clean_street_field(value))

        elif key == 'addr:city':
            if value in CITY_NAMES:
                if 'MN' in value:
                    return (0, 'city', CITY_NAMES[0])
                elif value == 'St. Paul':
                    return (0, 'city', CITY_NAMES[1])
                else:
                    return (0, 'city', value)

        elif ':' not in key[5:]:
            return (0, key[5:], value)

    elif key.startswith('metcouncil:'):
        k_len = len('metcouncil:')

        if ':' not in key[k_len:]:
            return (1, key[k_len:], value)

    return (-1, None, None)

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
        None: Inconsistent data in the k-tags that indicated the node wasn't
            actually in Minneapolis.
    """
    # Lists to hold specific special fields
    subfields_list = [[], []]
    node_refs = []


    # Iterate through tags and nds of an element
    for child in element:
        if child.tag == 'tag':
            if PROBLEMCHARS.search(child.attrib['k']) is None:
                # Subfield information
                if ":" in child.attrib["k"]:
                    (spec, key, value) = clean_subfield_tags(child.attrib['k'],
                                                             child.attrib['v'])
                    if spec == -1:
                        return None
                    else:
                        subfields_list[spec].append((key, value))

                # All other k tags
                else:
                    value = clean_k_value(child.attrib['v'])

                    if value:
                        node[child.attrib['k']] = value

        elif child.tag == 'nd':
            node_refs.append(child.attrib['ref'])
    if subfields_list[0]:
        node['address'] = dict(subfields_list[0])
    if subfields_list[1]:
        node['metcouncil'] = dict(subfields_list[1])
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
        except KeyError:
            pass
        except ValueError:
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

            # Created dict
            node["created"] = dict(created_tuples)

            # Shape and store children tags
            node = shape_k_tag(element, node)

            return node

    return None

def process_map(file_in, collection):
    """Cleans map data and stores to a file.

    Receives a .osm file and goes node-by-node cleaning element and
    possibly adding it to the clean .json file with the same name as the .osm
    file. Also, adds the element into the collection.

    Args:
        file_in (str): Name of the file containing the data to be cleaned.
        collection (MongoCollection): Collection that the cleaned files will
            be stored in.
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

    collection.insert_many(data)
