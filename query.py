"""File to make queries on a MongoDB collection that is formatted by process.py.
"""
import re
from sets import Set


class Query(object):
    """Class to make queries to a database."""

    def __init__(self, collection):
        self.collection = collection
        self.street_types_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

    def query_all(self):
        """Calls all other methods/ runs all current queries against the collection."""
        self.count_elements()
        self.query_amenity()
        self.query_postal_code()
        self.query_street_type()
        self.query_users()

    def count_elements(self):
        """Prints the number of nodes and ways in the collection."""
        count = self.collection.count()
        print 'Number of elements: {0}\n\n'.format(count)

    def query_amenity(self):
        """Lists the amenities in decreasing order of occurence."""
        query = [{'$match' : {'amenity' : {'$exists' : '1'}}},
                 {'$group' : {'_id' : '$amenity', 'count' : {'$sum' : 1}}},
                 {'$sort' : {'count' : -1}},
                 {'$limit' : 25}]

        amenity_count = self.collection.aggregate(query)

        for elem in amenity_count:
            print '{0} : {1}'.format(elem['_id'], elem['count'])

        print '\n\n'

    def query_postal_code(self):
        """Prints the distinct postal codes and how many there are."""
        postal_codes = self.collection.distinct('address.postcode')
        postal_codes.sort()

        for elem in postal_codes:
            print '{0}'.format(elem)

        print 'Number of distinct post codes: {0}\n\n'.format(len(postal_codes))

    def query_street_type(self):
        """Prints the distinct street name endings."""
        streets = self.collection.distinct('address.street')
        unique_endings = Set()

        for street in streets:
            match = self.street_types_re.search(street)

            if match:
                unique_endings.add(match.group())

        print unique_endings
        print "\n\n"

    def query_users(self):
        """Count and print in descending order to users with the most additions."""
        query = [{'$group' : {'_id' : '$created.user', 'count' : {'$sum' : 1}}},
                 {'$sort' : {'count' : -1}},
                 {'$limit' : 25}]
        users = self.collection.aggregate(query)

        num_users = 0
        for elem in users:
            print u'{0} : {1}'.format(elem['_id'], elem['count'])
            num_users += 1

        print '\nDistinct Users: {0}\n\n'.format(num_users)
