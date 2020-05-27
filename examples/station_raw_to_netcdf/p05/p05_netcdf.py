# Informacoes para estacao
STATION_NAME = 'eh-p05'
# String com identificador utilizado para certificar que eh
# o arquivo da estao escolhida
STATION_ID = 'EH-P05'
LATITUDE = 10.10
LONGITUDE = 20.20

import argparse

parser = argparse.ArgumentParser(description='Converte arquivo para netCDF.')
parser.add_argument("-i", "--input", help="nome do arquivo de entrada")
parser.add_argument("-o", "--output", help="nome do arquivo de saida. Se nao for informado eh gerado automaticamente")
parser.add_argument("-d", "--directory", help="nome do diretorio de saida")
args = parser.parse_args()

# Codigo de erro enviado para bash
ERROR_CODE = 1
OUTPUT_FOLDER = args.directory
OUTPUT_FILE = args.output
INPUT_FILE = args.input

if INPUT_FILE is None:
    parser.print_help()
    exit(ERROR_CODE)
     
import pandas as pd
import numpy as np
from datetime import datetime
import re
import os

from netCDF4 import Dataset,num2date, date2num
from datetime import timezone, timedelta


from netCDF4 import Dataset,num2date, date2num, stringtoarr
import json

from netcdfjson import NetCDFJSON
import utilconversor
import utilcf

# Nome do arquivo de dados
FILE_PATH = INPUT_FILE

# Seleciona encoding do arquivo
ENCODING = 'utf-8'
DECIMAL = '.'
SEPARATOR = ','

fo = open(FILE_PATH, "r")
first_line = fo.readline()

# Tenta encontrar 'plot title' na primeira linha para verificar se eh
# arquivo no formato esperado
if utilconversor.find_matches(first_line,[STATION_ID]):
    print('Processando estacao ID: ' + STATION_ID)
else:
    print("Erro: nao eh arquivo da estacao" + STATION_ID)
    exit(ERROR_CODE)
    
# Extrai dados da aquisicao
table = pd.read_csv(fo, sep=',', skiprows=0, verbose=False, na_filter=True,  header=0, encoding=ENCODING, decimal=DECIMAL, warn_bad_lines=True)
fo.close()
table

# Procura por coluna de datetime e variavel
date_time_col = None
precipitation_col = None
for column in table.columns:
    if utilconversor.find_matches(column,['date', 'time']):
        date_time_col = column
    if utilconversor.find_matches(column,['acum', 'chuva', 'mm']):
        precipitation_col = column

if date_time_col is None:
    print('Error, nao foi encontrada coluna de data')
    exit(ERROR_CODE)
else:
    print('Coluna datetime: ' + date_time_col)


if precipitation_col is None:
    print('Error, nao foi encontrada coluna de precipitacao')
    exit(ERROR_CODE)
else:
    print('Coluna precipitacao: ' + precipitation_col)
    
# Processa datetime para incluir timezone
date_str = table[date_time_col]
date_time = pd.to_datetime(date_str, format='%m/%d/%y %I:%M:%S %p')
# extrai informacao de gmt
gmt_hour_offset, gmt_minute_offset = utilconversor.get_gmt_offset(date_time.name)
tzinfo=timezone(timedelta(hours=gmt_hour_offset, minutes=gmt_minute_offset))
# gera os indices com informacao de fuso horarios incluido
index = date_time.dt.tz_localize(tzinfo)
# converte para UTC
index_utc = index.dt.tz_convert('UTC')
first_day_str = utilcf.datetime2str(index_utc.iloc[0])
last_day_str = utilcf.datetime2str(index_utc.iloc[-1])
print("Inicio e fim de medidas em UTC: {} - {}".format(first_day_str, last_day_str))

# Encontra coluna com chuva
precipitation = table[precipitation_col]

# Gera nome de arquivo de saida
if OUTPUT_FILE is None:
    file_name = '{}_{}_{}.nc'.format(STATION_ID, first_day_str, last_day_str)
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
nc_file.load_json('eh-p05.json')
nc_file.create_from_json()

# pega handlers para dimensoes
timeDim = nc_file.get_dimension('time')
nameDim = nc_file.get_dimension('name_strlen')
# pega handlers para variaveis
time = nc_file.get_variable('time')
time_bnds = nc_file.get_variable('time_bnds')
lat = nc_file.get_variable('lat')
lon = nc_file.get_variable('lon')
station_name = nc_file.get_variable('station_name')
precip = nc_file.get_variable('precipitation')

# Recupera qual o valor uilizado para valores que estao faltando
FILL_VALUE = precip._FillValue

# Substitui Nan por FILL_VALUE
precipitation = precipitation.replace(np.nan, FILL_VALUE)

# Seta variaveis
nc_time = index_utc.to_numpy()
nc_time = date2num(nc_time,units=time.units,calendar=time.calendar)
# Como a precipitacao e o acumulado entre a ultima medida e a atual
# eh necessario informar isso atraves dos bounds de tempo, ou seja,
# os valores inferioes e superiores respectivos ao limite do eixo de temp0
# O bound superior e o mesmo que o horario da medids
nc_superior_bound_time = nc_time
# bound inferior e o horario da ultima medida
nc_inferior_bound_time = np.roll(nc_superior_bound_time,1)
# a primeira medida nao tem medida anterior, por isso seta para o mesmo valor
nc_inferior_bound_time[0] = nc_superior_bound_time[0]
# combina bound inferior com bound superior
bnds = np.stack((nc_inferior_bound_time, nc_superior_bound_time), axis=-1)

nc_serie = precipitation.to_numpy()

nc_station_name = STATION_NAME
latitude = LATITUDE
longitude = LONGITUDE

lat[:] = np.array([latitude])
lon[:] = np.array([longitude])
time[:] = nc_time
time_bnds[:] = bnds

precip[:] = np.array(nc_serie)

station_name[:] = stringtoarr(nc_station_name, nameDim.size)

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
time1 = num2date(time[1], units=time.units, calendar=time.calendar)
time0 = num2date(time[0], units=time.units, calendar=time.calendar)
time_resolution = time1 - time0
time_resolution_str = utilcf.timedelta2str(time_resolution)

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

print('Arquivo de saida: {}'.format(nc_file_path))
# finalizado com sucesso
exit(0)

