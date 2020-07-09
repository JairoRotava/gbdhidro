
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
from gbdhidro import utilcf
import numpy
import datetime

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
ERROR_CODE = 1
LOG_FILE = 'upload.log'
# Mongodb info
MONGODB_URL = '127.0.0.1:27017'
DATABASE = 'gbdhidro'
COLLECTION = 'index'


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

def find(uuid=None, date=None, latlon=None, keywords=None):
    query_list = []
    # uuid
    if uuid:
        query_uuid = {'database_uuid': {'$regex': uuid, '$options': 'i'}}
        query_list.append(query_uuid)
    # start/stop dates
    if date:
        # Query para pegar qualquer dado que tenha algum overlap de tempo nessa faixa
        start_date = date[0]
        end_date = date[1]
        query_start_stop = {
            '$and': [
                {'time_coverage_start': {'$lte': end_date}},
                {'time_coverage_end': {'$gte': start_date}}
            ]
        }
        query_list.append(query_start_stop)
    # lat/lon area
    if latlon:
        lat_min = latlon[0]
        lon_min = latlon[1]
        lat_max = latlon[2]
        lon_max = latlon[3]
        # Query para pegar qualquer dado que tenha um overlap com essa area de lat/lon
        query_lat_lon = {
            '$and': [
                {'geospatial_lat_min': {'$lte': lat_max}},
                {'geospatial_lat_max': {'$gte': lat_min}},
                {'geospatial_lon_min': {'$lte': lon_max}},
                {'geospatial_lon_max': {'$gte': lon_min}}
            ]
        }
        query_list.append(query_start_stop)
    # keywords
    if keywords:
        query_keywords = {'keywords': {'$in': keywords}}
        query_list.append(query_keywords)

    # Finaliza query composta
    query = {
        '$and': query_list
    }
    return query


client = MongoClient(MONGODB_URL)
gbd = client[DATABASE]
index = gbd[COLLECTION]

mydoc = index.find(find(date=[start_date, end_date]))
for x in mydoc:
    print(x)

#client.close()





