#!/usr/bin/env python
# coding: utf-8

# # Desenvolvimento de conversao arquivo h01 para netcdf
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
# Pega path absoluto deste arquivo
here = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
JSON_FILE = os.path.join(here, 'p06.json')
IMAGE_FILE = os.path.join(here, 'p06.jpg')
FILE_PATH_DEBUG = '../../input/p06/p06.csv'
OUTPUT_FOLDER_DEBUG = '../../output'
OUTPUT_FILE_DEBUG = None
GMT = -3
DECIMAL = '.'
SEPARATOR = ','
VAR_LIST = {
        'datetime': {'match': ['Date', 'Time'], 'pandas_col': None},
        'precipitation': {'netcdf_var': 'precipitation', 'match': ['Chuva', 'mm'], 'pandas_col': None},
    }



# Codigo de erro utilizado no shell em caso de problema
ERROR_CODE = 1
logger = logging.getLogger(__name__)

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

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


# Abre arquivo json de configuração
with open(JSON_FILE, 'r') as fp:
    json_data = json.load(fp)

STATION_NAME = json_data['station']['name']
STATION_NAME_MATCH = json_data['station']['name_match_string']
LATITUDE = json_data['station']['latitude']
LONGITUDE = json_data['station']['longitude']
ALTITUDE = json_data['station']['altitude']
ENCODING = json_data['station']['input_file_encoding']

#logger.debug("Conversao para estacao {}".format(STATION_NAME))

# Le arquivo de imagem
with open(IMAGE_FILE, "rb") as image_file:
    image_base64 = utilcf.bin2base64(image_file.read())

# Le somente o cabecalho para ver se eh o arquivo procurado
fo = open(FILE_PATH, "r", encoding=ENCODING)
first_line = fo.readline()
second_line = fo.readline()
fo.close()

# Verifica se tem numero de serie correto
# Procura por alguns termos especifcos para verificar se o arquivo
# esta dentro do esperado
print('Conversor estacao {} para netcdf'.format(STATION_NAME))
if not utilconversor.find_matches(second_line, STATION_NAME_MATCH):
    print('Erro ao detectar identificador, arquivo fora do padrao esperado')
    exit(ERROR_CODE)

# Le cabecalho da tabela
# Estou abrindo e fechando o arquivo pq fica mais facil gerenciar. Não é o mais eficiente
#fo = open(FILE_PATH, "r", encoding=ENCODING)
# pula as primeiras 14 linhas
#for i in range(14):
#    fo.readline()
#first_line = fo.readline()
#fo.readline()
#second_line = fo.readline()
#first_line_sep = first_line.split()
#second_line_sep = second_line.split()
#header = ['Date', 'Time'] + first_line_sep
#for l1, l2 in zip(first_line_sep, second_line_sep):
#    header.append("{} {}".format(l1.strip(),l2.strip()))
#fo.close()

# Extrai dados da aquisicao
table = pd.read_csv(FILE_PATH, sep=SEPARATOR, skiprows=1, verbose=False, na_filter=True, header=0, encoding=ENCODING, decimal=DECIMAL, warn_bad_lines=True, dtype=str)
#table.columns = header
#print(table)

for key, value in VAR_LIST.items():
    found = False
    for column in table.columns:
        if utilconversor.find_matches(column, value['match']):
            value['pandas_col'] = column
            found = True
            break
    if not found:
        print('Erro, nao foi encontrada coluna {}'.format(key))
        exit(ERROR_CODE)

# Filtra linhas incorretas
#bad_rows = []
#for index, row in table.iterrows():
#    date = row[VAR_LIST["date"]["pandas_col"]]
#    time = row[VAR_LIST["time"]["pandas_col"]]
    # Apaga estes elementos da lista pois ja foram utilizados
    # evita atrapalhar algm codigo mais adiante
    #del var_list['date']
    #del var_list['time']
    
#    date_str = '{} {}'.format(date, time)
#    try:
#        date_time = pd.to_datetime(date_str, format='%d/%m/%Y %H:%M:%S')
#    except:
#        bad_rows.append(index)

#if bad_rows:
#    logger.debug('Foram removidas {} linhas com dados invalidos'.format(len(bad_rows)))
#    table = table.drop(bad_rows)


#date = table[VAR_LIST["date"]["pandas_col"]]
#time = table[VAR_LIST["time"]["pandas_col"]]
date_str = table[VAR_LIST['datetime']['pandas_col']]
date_time = pd.to_datetime(date_str, format='%m/%d/%y %I:%M:%S %p')


# Processa datetime para incluir timezone
gmt_hour_offset, gmt_minute_offset = utilconversor.get_gmt_offset(date_time.name)
#gmt_hour_offset = GMT
#gmt_minute_offset = 0

# Erro de gmt.
# TODO: Verificar como lidar com isso
if gmt_hour_offset != GMT:
    print('Erro: GMT diferente do esperado {} != {}'.format(gmt_hour_offset, GMT))
    exit(ERROR_CODE)

tzinfo=timezone(timedelta(hours=gmt_hour_offset, minutes=gmt_minute_offset))
# gera os indices com informacao de fuso horarios incluido
index = date_time.dt.tz_localize(tzinfo)
# converte para UTC
index_utc = index.dt.tz_convert('UTC')
first_day_str = utilcf.datetime2str(index_utc.iloc[0])
last_day_str = utilcf.datetime2str(index_utc.iloc[-1])
logger.debug("Inicio e fim de medidas em UTC: {} - {}".format(first_day_str, last_day_str))

if OUTPUT_FILE is None:
    file_name = '{}_{}_{}.nc'.format(STATION_NAME, first_day_str, last_day_str)
else:
    file_name = OUTPUT_FILE

if OUTPUT_FOLDER is None:
    nc_file_path = file_name
else:
    nc_file_path = os.path.join(OUTPUT_FOLDER, file_name)

logger.info("Nome de arquivo de saida: {}".format(file_name))


# Insere lista de variaveis no netcdf
# Pega colunas de dados (exclui data e hora)
DATA_LIST = VAR_LIST
del DATA_LIST['datetime']

# Convert string to floats
#table[DATA_LIST['precipitation']['pandas_col']] = table[DATA_LIST['precipitation']["pandas_col"]].str.replace(',', '').astype(float)
#table[DATA_LIST['sediment']['pandas_col']] = table[DATA_LIST['sediment']["pandas_col"]].str.replace(',', '').astype(float)
#table[DATA_LIST['level']['pandas_col']] = table[DATA_LIST['level']["pandas_col"]].str.replace(',', '').astype(float)
#table[DATA_LIST['battery']['pandas_col']] = table[DATA_LIST['battery']["pandas_col"]].str.replace(',', '').astype(float)

# ## Geracao de arquivo netCDF

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
#precip = nc_file.get_variable('precipitation')
station_image = nc_file.get_variable('station_image')

for key, value in DATA_LIST.items():
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

logger.debug('Min/Max latitude: {}/{}'.format(min_lat,max_lat))
logger.debug('Min/Max longitude: {}/{}'.format(min_lon,max_lon))
logger.debug('Min/Max datetime: {}/{}'.format(min_time_str,max_time_str))
logger.debug('Time duration:{}'.format(time_delta_str))
logger.debug('Time resolution:{}'.format(time_resolution_str))

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

# Sai com codigo zero - sucesso
print('Arquivo de saida: {}'.format(nc_file_path))
exit(0)