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

# In[1]:


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


# In[2]:


# Verifica se esta no jupyter. Isso altera o comportamento do codigo
IN_JUPYTER = utilconversor.isnotebook()
if IN_JUPYTER:
    DEBUG = True
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Jupyter detectado. Alterando modo de operacao para DEBUG")
else:
    DEBUG = False
    logging.basicConfig(level=logging.INFO)


# In[3]:


logger.info("Conversao para netcdf")


# In[4]:


if IN_JUPYTER:
    from PIL import Image
    get_ipython().run_line_magic('matplotlib', 'inline')
    import matplotlib.pyplot as plt


# In[5]:


# Codigo de erro utilizado no shell em caso de problema
ERROR_CODE = 1
if not IN_JUPYTER:
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
else:
    # esta dentro do jupyter, utiliza valores padroes para debug
    FILE_PATH = 'p05.csv'
    OUTPUT_FOLDER = '.'
    OUTPUT_FILE = None
    
# Arquivo com configuracao da estacao
JSON_FILE = 'p05.json'


# In[6]:


# Abre arquivo json de configuração
with open(JSON_FILE, 'r') as fp:
    json_data = json.load(fp)


# In[7]:


if IN_JUPYTER:
    display(json_data['station'])


# In[8]:


# Nome do arquivo de dados
STATION_NAME = json_data['station']['name']
# String com identificador utilizado para certificar que eh
# o arquivo da estao escolhida
STATION_ID = json_data['station']['name_match_string']
LATITUDE = json_data['station']['latitude']
LONGITUDE = json_data['station']['longitude']
ALTITUDE = json_data['station']['altitude']
IMAGE_FILE = json_data['station']['image']
DATETIME_MATCH = json_data['station']['datetime_match_string']
PRECIPITATION_MATCH = json_data['station']['precipitation_match_string']



# Seleciona encoding do arquivo
ENCODING = json_data['station']['input_file_encoding']
DECIMAL = json_data['station']['decimal_separator']
SEPARATOR = json_data['station']['column_delimiter']


# In[9]:


# Le arquivo de imagem
with open(IMAGE_FILE, "rb") as image_file:
    image_base64 = utilcf.bin2base64(image_file.read())


# In[10]:


fo = open(FILE_PATH, "r")
first_line = fo.readline()


# In[11]:


logger.debug(first_line)


# In[12]:


# Tenta encontrar 'plot title' na primeira linha para verificar se eh
# arquivo no formato esperado
if utilconversor.find_matches(first_line,[STATION_ID]):
    logger.info('Processando estacao ID: ' + STATION_NAME)
else:
    logger.info("Erro: não é arquivo da estacao" + STATION_NAME)
    


# In[13]:


# Extrai dados da aquisicao
table = pd.read_csv(fo, sep=SEPARATOR, skiprows=0, verbose=False, na_filter=True,  header=0, encoding=ENCODING, decimal=DECIMAL, warn_bad_lines=True)
fo.close()

if IN_JUPYTER:
    display(table)


# In[14]:


# Procura por coluna de datetime e variavel
date_time_col = None
precipitation_col = None
for column in table.columns:
    if utilconversor.find_matches(column,['date', 'time']):
        date_time_col = column
    if utilconversor.find_matches(column,['acum', 'chuva', 'mm']):
        precipitation_col = column

if date_time_col is None:
    logger.error('Error, nao foi encontrada coluna de data')
    exit(ERROR_CODE)
else:
    logger.info('Coluna datetime: ' + date_time_col)

if precipitation_col is None:
    logger.error('Error, nao foi encontrada coluna de precipitacao')
    exit(ERROR_CODE)
else:
    logger.info('Coluna precipitacao: ' + precipitation_col)


# In[15]:


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
logger.info("Inicio e fim de medidas em UTC: {} - {}".format(first_day_str, last_day_str))


# In[16]:


# Encontra coluna com chuva
precipitation = table[precipitation_col]

if IN_JUPYTER:
    display(precipitation)


# In[17]:


# Gera nome de arquivo de saida
#file_name = '{}_{}_{}.nc'.format(STATION_NAME, first_day_str, last_day_str)
#logger.info("Nome de arquivo de saida: {}".format(file_name))

if OUTPUT_FILE is None:
    file_name = '{}_{}_{}.nc'.format(STATION_NAME, first_day_str, last_day_str)
else:
    file_name = OUTPUT_FILE

if OUTPUT_FOLDER is None:
    nc_file_path = file_name
else:
    nc_file_path = os.path.join(OUTPUT_FOLDER, file_name)

logger.info("Nome de arquivo de saida: {}".format(file_name))


# ## Geracao de arquivo netCDF

# In[18]:


#nc_file_path = os.path.join(OUTPUT_FOLDER, file_name)
# Cria arquivo netCDF
nc_file = NetCDFJSON()
nc_file.write(nc_file_path)
# Le arquivo json com configuracao da estrutura do netcdf
nc_file.load_json('p05.json')
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

# Recupera qual o valor uilizado para valores que estao faltando
FILL_VALUE = precip._FillValue


# In[19]:


# Substitui Nan por FILL_VALUE
precipitation = precipitation.replace(np.nan, FILL_VALUE)

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

nc_serie = precipitation.to_numpy()

nc_station_name = STATION_NAME
latitude = LATITUDE
longitude = LONGITUDE
altitude = ALTITUDE

lat[:] = np.array([latitude])
lon[:] = np.array([longitude])
alt[:] = np.array([altitude])

time[:] = nc_time
time_bnds[:] = bnds

precip[:] = np.array(nc_serie)

station_name[:] = stringtoarr(nc_station_name, nameDim.size)
station_image[:] = stringtoarr(image_base64, len(image_base64))
station_image.file_name = IMAGE_FILE


# In[20]:


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


logger.info('Min/Max latitude: {}/{}'.format(min_lat,max_lat))
logger.info('Min/Max longitude: {}/{}'.format(min_lon,max_lon))
logger.info('Min/Max datetime: {}/{}'.format(min_time_str,max_time_str))
logger.info('Time duration:{}'.format(time_delta_str))
logger.info('Time resolution:{}'.format(time_resolution_str))


# In[21]:


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


# In[22]:


#nc_file.rootgrp


# In[23]:


# Visualiza dados para confirma se esta tudo ok.
# Date time deve ser linear, sem quebras abruptas
if IN_JUPYTER:
    fig, (ax0, ax1) = plt.subplots(ncols=2)
    ax0.plot(time[:])
    ax0.set_title('Date time')
    ax1.plot(precip[:])
    ax1.set_title('Variavel')
    plt.show() 

    # Mostra imagem
    image = utilcf.base642bin(station_image[:])
    print(station_image.file_name)
    im = Image.open(image)
    display(im)


# In[24]:


# Fecha e salva arquivo
nc_file.close()


# ## Dump do arquivo nc

# In[25]:


# Apresenta o dump do arquivo netcdf
# Precisa instalar: sudo apt install netcdf-bin 
if IN_JUPYTER:
    cmd = '"' + nc_file_path + '"'
    get_ipython().system('ncdump {  cmd }')


# ## Verifica se arquivo .nc atende o CF Standard

# In[26]:


# Verifica compatibilidade com CF
# Precisa instalar pip install cfchecker 
# site: https://pypi.org/project/cfchecker/
if IN_JUPYTER:
    CF_VERSION = '1.7'
    cmd = '-v ' + CF_VERSION + ' ' + '"' + nc_file_path + '"'
    get_ipython().system('cfchecks {cmd}')


# In[ ]:





# In[ ]:




