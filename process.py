#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\.{}\t\r\n]')
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

'''
    Only pts within or close to the limits of Minneapolis are allowed in the
    data set
'''
def inCityLimits(lat, lon):
    if lat <=  45.05125 and lat >= 44.889787:
        if lon <= -93.193794 and lon >= -93.329437:
            return True

    return False


def clean_amenity(value):
    if problemchars.search(value) != None or ':' in value:
        return None

    if value == 'CHURCH':
        return 'place_of_worship'
    elif value == 'parking_enterance':
        return 'parking_entrance'

    return value

'''
    Shapes the k-tags
'''
def shape_k_tag(element, node):
    # Lists to hold specific special fields
    addr = []
    node_refs = []
    metcouncil = []
    amenity = []

    # Iterate through tags and nds of an element
    for child in element:
        if child.tag == 'tag':
            if problemchars.search(child.attrib['k']) == None:
                if ":" in child.attrib["k"]:

                    """ Special K tags with important sub fields """
                    # "addr: field"
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

                    # Amenity tag
                    elif child.attrib['k'].startswith('amenity:'):
                        _len = len('amenity:')
                        if ':' not in child.attrib['k'][_len:]:
                            # Make sure value is clean
                            value = clean_amenity(child.attrib['v'])

                            if value != None:
                                # Clean poorly entered amenity values
                                amenity.append((child.attrib['k'][_len:],
                                    value))

                # All other k tags
                else:
                    node[child.attrib['k']] = child.attrib['v']

        elif child.tag == 'nd':
             node_refs.append(child.attrib['ref'])

    if metcouncil: node['metcouncil'] = dict(metcouncil)
    if amenity: node['amenity'] = dict(amenity)
    if addr: node['address'] = dict(addr)
    if node_refs: node['node_refs'] = node_refs

    return node

def shape_element(element):
    node = {}

    if element.tag == "node" or element.tag == "way" :
        # Latitude and longitude of point
        lat = lon = None
        try:
            lat = float(element.attrib["lat"])
            lon = float(element.attrib["lon"])

            # GEO 2D data
            node["pos"] = [lat, lon]
        except: pass

        # Lat is positive and lon is neg, so if they exist they won't be equal
        if (lat != lon and inCityLimits(lat, lon)) or lat == lon:
            # Type of node
            node['type'] = element.tag

            # Attributes of element
            created_tuples = []
            for key, value in element.attrib.items():
                if key in ['lat', 'lon']: continue # Pos data already added
                elif key in CREATED:
                    created_tuples.append((key, value))
                elif key.startswith('amenity'):
                    print 'HIT'
                else:
                    node[key] = value

            # Shape and store children tags
            node = shape_k_tag(element, node)

            # Created dict
            node["created"] = dict(created_tuples)

            return node

    return None


def process_map(file_in):
    file_out = "{0}.json".format(file_in[:-4])
    data = []

    # Store JSON ouput
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            # Clean element
            el = shape_element(element)
            if el:
                data.append(el)
                fo.write(json.dumps(el) + "\n")

    return data

if __name__ == '__main__':
    osm_file = "minneapolis-saint-paul_minnesota.osm"
    data = process_map(osm_file)
