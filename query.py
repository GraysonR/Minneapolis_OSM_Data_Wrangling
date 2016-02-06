from pymongo import MongoClient

def query_amenity(collection):
    query = [{'$match' : {'amenity' : {'$exists' : '1'}}},
             {'$group' : {'_id' : '$amenity', 'count' : {'$sum' : 1}}},
             {'$sort' : {'count' : 1}}]

    amenity_count = collection.aggregate(query)

    for elem in amenity_count:
        print '{0} : {1}'.format(elem['_id'], elem['count'])

def query_postal_code(collection):
    postalCodes = collection.distinct('address.postcode')
    postalCodes.sort()

    for elem in postalCodes:
        print '{0}'.format(elem)

    print len(postalCodes)
