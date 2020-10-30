import iso8601
import re
import argparse
import logging
from pymongo import MongoClient
import gbdhidro.database.credentials as cred

# Exemplos de query para mongoDB
#db.getCollection('index').find({'database_uuid': 'gbdhidro/estacoes/eh-p05/EH-P05_20200226T190000Z_20200508T151000Z.nc'})
#db.getCollection('index').find({geospatial_lat_min: { $gt: -31.4, $lt: 0}})
#db.getCollection('index').find({geospatial_lat_min: { $gt: -32, $lt: -31.55}})
#db.getCollection('index').find({database_uuid: { $regex: /eh-p01/ }})
#db.getCollection('index').find({time_coverage_start: { $gt: new Date('2020-03-09')}})
#db.bios.find( { birth: { $gt: new Date('1940-01-01'), $lt: new Date('1960-01-01') } } )
#db.getCollection('index').find({keywords: { $in: ["EH-P01"]}})
#db.getCollection('index').find({database_uuid: { $regex: 'eh-p01/EH' }})
#db.getCollection('index').find({database_uuid: { $regex: '2020', $options: 'i' }})
#db.getCollection('index').find({keywords: { $elemMatch: {$regex: 'eh-p05', $options: 'i'}}})

DEFAULT_MONGO_DATABASE = 'gbdhidro'
DEFAULT_COLLECTION = 'index'
DEFAULT_MONGO_PORT = 27017

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def make_query(uuid=None, before=None, after=None, cornerlon=None, cornerlat=None, keywords=None, custom=None):
    query_list = []
    # uuid
    if uuid:
        query_uuid = {'database_uuid': {'$regex': uuid, '$options': 'i'}}
        query_list.append(query_uuid)

    # check for data before date
    if before:
        query_list.append({'time_coverage_start': {'$lte': before}})

    # check for data after date
    if after:
        query_list.append({'time_coverage_end': {'$gte': after}})

    # cornerlon
    if cornerlon:
        lon_min = cornerlon[0]
        lon_max = cornerlon[1]
        # Query para pegar qualquer dado que tenha um overlap com essa area de lat/lon
        query_lon = {
            '$and': [
                {'geospatial_lon_min': {'$lte': lon_max}},
                {'geospatial_lon_max': {'$gte': lon_min}}
            ]
        }
        query_list.append(query_lon)

    # cornerlat
    if cornerlat:
        lat_min = cornerlat[0]
        lat_max = cornerlat[1]
        # Query para pegar qualquer dado que tenha um overlap com essa area de lat/lon
        query_lat = {
            '$and': [
                {'geospatial_lat_min': {'$lte': lat_max}},
                {'geospatial_lat_max': {'$gte': lat_min}}
            ]
        }
        query_list.append(query_lat)


    # keywords
    if keywords:
        query_keywords = {'keywords': {'$in': keywords}}
        query_list.append(query_keywords)

    if custom:
        query_custom = {}
        query_list.append(query_custom)

    # Finaliza query composta
    if len(query_list) >= 1:
        p_query = {
            '$and': query_list
        }
    else:
        p_query = {}

    return p_query


def command_line():
    """
    Captura dados de linhas de comando
    """
    TOOL_DESCRIPTION = 'Find item in database'
    parser = argparse.ArgumentParser(description=TOOL_DESCRIPTION)
    parser.add_argument("index_user", type=str, help="index credential user:password@host:port/database")
    parser.add_argument('-uuid', type=str, help="uuid")
    parser.add_argument('-b', "--before", type=str, help="before datetime ISO8601 (eg. 2004-06-23T22:00:00Z)")
    parser.add_argument('-a', "--after", type=str, help="after datetime ISO8601 (eg. 2004-06-23T22:00:00Z)")
    parser.add_argument('--cornerlon', type=float, nargs='+', help="longitude in decimal degrees of box corners (eg. 10.2  13.23)")
    parser.add_argument('--cornerlat', type=float, nargs='+', help="latitude in decimal degrees of box corners (eg. -12.2 -1.1)")
    parser.add_argument('-k', '--keywords', type=str, help="keywords: 'keyword1, keyword2'")
    parser.add_argument('-c', '--custom', type=str, help="custom search:  '(mongodb syntax)'")
    args = parser.parse_args()

    # Credenciais para index/Mongo 'user:pass@hostname:port/path'
    #regex = "(((?P<user>[^:@]+)(:(?P<password>[^@]+))?)@)?(?P<hostname>[^:]+)(:(?P<port>[^/]+))?(/(?P<path>.+))?"
    #pattern = re.compile(regex)
    #m = pattern.match(args.index_user)
    #mongo = {
    #    'user': m.group('user'),
    #    'hostname': m.group('hostname'),
    #    'port': int(m.group('port')),
    #    'password': m.group('password'),
    #    'database': m.group('path')
    #}

    mongo = cred.extract(args.index_user)
    mongo['database'] = mongo['path']

    mongo['user'], mongo['password'] = cred.ask_user_and_pass(mongo['user'], mongo['password'], prompt='Index credentials')

    if mongo['database'] is None:
        mongo['database'] = DEFAULT_MONGO_DATABASE

    if mongo['port'] is None:
        mongo['port'] = DEFAULT_MONGO_PORT

    uuid = args.uuid

    if args.cornerlon:
        cornerlon = args.cornerlon
        logger.debug('Corner longitude: {}'.format(cornerlon))
    else:
        cornerlon = None

    if args.cornerlat:
        cornerlat = args.cornerlat
        logger.debug('Corner latitude: {}'.format(cornerlat))
    else:
        cornerlat = None

    if args.before:
        before = iso8601.parse_date(args.before)
        logger.debug('Before: {}'.format(before))
    else:
        before = None

    if args.after:
        after = iso8601.parse_date(args.after)
        logger.debug('After: {}'.format(after))
    else:
        after = None

    if args.keywords:
        keywords = args.keywords.split(',')
        keywords = [k.strip() for k in keywords]
    else:
        keywords = None
    custom = args.custom

    client = MongoClient(mongo['hostname'], username=mongo['user'], password=mongo['password'], port=mongo['port'])
    gbd = client[mongo['database']]
    index = gbd[DEFAULT_COLLECTION]
    my_query = make_query(uuid=uuid, before=before, after=after, cornerlon=cornerlon, cornerlat=cornerlat,
                          keywords=keywords, custom=custom)
    logger.debug('Mongodb query: {}'.format(my_query))
    items = index.find(my_query)
    total_found = 0
    for i in items:
        print(i)
        total_found += 1

    print('Found {} items'.format(total_found))

    client.close()


# Chamado da linha de comando
if __name__ == "__main__":
    command_line()




