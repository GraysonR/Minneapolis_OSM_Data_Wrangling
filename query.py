from pymongo import MongoClient
from sets import Set
import re

STREET_TYPES_RE = re.compile(r'\b\S+\.?$', re.IGNORECASE)


def count_elements(collection):
    count = collection.count()
    print 'Number of elements: {0}\n\n'.format(count)

def query_amenity(collection):
    query = [{'$match' : {'amenity' : {'$exists' : '1'}}},
             {'$group' : {'_id' : '$amenity', 'count' : {'$sum' : 1}}},
             {'$sort' : {'count' : 1}}]

    amenity_count = collection.aggregate(query)

    for elem in amenity_count:
        print '{0} : {1}'.format(elem['_id'], elem['count'])

    print '\n\n'

def query_postal_code(collection):
    postalCodes = collection.distinct('address.postcode')
    postalCodes.sort()

    for elem in postalCodes:
        print '{0}'.format(elem)

    print 'Number of distinct post codes: {0}\n\n'.format(len(postalCodes))

def query_street_type(collection):
    streets = collection.distinct('address.street')
    unique_endings = Set()

    for s in streets:
        match = STREET_TYPES_RE.search(s)

        if match:
            unique_endings.add(match.group(0))

    print unique_endings
    print "\n\n"
