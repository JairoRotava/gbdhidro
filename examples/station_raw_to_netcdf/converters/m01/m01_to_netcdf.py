#!/usr/bin/env python
# coding: utf-8

# # Desenvolvimento de conversao arquivo p05 para netcdf
# Este é um esqueleto para processamento dos arquivos csv/txt das plataformas, e conversão para netcdf, assim como preenchimento dos dados de informações (metadados). Os passos são os seguintes:
# 1. Abre arquivo JSON onde informações de configuração, da plataforma e dos arquivo netcdf estão armazenadas. Isso é necessário para flexibilizar o código e permitir reutilizacao do código. Isso é vantajoso quando várias estações com mesmo modelo de arquivo de saída são utilizadas.
# 2. Abertura do arquivo de imagem e conversão para base64. O arquivo netcdf não tem um tipo de variável adequado para armazenamento direto de arquivos binários. Ainda não esta fechado a melhor forma de armazenar esse tipo de dado dentro do netcdf, mas acho que converter o arquivo para baser64 (texto, muito utilizado em navegadores de internet) é um método razoavel. A vantagem dessa conversão é permitr armazenar os arquivos como texto simples, e fácil de recuperar. Esse formato ainda pode ser revisto.
# 3. Leitura do arquivo de dados, e varredura para alguns termos para confirmar que arquivo é da estação definida. Leitura das medidas em uma tabela Pandas
# 4. Criação do arquivo netcdf
# 5. Geração de metadados
# 6. Inserção dos dados no arquivo netcdf
# 7. Dump do arquivo para verificação
# 8. Verificação do padrão CF
# 
# Após desenvolvimento é possível exportar o codigo para .py e utilizar o codigo diretamente na linha de comando.

# Carrega bibliotecas de acordo com o necessario
import pandas as pd
import numpy as np
from datetime import datetime
import re
import os

from netCDF4 import Dataset,num2date, date2num
from datetime import timezone, timedelta

from netCDF4 import Dataset,num2date, date2num, stringtoarr
import json

from gbdhidro import utilconversor
from gbdhidro import utilcf
from gbdhidro.netcdfjson import NetCDFJSON
import base64

import argparse

from io import BytesIO
import logging

# Inicia logging
logger = logging.getLogger(__name__)

# Pega path absoluto deste arquivo
here = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
JSON_FILE = os.path.join(here, 'm01.json')
IMAGE_FILE = os.path.join(here, 'm01.jpg')
DECIMAL = ','
SEPARATOR = '\t'
VAR_LIST = {
        "date": {"match":["Date"], "pandas_col": None},
        "time": {"match":["Time"], "pandas_col": None},
        "temperature": {'netcdf_var': 'temperature', "match":["Temp", "Out"], "pandas_col": None},    
        "temperature_high": {'netcdf_var': 'temperature_high', "match":["Hi", "Temp"], "pandas_col": None},
        "temperature_low": {'netcdf_var': 'temperature_low', "match":["Low", "Temp"], "pandas_col": None},
        "humidity": {'netcdf_var': 'humidity', "match":["Out","Hum"], "pandas_col": None},
        "dew_point": {'netcdf_var': 'dew_point', "match":["Dew","Pt"], "pandas_col": None},
        "wind_speed": {'netcdf_var': 'wind_speed', "match":["Wind","Speed"], "pandas_col": None},
        "wind_speed_high": {'netcdf_var': 'wind_speed_high', "match":["Hi","Speed"], "pandas_col": None},
        "air_pressure": {'netcdf_var': 'air_pressure', "match":[" Bar"], "pandas_col": None},
        'precipitation': {'netcdf_var':'precipitation', 'match':[' Rain'], 'pandas_col': None},
        'precipitation_rate': {'netcdf_var':'precipitation_rate', 'match':['Rain', 'Rate'], 'pandas_col': None},
    }

GMT = -3

# Codigo de erro utilizado no shell em caso de problema
ERROR_CODE = 1
logger = logging.getLogger(__name__)

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)


if DEBUG:
    # Esta em debug - seta essas variaveis de entrada para facilitar
    FILE_PATH = '../../input/m01/m01.txt'
    OUTPUT_FOLDER = '../../output'
    OUTPUT_FILE = None
else:
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

# Abre arquivo json de configuração
with open(JSON_FILE, 'r') as fp:
    json_data = json.load(fp)

# Nome do arquivo de dados
STATION_NAME = json_data['station']['name']
# String com identificador utilizado para certificar que eh
# o arquivo da estao escolhida
STATION_ID = json_data['station']['name_match_string']
LATITUDE = json_data['station']['latitude']
LONGITUDE = json_data['station']['longitude']
ALTITUDE = json_data['station']['altitude']
IMAGE_FILE = json_data['station']['image']
#DATETIME_MATCH = json_data['station']['datetime_match_string']
#PRECIPITATION_MATCH = json_data['station']['precipitation_match_string']

# Seleciona encoding do arquivo
ENCODING = json_data['station']['input_file_encoding']
DECIMAL = '.'
SEPARATOR = '\t'



#logger.info("Conversao para estacao {}".format(STATION_NAME))

# Le arquivo de imagem
with open(os.path.join(here, IMAGE_FILE), "rb") as image_file:
    image_base64 = utilcf.bin2base64(image_file.read())


print('Conversor estacao {} para netcdf'.format(STATION_NAME))
fo = open(FILE_PATH, "r")
first_line = fo.readline()
second_line = fo.readline()
fo.close()

#logger.debug(first_line)
#logger.debug(second_line)
first_line_sep = first_line.split(SEPARATOR)
second_line_sep = second_line.split(SEPARATOR)
header = []
for l1, l2 in zip(first_line_sep, second_line_sep):
    header.append("{} {}".format(l1.strip(), l2.strip()))
logger.debug(header)    

# Procura por alguns termos especifcos para verificar se o arquivo
# esta dentro do esperado
if not utilconversor.find_matches(" ".join(header), STATION_ID):
    logger.error('Erro ao detectar identificador, arquivo fora do padrao esperado')
    exit(ERROR_CODE)
    
# Extrai dados da aquisicao
table = pd.read_csv(FILE_PATH, sep=SEPARATOR, skiprows=2, verbose=False, na_filter=True, header=None, encoding=ENCODING, decimal=DECIMAL, warn_bad_lines=True)

table.columns = header

for key, value in VAR_LIST.items():
    found = False
    for column in table.columns:
        if utilconversor.find_matches(column, value['match']):
            value['pandas_col'] = column
            found = True
            break
    if not found:
        logger.error('Erro, nao foi encontrada coluna {}'.format(key))
        exit(ERROR_CODE)



date = table[VAR_LIST["date"]["pandas_col"]]
time = table[VAR_LIST["time"]["pandas_col"]]
# Apaga estes elementos da lista pois ja foram utilizados
# evita atrapalhar algm codigo mais adiante
del VAR_LIST['date']
del VAR_LIST['time']

date_str = date.str.cat(time, sep=" ")
logger.debug(date_str)
date_time = pd.to_datetime(date_str, format='%d/%m/%y %H:%M')


# Processa datetime para incluir timezone
#date_str = table[date_time_col]
#date_time = pd.to_datetime(date_str, format='%d/%m/%y %I:%M:%S %p')
# extrai informacao de gmt
#gmt_hour_offset, gmt_minute_offset = utilconversor.get_gmt_offset(date_time.name)
# TODO: Como converte para UTC essa estacao?
gmt_hour_offset = GMT
gmt_minute_offset = 0
tzinfo=timezone(timedelta(hours=gmt_hour_offset, minutes=gmt_minute_offset))
# gera os indices com informacao de fuso horarios incluido
index = date_time.dt.tz_localize(tzinfo)
# converte para UTC
index_utc = index.dt.tz_convert('UTC')
first_day_str = utilcf.datetime2str(index_utc.iloc[0])
last_day_str = utilcf.datetime2str(index_utc.iloc[-1])
logger.info("Inicio e fim de medidas em UTC: {} - {}".format(first_day_str, last_day_str))



if OUTPUT_FILE is None:
    file_name = '{}_{}_{}.nc'.format(STATION_NAME, first_day_str, last_day_str)
else:
    file_name = OUTPUT_FILE

if OUTPUT_FOLDER is None:
    nc_file_path = file_name
else:
    nc_file_path = os.path.join(OUTPUT_FOLDER, file_name)

logger.info("Nome de arquivo de saida: {}".format(file_name))




#nc_file_path = os.path.join(OUTPUT_FOLDER, file_name)
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
precip = nc_file.get_variable('precipitation')
station_image = nc_file.get_variable('station_image')


# Insere lista de variaveis no netcdf
for key, value in VAR_LIST.items():
    nc_var = nc_file.get_variable(value['netcdf_var'])
    FILL_VALUE = nc_var._FillValue
    data_var = table[value['pandas_col']]
    data_var = data_var.replace(np.nan, FILL_VALUE)
    data_var = data_var.to_numpy()
    nc_var[:] = data_var
    


# Seta variaveis
nc_time = index_utc.to_numpy()
nc_time = date2num(nc_time,units=time.units,calendar=time.calendar)
# Como a precipitacao e o acumulado entre a ultima medida e a atual
# é necessario informar isso atraves dos bounds de tempo, ou seja,
# os valores inferioes e superiores respectivos ao limite do eixo de temp0
# O bound superior e o mesmo que o horario da medids
nc_superior_bound_time = nc_time
# bound inferior e o horario da ultima medida
nc_inferior_bound_time = np.roll(nc_superior_bound_time,1)
# a primeira medida não tem medida anterior, por isso seta para o mesmo valor
nc_inferior_bound_time[0] = nc_superior_bound_time[0]
# combina bound inferior com bound superior
bnds = np.stack((nc_inferior_bound_time, nc_superior_bound_time), axis=-1)

#nc_serie = precipitation.to_numpy()

nc_station_name = STATION_NAME
latitude = LATITUDE
longitude = LONGITUDE
altitude = ALTITUDE

lat[:] = np.array([latitude])
lon[:] = np.array([longitude])
alt[:] = np.array([altitude])

time[:] = nc_time
time_bnds[:] = bnds

#precip[:] = np.array(nc_serie)

station_name[:] = stringtoarr(nc_station_name, nameDim.size)
station_image[:] = stringtoarr(image_base64, len(image_base64))
station_image.file_name = IMAGE_FILE


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
time1 = num2date(time[1], units=time.units, calendar=time.calendar)
time0 = num2date(time[0], units=time.units, calendar=time.calendar)
time_resolution = time1 - time0
time_resolution_str = utilcf.timedelta2str(time_resolution)


logger.info('Min/Max latitude: {}/{}'.format(min_lat,max_lat))
logger.info('Min/Max longitude: {}/{}'.format(min_lon,max_lon))
logger.info('Min/Max datetime: {}/{}'.format(min_time_str,max_time_str))
logger.info('Time duration:{}'.format(time_delta_str))
logger.info('Time resolution:{}'.format(time_resolution_str))


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



# Fecha e salva arquivo
nc_file.close()

# Sai com codigo zero - sucesso
print('Arquivo de saida: {}'.format(nc_file_path))
exit(0)