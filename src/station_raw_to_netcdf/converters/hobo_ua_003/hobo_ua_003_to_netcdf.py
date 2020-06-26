#!/usr/bin/env python
# coding: utf-8

# # Converte .csv de hoboware para estacao de precipitacao

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

# Pega path absoluto deste arquivo
here = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
ENCODING = 'utf-8'
config_file = 'stations_info.csv'
JSON_FILE = os.path.join(here, 'precipitation_netcdf.json')
EXPECTED_TIME_RESOLUTION = 'PT5M'
#IMAGE_FILE = os.path.join(here, 'p01.jpg')
FILE_PATH_DEBUG = '/media/jairo/Dados/Jairo/Projetos/Samuel data/git/GBD-Hidro/src/station_raw_to_netcdf/input/hobo UA-003 precipitacao/EHP02039.csv'
OUTPUT_FOLDER_DEBUG = './'
OUTPUT_FILE_DEBUG = None
#GMT = -3
DECIMAL = '.'
SEPARATOR = ','

# Codigo de erro utilizado no shell em caso de problema
ERROR_CODE = 1

if DEBUG:
    # Esta em debug - seta essas variaveis de entrada para facilitar
    FILE_PATH = FILE_PATH_DEBUG
    OUTPUT_FOLDER = OUTPUT_FOLDER_DEBUG
    OUTPUT_FILE = OUTPUT_FILE_DEBUG
else:
    # nao esta em debug. Pega informações da linha de comando
    parser = argparse.ArgumentParser(description='Converte arquivo para netCDF.')
    parser.add_argument("-i", "--input", help="nome do arquivo de entrada")
    parser.add_argument("-o", "--output", help="nome do arquivo de saida. Se nao for informado eh gerado automaticamente")
    parser.add_argument("-d", "--directory", help="nome do diretorio de saida")
    args = parser.parse_args()

    OUTPUT_FOLDER = args.directory
    OUTPUT_FILE = args.output
    FILE_PATH = args.input

    if FILE_PATH is None:
        parser.print_help()
        exit(ERROR_CODE)

# Abre arquivo e extrai informacoes
title, serial_number, header, details = hobo.get_info(FILE_PATH)

if not details:
    # Erro - nao tem nenhuma informacao sobre esse titulo de plot
    print('ERRO: arquivo sem detalhes. Arquivo deve ser exportado com detalhes para permitir verificacao')
    exit(ERROR_CODE)


# Abre arquivo com lista de sensores e informacoes extra
# Abre arquivo de configuracao e retira dados importantes
cfgs = pd.read_csv(config_file)
row = cfgs.loc[cfgs['Plot Title'] == title]
if row.empty:
    # Erro - nao tem nenhuma informacao sobre esse titulo de plot
    print('ERRO: arquivo nao reconhecido')
    exit(ERROR_CODE)
station_id = row.iloc[0]['Codigo']
station_sn = row.iloc[0]['Numero de serie']
station_latitude = row.iloc[0]['Latitude [graus]']
station_longitude = row.iloc[0]['Longitude [graus]']
station_altitude = row.iloc[0]['Altitude [m]']
station_datetime_col = row.iloc[0]['Coluna data/hora']
station_gmt = int(row.iloc[0]['GMT'])
station_time_resolution = row.iloc[0]['Intervalo medidas (ISO8601)']
station_variable_col = row.iloc[0]['Coluna variavel']

# Encontra colune datetime
datetime_col = None
for col_name in header:
    found = False
    if utilconversor.find_matches(col_name, station_datetime_col):
        datetime_col = col_name
        found = True
        break
if not datetime_col:
    print('ERRO: nao foi encontrada coluna {}'.format(station_datetime_col))
    exit(ERROR_CODE)

# Encontra timezone e verifica se esta dentro do valor esperado
gmt_hour_offset, gmt_minute_offset = utilconversor.get_gmt_offset(datetime_col)
if station_gmt != gmt_hour_offset:
    print('AVISO: fuso horario encontrado (GMT{}) diferente do esperado (GMT{}). Utilizando GMT{}. Isso esta correto?'.format(gmt_hour_offset, station_gmt, gmt_hour_offset))

# Encontra nome de coluna
# Isso eh necessario pois pode incluir o numero de serie
# por isso faz matching parcial

variable_col = None
for col_name in header:
    found = False
    if utilconversor.find_matches(col_name, station_variable_col):
        variable_col = col_name
        found = True
        break
if not variable_col:
    print('ERRO: nao foi encontrada coluna {}'.format(station_variable_col))
    exit(ERROR_CODE)

# Verifica resolucao de tempo se esta dentro da esperada
details = hobo.process_details(details)

# TODO: Encontrar o campo no dicionario sem ser case sensitive
#serie = details['Details']['Series: ' + variable_col]
details = details['Details']
serie = None
for k, v in details.items():
    found = False
    if utilconversor.find_matches(k, ['Series:', station_variable_col]):
        serie = v
        found = True
        break
if not serie:
    print('ERRO: nao foi encontrada informacao da serie nos detalhes')
    exit(ERROR_CODE)


filter_param = serie['Filter Parameters']
filter_type = filter_param['Filter Type']
filter_interval = filter_param['Filter Interval']

# TODO: isso nao esta bom, os formatos utilizados nao sao flexiveis e iguais. Automatizar mehlor isso no futuro
if filter_type != 'Sum of event values':
    print('ERRO: serie com filtro inesperado: {}'.format(filter_type))
    exit(ERROR_CODE)

if filter_interval == '5 Minutes':
    if station_time_resolution != 'PT5M':
        print('AVISO: serie com intervalo {}, esperado era {}'.format(filter_interval, station_time_resolution))
        station_time_resolution = 'PT5M'
elif filter_interval == '1 Day':
    if station_time_resolution != 'PT1D':
        print('AVISO: serie com intervalo {}, esperado era {}'.format(filter_interval, station_time_resolution))
        station_time_resolution = 'PT1D'
else:
    print('ERRO: resolucao temporal ainda nao implenteada: {}'.format(filter_interval))
    exit(ERROR_CODE)





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

# Processa dados de data/hora
date_str = table[datetime_col]
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

if OUTPUT_FILE is None:
    file_name = '{}_{}_{}.nc'.format(station_id, first_day_str, last_day_str)
else:
    file_name = OUTPUT_FILE

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
time_bnds = nc_file.get_variable('time_bnds')
lat = nc_file.get_variable('lat')
lon = nc_file.get_variable('lon')
alt = nc_file.get_variable('alt')
station_name = nc_file.get_variable('station_name')

np_time = index_utc.to_numpy()
nc_time = date2num(np_time, units=time.units, calendar=time.calendar)
# A precipitacao eh acumulada no tempo. O CF estabelece que neste tipo de caso
# eh necessario informar as fronteiras do tempo no qual eh feito o acumulo. No caso de ser a medida
# acumulada nos ultimos 5 minutos as fronteiras sao o tempo atual - 5 min, e o tempo atual

nc_superior_bound_time = nc_time
#if station_time_resolution == 'PT5M':
#    delta = timedelta(minutes=5)
#elif station_time_resolution == 'PT1D':
#    delta = timedelta(days=1)
#else:
#    print('Erro. Intervalo de tempo ainda nao implementada {}'.format(station_time_resolution))
#    exit(ERROR_CODE)

delta = utilcf.period_iso8601_to_relativetime(station_time_resolution)
inferior_bound_time = np_time - delta

nc_inferior_bound_time = date2num(inferior_bound_time, units=time.units, calendar=time.calendar)
# combina bound inferior com bound superior
nc_time_bnds = np.stack((nc_inferior_bound_time, nc_superior_bound_time), axis=-1)

# Seta variaveis
lat[:] = np.array([station_latitude])
lon[:] = np.array([station_longitude])
alt[:] = np.array([station_altitude])
time[:] = nc_time
time_bnds[:] = nc_time_bnds
station_name[:] = stringtoarr(station_id, nameDim.size)
# Insere informacoes sobre a precipitacao
nc_var = nc_file.get_variable('precipitation')
FILL_VALUE = nc_var._FillValue
data_var = table[variable_col]
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
time_resolution_str = station_time_resolution

# Atualiza metadados
nc_file.rootgrp.geospatial_lat_min = min_lat
nc_file.rootgrp.geospatial_lat_max = max_lat
nc_file.rootgrp.geospatial_lon_min = min_lon
nc_file.rootgrp.geospatial_lon_max = max_lon
nc_file.rootgrp.time_coverage_start = min_time_str
nc_file.rootgrp.time_coverage_end = max_time_str
nc_file.rootgrp.time_coverage_duration = time_delta_str
nc_file.rootgrp.time_coverage_resolution = time_resolution_str
nc_file.rootgrp.id = file_name
nc_file.rootgrp.date_created = utilcf.datetime2str(datetime.now(timezone.utc))
nc_file.close()

# Imprime resultado
print('Arquivo de saida: {}'.format(nc_file_path))
print('Numero de pontos: {}'.format(data_len))
print('Min/Max latitude: {} / {}'.format(min_lat, max_lat))
print('Min/Max longitude: {} / {}'.format(min_lon, max_lon))
print('Min/Max datetime: {} / {}'.format(min_time_str, max_time_str))
print('Duracao: {}'.format(time_delta_str))
print('Resolucao: {}'.format(time_resolution_str))

exit(0)
