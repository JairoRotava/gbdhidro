#!/usr/bin/env python
# coding: utf-8

# Carrega bibliotecas de acordo com o necessario
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timezone, timedelta
from netCDF4 import num2date, date2num, stringtoarr
from gbdhidro import utilconversor
from gbdhidro import utilcf
from gbdhidro.netcdfjson import NetCDFJSON
from gbdhidro.hobo import hobo
from cfchecker.cfchecks import main
import sys


VERSION = '0.0.1'
TOOL_NAME = 'HOBO Pendant Event Data Logger (UA-003-64) to NetCDF conversion tool v.' + VERSION

# Pega path absoluto deste arquivo
here = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
FILE_PATH_DEBUG = './test/data/EHP02039.csv'
#OUTPUT_FOLDER_DEBUG = './'
#OUTPUT_FILE_DEBUG = None


# Parametros default
FILE_PATH = None
OUTPUT_FOLDER = ''
OUTPUT_FILE = None
JSON_FILE = os.path.join(here, 'precipitation_netcdf.json')
CONFIG_FILE = os.path.join(here, 'stations_info.csv')
DECIMAL = '.'
SEPARATOR = ','
ENCODING = 'utf-8'

# Codigo de erro utilizado no shell em caso de problema
ERROR_CODE = 1


print(TOOL_NAME)

if DEBUG:
    # Esta em debug - seta essas variaveis de entrada para facilitar
    FILE_PATH = FILE_PATH_DEBUG
    #OUTPUT_FOLDER = OUTPUT_FOLDER_DEBUG
    #OUTPUT_FILE = OUTPUT_FILE_DEBUG
    print('WARNING: DEBUG MODE')
else:
    # nao esta em debug. Pega informações da linha de comando
    parser = argparse.ArgumentParser(description='Conversion tool arguments:')
    parser.add_argument("-i", "--input", help="hobo input file (.csv)")
    parser.add_argument("-o", "--output", help="output file")
    parser.add_argument("-d", "--directory", help="output directory")
    parser.add_argument("-c", "--config", help="stations config file (.csv)")
    parser.add_argument("-n", "--netcdf", help="json file with NetCDF file information")
    args = parser.parse_args()

    if args.netcdf:
        JSON_FILE = args.netcdf
    if args.config:
        CONFIG_FILE = args.config
    if args.directory:
        OUTPUT_FOLDER = args.directory
    if args.output:
        OUTPUT_FILE = args.output
    if args.input:
        FILE_PATH = args.input
    else:
        parser.print_help()
        exit(ERROR_CODE)

# Abre arquivo e extrai informacoes
title, serial_number, header, details = hobo.get_info(FILE_PATH)

#if not details:
#    # Erro - nao tem nenhuma informacao sobre esse titulo de plot
#    print('ERRO: arquivo sem detalhes. Arquivo deve ser exportado com detalhes para permitir verificacao')
#    exit(ERROR_CODE)


# Le arquivo .csv com configuracoes e informacoes adicionais das estacoes
cfgs = pd.read_csv(CONFIG_FILE)
row = cfgs.loc[cfgs['Plot Title'] == title]    # Procura por plot tittle igual do arquivo de entrada
if row.empty:
    # Erro - nao tem nenhuma informacao sobre esse titulo de plot
    print('ERROR: plot title ({}) not found in config file'.format(title))
    exit(ERROR_CODE)

# Extrai informacoes importantes sobre a estacao do arquivo de configuracao
station_id = row.iloc[0]['Codigo']
station_sn = row.iloc[0]['Numero de serie']
station_latitude = row.iloc[0]['Latitude [graus]']
station_longitude = row.iloc[0]['Longitude [graus]']
station_altitude = row.iloc[0]['Altitude [m]']
station_datetime_col = row.iloc[0]['Coluna data/hora']
station_gmt = int(row.iloc[0]['GMT'])
#station_time_resolution = row.iloc[0]['Intervalo medidas (ISO8601)']
station_variable_col = row.iloc[0]['Coluna variavel']
# Encontra coluna datetime de formar flexivel (procura por nome parecido)
datetime_col = None
for col_name in header:
    found = False
    if utilconversor.find_matches(col_name, station_datetime_col):
        datetime_col = col_name
        found = True
        break
if not datetime_col:
    print('ERROR: col ({}) not found'.format(station_datetime_col))
    exit(ERROR_CODE)
# Encontra timezone e verifica se esta dentro do valor esperado
gmt_hour_offset, gmt_minute_offset = utilconversor.get_gmt_offset(datetime_col)
if station_gmt != gmt_hour_offset:
    print('Warning: found timezone (GMT{}) different from config (GMT{}). Using GMT{}.'.format(gmt_hour_offset, station_gmt, gmt_hour_offset))

# Encontra nome de coluna de dados por semelhança
variable_col = None
for col_name in header:
    found = False
    if utilconversor.find_matches(col_name, station_variable_col):
        variable_col = col_name
        found = True
        break
if not variable_col:
    print('ERROR: col ({}) not found'.format(station_variable_col))
    exit(ERROR_CODE)

# Verifica resolucao de tempo se esta dentro da esperada
#details = hobo.process_details(details)

# TODO: Encontrar o campo no dicionario sem ser case sensitive
#serie = details['Details']['Series: ' + variable_col]
#details = details['Details']
#serie = None
#for k, v in details.items():
#    found = False
#    if utilconversor.find_matches(k, ['Series:', station_variable_col]):
#        serie = v
#        found = True
#        break
#if not serie:
#    print('ERRO: nao foi encontrada informacao da serie nos detalhes')
#    exit(ERROR_CODE)


#filter_param = serie['Filter Parameters']
#filter_type = filter_param['Filter Type']
#filter_interval = filter_param['Filter Interval']

# TODO: isso nao esta bom, os formatos utilizados nao sao flexiveis e iguais. Automatizar mehlor isso no futuro
#if filter_type != 'Sum of event values':
#    print('ERRO: serie com filtro inesperado: {}'.format(filter_type))
#    exit(ERROR_CODE)

#if filter_interval == '5 Minutes':
#    if station_time_resolution != 'PT5M':
#        print('AVISO: serie com intervalo {}, esperado era {}'.format(filter_interval, station_time_resolution))
#        station_time_resolution = 'PT5M'
#elif filter_interval == '1 Day':
#    if station_time_resolution != 'PT1D':
#        print('AVISO: serie com intervalo {}, esperado era {}'.format(filter_interval, station_time_resolution))
#        station_time_resolution = 'PT1D'
#else:
#    print('ERRO: resolucao temporal ainda nao implenteada: {}'.format(filter_interval))
#    exit(ERROR_CODE)





#if station_time_resolution == 'PT5M':
#    if filter_interval != '5 Minutes':
#        print('ERRO: serie com intervalo {}, esperado era {}'.format(filter_interval, station_time_resolution))
#        exit(ERROR_CODE)
#elif station_time_resolution == 'PT1D':
#    if filter_interval != '1 Day':
#        print('ERRO: serie com intervalo {}, esperado era {}'.format(filter_interval, station_time_resolution))
#        exit(ERROR_CODE)
#else:
#    print('Erro: resolucao temporal ainda nao implenteada: {}'.format(station_time_resolution))
#    exit(ERROR_CODE)

# Extrai dados da aquisicao
table = hobo.get_data(FILE_PATH)

# Separa precipitacao
precipitation = table[variable_col]
precipitation.index = table[datetime_col]
precipitation = precipitation.dropna()  # Deleta os NaN

# Processa dados de data/hora
#date_str = table[datetime_col]
date_str = precipitation.index.to_series()
date_time = pd.to_datetime(date_str, format='%m/%d/%y %I:%M:%S %p')
#gmt_hour_offset = station_gmt
#gmt_minute_offset = 0
tzinfo=timezone(timedelta(hours=gmt_hour_offset, minutes=gmt_minute_offset))
# gera os indices com informacao de fuso horarios incluido
index = date_time.dt.tz_localize(tzinfo)
# converte para UTC
index_utc = index.dt.tz_convert('UTC')

# Identifica primeiro e ultimo evento de aquisicao
first_day_str = utilcf.datetime2str(index_utc.iloc[0])
last_day_str = utilcf.datetime2str(index_utc.iloc[-1])
#logger.debug("Inicio e fim de medidas em UTC: {} - {}".format(first_day_str, last_day_str))

# Gera nome do arquivo de saida se ainda nao foi definido
if OUTPUT_FILE is None:
    file_name = '{}_{}_{}.nc'.format(station_id, first_day_str, last_day_str)
else:
    file_name = OUTPUT_FILE

# Adiciona pasta de saida no path se definido
if OUTPUT_FOLDER is None:
    nc_file_path = file_name
else:
    nc_file_path = os.path.join(OUTPUT_FOLDER, file_name)

# Cria arquivo netCDF
nc_file = NetCDFJSON()
nc_file.write(nc_file_path)
# Le arquivo json com configuracao da estrutura do netcdf
nc_file.load_json(JSON_FILE)
nc_file.create_from_json()

# pega handlers para dimensoes
timeDim = nc_file.get_dimension('time')
nameDim = nc_file.get_dimension('name_strlen')
# pega handlers para variaveis
time = nc_file.get_variable('time')
#time_bnds = nc_file.get_variable('time_bnds')
lat = nc_file.get_variable('lat')
lon = nc_file.get_variable('lon')
alt = nc_file.get_variable('alt')
station_name = nc_file.get_variable('station_name')

np_time = index_utc.to_numpy()
nc_time = date2num(np_time, units=time.units, calendar=time.calendar)
# A precipitacao eh acumulada no tempo. O CF estabelece que neste tipo de caso
# eh necessario informar as fronteiras do tempo no qual eh feito o acumulo. No caso de ser a medida
# acumulada nos ultimos 5 minutos as fronteiras sao o tempo atual - 5 min, e o tempo atual

#nc_superior_bound_time = nc_time
#if station_time_resolution == 'PT5M':
#    delta = timedelta(minutes=5)
#elif station_time_resolution == 'PT1D':
#    delta = timedelta(days=1)
#else:
#    print('Erro. Intervalo de tempo ainda nao implementada {}'.format(station_time_resolution))
#    exit(ERROR_CODE)

#delta = utilcf.period_iso8601_to_relativetime(station_time_resolution)
#inferior_bound_time = np_time - delta

#nc_inferior_bound_time = date2num(inferior_bound_time, units=time.units, calendar=time.calendar)
# combina bound inferior com bound superior
#nc_time_bnds = np.stack((nc_inferior_bound_time, nc_superior_bound_time), axis=-1)

# Seta variaveis
lat[:] = np.array([station_latitude])
lon[:] = np.array([station_longitude])
alt[:] = np.array([station_altitude])
time[:] = nc_time
#time_bnds[:] = nc_time_bnds
station_name[:] = stringtoarr(station_id, nameDim.size)
# Insere informacoes sobre a precipitacao
nc_var = nc_file.get_variable('precipitation')
nc_file.rootgrp.keywords = [nc_var.standard_name, nc_var.units, station_id]
nc_file.rootgrp.key_variables = 'precipitation'

FILL_VALUE = nc_var._FillValue
#data_var = table[variable_col]
data_var = precipitation
data_var = data_var.replace(np.nan, FILL_VALUE)
data_var = data_var.to_numpy()
nc_var[:] = data_var
data_len = len(data_var)

# Faz processamento para metadados
# Processa os dados ja convertidos para facilitar reutilizar o codigo depois

# min max lat e lon
min_lat = np.amin(lat)
max_lat = np.amax(lat)
min_lon = np.amin(lon)
max_lon = np.amax(lon)

# time duration
min_time = num2date(np.amin(time), units=time.units, calendar=time.calendar)
max_time = num2date(np.amax(time), units=time.units, calendar=time.calendar)
min_time_str = utilcf.datetime2str(min_time)
max_time_str = utilcf.datetime2str(max_time)
time_delta = max_time - min_time
time_delta_str = utilcf.timedelta2str(time_delta)
# time resolution
#time_resolution_str = station_time_resolution

# Atualiza metadados
nc_file.rootgrp.geospatial_lat_min = min_lat
nc_file.rootgrp.geospatial_lat_max = max_lat
nc_file.rootgrp.geospatial_lon_min = min_lon
nc_file.rootgrp.geospatial_lon_max = max_lon
nc_file.rootgrp.time_coverage_start = min_time_str
nc_file.rootgrp.time_coverage_end = max_time_str
nc_file.rootgrp.time_coverage_duration = time_delta_str
#nc_file.rootgrp.time_coverage_resolution = time_resolution_str
nc_file.rootgrp.id = file_name
nc_file.rootgrp.date_created = utilcf.datetime2str(datetime.now(timezone.utc))
nc_file.rootgrp.history = '({}) Created with {}'.format(nc_file.rootgrp.date_created, TOOL_NAME)
nc_file.close()

# Imprime resultado
print('Input file: {}'.format(FILE_PATH))
print('Output file: {}'.format(nc_file_path))
print('Latitude Min/Max: {} / {}'.format(min_lat, max_lat))
print('Longitude Min/Max: {} / {}'.format(min_lon, max_lon))
print('Datetime (UTC) Min/Max: {} / {}'.format(min_time_str, max_time_str))
print('Coverage duration: {}'.format(time_delta_str))
print('Data length: {}'.format(data_len))

#print('Resolucao: {}'.format(time_resolution_str))

# Checa se arquivo atende padrao CF utilizando o cfchecks
print('\nRunning cfchecks')
sys.argv = ['', nc_file_path]
sys.exit(main())
