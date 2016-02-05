from pymongo import MongoClient

def amenityQuery(db):
    query = [{'$match' : {'amenity' : {'$exists' : '1'}}},
             {'$group' : {'_id' : '$amenity', 'count' : {'$sum' : 1}}},
             {'$sort' : {'count' : 1}}]

    amenity_count = db.aggregate(query)

    for elem in amenity_count:
        print '{0} : {1}'.format(elem['_id'], elem['count'])

    return None

def postalCodeQuery(db):
    postalCodes = db.distinct('address.postcode')

    for elem in postalCodes:
        print '{0}'.format(elem)

    print len(postalCodes)

    return None
