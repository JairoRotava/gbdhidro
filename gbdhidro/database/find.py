
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

import argparse
import os
import glob
import subprocess
import logging
import sys
import os
from netCDF4 import Dataset
from shutil import copyfile
import zipfile
from pymongo import MongoClient
from gbdhidro.netcdf import cf
import numpy
import datetime
import iso8601

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
ERROR_CODE = 1
LOG_FILE = 'upload.log'
# Mongodb info
MONGODB_URL = '127.0.0.1:27017'
DATABASE = 'gbdhidro'
COLLECTION = 'index'

import argparse
import os
import glob
import subprocess
import logging
import sys
import os
from netCDF4 import Dataset
from shutil import copyfile
import zipfile
from pymongo import MongoClient
from gbdhidro.netcdf import cf
import numpy

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = os.path.realpath('./test/output/hobo_ua_003_64')
OUTPUT_FOLDER = os.path.realpath('../test/output/load_netcdf_to_db/database_root')
CONVERTER_LIST = [os.path.join(HERE, '../station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')]
FILE_OVERWRITE = True
ERROR_CODE = 1
LOG_FILE = 'upload.log'
# Mongodb info
MONGODB_URL = '127.0.0.1:27017'
DATABASE = 'gbdhidro'
COLLECTION = 'index'

DATABASE_DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'gbdroot')

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)



# para encontrar
uuid = 'eh-p07'
query_uuid = {'database_uuid': {'$regex': uuid, '$options': 'i'}}
lat_min = -35.0
lon_min = -52.64

lat_max = -31.0
lon_max = -52.62


# Query para pegar qualquer dado que tenha um overlap com essa area de lat/lon
query_lat_lon = {
    '$and': [
        {'geospatial_lat_min': {'$lte': lat_max}},
        {'geospatial_lat_max': {'$gte': lat_min}},
        {'geospatial_lon_min': {'$lte': lon_max}},
        {'geospatial_lon_max': {'$gte': lon_min}}
    ]
}

# Query para pegar qualquer dado que tenha algum overlap de tempo nessa faixa
start_date = datetime.datetime(2018, 1, 1, 0, 0, 0)
end_date = datetime.datetime(2021, 1, 28, 0, 0, 0)
query_start_stop = {
    '$and': [
        {'time_coverage_start': {'$lte': end_date}},
        {'time_coverage_end': {'$gte': start_date}}
    ]
}

# Query para retornar alguma palavra chave
# Case sensitive: talvez forçar que todas palavras chaves sejam em minusculo??
keywords = ['EH-P05', 'EH-P06']
query_keywords = {'keywords': {'$in': keywords}}

query_list = []
query_list.append(query_uuid)
query_list.append(query_start_stop)

# Query composta por querys menores
query = {
    '$and': query_list
}

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
    parser.add_argument('-uuid', type=str, help="uuid")
    parser.add_argument('-b', "--before", type=str, help="before datetime ISO8601 (eg. 2004-06-23T22:00:00Z)")
    parser.add_argument('-a', "--after", type=str, help="after datetime ISO8601 (eg. 2004-06-23T22:00:00Z)")
    parser.add_argument('--cornerlon', type=float, nargs='+', help="longitude in decimal degrees of box corners (eg. 10.2  13.23)")
    parser.add_argument('--cornerlat', type=float, nargs='+', help="latitude in decimal degrees of box corners (eg. -12.2 -1.1)")
    parser.add_argument('-k', '--keywords', type=str, help="keywords: 'keyword1, keyword2'")
    parser.add_argument('-c', '--custom', type=str, help="custom search:  '(mongodb syntax)'")
    args = parser.parse_args()

    uuid = args.uuid
    #period = args.period
    #region = args.region

    #    Date and time in UTC
    #    2020-10-16T19:27:42+00:00
    #    2020-10-16T19:27:42Z
    #    20201016T192742Z

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

    client = MongoClient(MONGODB_URL)
    gbd = client[DATABASE]
    index = gbd[COLLECTION]
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
    if DEBUG:
        logger.setLevel(level=logging.DEBUG)
    else:
        command_line()




