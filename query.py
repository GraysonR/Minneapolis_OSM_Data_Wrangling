"""File to make queries on a MongoDB collection that is formatted by process.py.

Attributes:
    STREET_TYPES_RE (regex): Compile regular expression to get the last word in
        a street name. AKA-The street type.
"""
import re
from sets import Set

STREET_TYPES_RE = re.compile(r'\b\S+\.?$', re.IGNORECASE)


class Query(object):
    """Class to make queries to a database."""

    def __init__(self, collection):
        """Constructor taking in a collection"""
        self.collection = collection

    def query_gen_info(self):
        """Calls all other methods/runs all current queries against the collection."""
        self.count_elements()
        self.query_location()
        self.query_amenity()
        self.query_users()

        return

    def count_elements(self):
        """Prints the number of nodes and ways in the collection."""
        count = self.collection.count()
        ways_count = self.collection.find({'type': 'way'}).count()
        ways_percent = int(ways_count * 100 / count)

        print 'Number of elements: {0}'.format(count)
        print 'Number of nodes: {0}  ({1}%)'.format(count - ways_count, 100 - ways_percent)
        print 'Number of ways:  {0}  ({1}%)'.format(ways_count, ways_percent)

        print '\n\n'

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
            match = STREET_TYPES_RE.search(street)

            if match:
                unique_endings.add(match.group())

        print unique_endings
        print "\n\n"

    def query_users(self):
        """Query information about the users.

        Gets information about the total number of users and the users with less than 5 posts. Then
        lists the most prominent users in decreasing order along with the number of posts and the
        percentage they contributed to the project.
        """
        user_query = [{'$group' : {'_id' : '$created.user', 'count' : {'$sum' : 1}}},
                      {'$sort' : {'count' : -1}},
                      {'$limit' : 25}]
        lt_query = [{'$group' : {'_id' : '$created.user', 'count' : {'$sum' : 1}}},
                    {'$match' : {'count' : {'$lte' : 5}}},
                    {'$group' : {'_id' : '_id', 'count' : {'$sum' : 1}}}]

        users = self.collection.aggregate(user_query)
        count = len(self.collection.distinct('created.user'))
        collection_count = self.collection.count()
        min_user_count = self.collection.aggregate(lt_query).next()['count']


        print 'Users: {0}'.format(count)
        print 'Users with less than 5 posts: {0} ({1:.2%})\n'.format(min_user_count,
                                                                     float(min_user_count) / count)

        template = u'{USER:17}|{POSTS:9}|{PERCENT:>7}'
        print template.format(USER='User', POSTS='Posts (#)', PERCENT='Percent')
        for elem in users:
            dec_format = '{:.2g}%'.format(float(elem['count']) * 100 / collection_count)
            print template.format(USER=elem['_id'], POSTS=elem['count'], PERCENT=dec_format)

        print '\n\n'

    def query_location(self):
        """Get information about how many nodes have location data."""
        query = [{'$match' : {'pos' : {'$exists' : '1'}}},
                 {'$group' : {'_id' : '$pos', 'count' : {'$sum' : 1}}},
                 {'$group' : {'_id' : 'id', 'count' : {'$sum' : 1}}}]

        loc_count = self.collection.aggregate(query).next()['count']
        loc_percent = float(loc_count) * 100 / self.collection.count()

        print 'Nodes or ways with location data: {0}  ({1:.2g}%)\n\n'.format(loc_count, loc_percent)
