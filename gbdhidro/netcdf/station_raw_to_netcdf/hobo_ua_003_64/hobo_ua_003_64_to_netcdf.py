# coding: utf-8

# Carrega bibliotecas de acordo com o necessario
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timezone, timedelta
from netCDF4 import num2date, date2num, stringtoarr
from gbdhidro.netcdf import util
from gbdhidro.netcdf import cf
from gbdhidro.netcdf.netcdfjson import NetCDFJSON
from gbdhidro.hobo import hobo
from cfchecker.cfchecks import main
import sys
import logging

# Versao
__version_info__ = (0, 1, 0)
__version__ = '.'.join(map(str,__version_info__))
TOOL_NAME = 'HOBO Pendant Event Data Logger (UA-003-64) to NetCDF conversion tool v.' + __version__

HERE = os.path.abspath(os.path.dirname(__file__))
#cwd = os.getcwd()

# Configura debug
DEBUG = False
DEBUG_INPUT_FILE = os.path.realpath('../../test/station_files/hobo_ua_003_64/EHP02039.csv')
DEBUG_OUTPUT = os.path.realpath('../../test/output/hobo_ua_003_64')
DEBUG_OVERWRITE = True

# Parametros default
JSON_FILE = os.path.join(HERE, 'precipitation_netcdf.json')
CONFIG_FILE = os.path.join(HERE, 'stations_info.csv')
DECIMAL = '.'
SEPARATOR = ','
ENCODING = 'utf-8'
RUN_CFCHECKS = False

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def hobo_to_netcdf(input_file, output, config_file=None, json_file=None, overwrite=False):
    """
    Converte arquivos hobo (convertidos para csv) para formato netcdf

    :param input_file:
    :param output:
    :param config_file:
    :param json_file:
    :param overwrite:
    :return:
    """

    logger.debug('Input file: {}'.format(input_file))
    logger.debug('Output: {}'.format(output))
    logger.debug('Config file: {}'.format(config_file))
    logger.debug('NetCDF file json: {}'.format(json_file))
    logger.debug('Overwrite flag: {}'.format(overwrite))

    # Se output for um diretorio, gera um nome automatico
    if os.path.isdir(output):
        file_name = os.path.splitext(os.path.basename(input_file))[0] + '.nc'
        output_file = os.path.join(output, file_name)
    else:
        output_file = output

    # Verifica se arquivo ja existe e gera erro caso flag de overwrite nao for setado
    if os.path.exists(output_file) and overwrite is False:
        raise FileExistsError('File already exist. Use -ow flag to overwrite')

    # Abre arquivo e extrai informacoes
    title, serial_number, header, details = hobo.get_info(input_file)

    #if not details:
    #    # Erro - nao tem nenhuma informacao sobre esse titulo de plot
    #    print('ERRO: arquivo sem detalhes. Arquivo deve ser exportado com detalhes para permitir verificacao')
    #    exit(ERROR_CODE)


    # Le arquivo .csv com configuracoes e informacoes adicionais das estacoes

    if os.path.exists(config_file) is False:
        raise FileNotFoundError('Config file not found {}'.format(config_file))

    cfgs = pd.read_csv(config_file)

    row = cfgs.loc[cfgs['Plot Title'] == title]    # Procura por plot tittle igual do arquivo de entrada
    if row.empty:
        # Erro - nao tem nenhuma informacao sobre esse titulo de plot
        raise AttributeError('Plot title ({}) not found in config file'.format(title))

    # Extrai informacoes importantes sobre a estacao do arquivo de configuracao
    station_id = row.iloc[0]['Codigo']
    station_sn = row.iloc[0]['Numero de serie']
    station_latitude = row.iloc[0]['Latitude [graus]']
    station_longitude = row.iloc[0]['Longitude [graus]']
    station_altitude = row.iloc[0]['Altitude [m]']
    station_datetime_col = row.iloc[0]['Coluna data/hora']
    station_gmt = int(row.iloc[0]['GMT'])
    station_uuid = row.iloc[0]['UUID']
    #station_time_resolution = row.iloc[0]['Intervalo medidas (ISO8601)']
    station_variable_col = row.iloc[0]['Coluna variavel']
    # Encontra coluna datetime de formar flexivel (procura por nome parecido)
    datetime_col = None
    for col_name in header:
        found = False
        if util.find_matches(col_name, station_datetime_col):
            datetime_col = col_name
            found = True
            break
    if not datetime_col:
        raise AttributeError('col ({}) not found'.format(station_datetime_col))

    # Encontra timezone e verifica se esta dentro do valor esperado
    gmt_hour_offset, gmt_minute_offset = util.get_gmt_offset(datetime_col)
    if station_gmt != gmt_hour_offset:
        print('Warning: found timezone (GMT{}) different from config (GMT{}). Using GMT{}.'.format(gmt_hour_offset, station_gmt, gmt_hour_offset))

    # Encontra nome de coluna de dados por semelhança
    variable_col = None
    for col_name in header:
        found = False
        if util.find_matches(col_name, station_variable_col):
            variable_col = col_name
            found = True
            break
    if not variable_col:
        raise AttributeError('col ({}) not found'.format(station_variable_col))

    # Verifica resolucao de tempo se esta dentro da esperada
    #details = hobo.process_details(details)

    # TODO: Encontrar o campo no dicionario sem ser case sensitive
    #serie = details['Details']['Series: ' + variable_col]
    #details = details['Details']
    #serie = None
    #for k, v in details.items():
    #    found = False
    #    if util.find_matches(k, ['Series:', station_variable_col]):
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
    table = hobo.get_data(input_file)

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
    first_day_str = cf.datetime2str(index_utc.iloc[0])
    last_day_str = cf.datetime2str(index_utc.iloc[-1])
    #logger.debug("Inicio e fim de medidas em UTC: {} - {}".format(first_day_str, last_day_str))

    # Gera nome do arquivo de saida se ainda nao foi definido
    if output_file is None:
        file_name = '{}_{}_{}.nc'.format(station_id, first_day_str, last_day_str)
    else:
        file_name = output_file

    nc_input_file = file_name

    # Adiciona pasta de saida no path se definido
    #if output_folder is None:
    #    nc_input_file = file_name
    #else:
    #    nc_input_file = os.path.join(output_folder, file_name)

    # Cria arquivo netCDF
    nc_file = NetCDFJSON()
    nc_file.write(nc_input_file)

    # Le arquivo json com configuracao da estrutura do netcdf
    if os.path.exists(json_file) is False:
        raise FileNotFoundError('NetCDF json file not found {}'.format(json_file))

    nc_file.load_json(json_file)
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
    #    delta = timedelta(days=1)nc_
    #else:
    #    print('Erro. Intervalo de tempo ainda nao implementada {}'.format(station_time_resolution))
    #    exit(ERROR_CODE)

    #delta = cf.period_iso8601_to_relativetime(station_time_resolution)
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
    min_time_str = cf.datetime2str(min_time)
    max_time_str = cf.datetime2str(max_time)
    time_delta = max_time - min_time
    time_delta_str = cf.timedelta2str(time_delta)
    # time resolution
    #time_resolution_str = station_time_resolution

    # Atualiza metadados
    gbd_index = nc_file.get_group('gbd_index')
    gbd_index.geospatial_lat_min = min_lat
    gbd_index.geospatial_lat_max = max_lat
    gbd_index.geospatial_lon_min = min_lon
    gbd_index.geospatial_lon_max = max_lon
    gbd_index.time_coverage_start = min_time_str
    gbd_index.time_coverage_end = max_time_str
    gbd_index.time_coverage_duration = time_delta_str
    #nc_file.rootgrp.time_coverage_resolution = time_resolution_str
    uuid = '{}/{}_{}_{}.nc'.format(station_uuid, station_id, first_day_str, last_day_str)
    gbd_index.uuid = uuid
    gbd_index.date_created = cf.datetime2str(datetime.now(timezone.utc))
    gbd_index.history = '({}) Created with {}'.format(gbd_index.date_created, TOOL_NAME)
    gbd_index.keywords = [nc_var.standard_name, nc_var.units, station_id]
    gbd_index.key_variables = 'precipitation'

    # Gera dados do grupo gbd_index
    #nc_file.rootgrp.createGroup('gbd_index')
    #nc_file.rootgrp.gbd_index.uuid = uuid
   
    
    nc_file.close()

    # Imprime resultado
    print('Input file: {}'.format(input_file))
    print('Output file: {}'.format(nc_input_file))
    print('Latitude Min/Max: {} / {}'.format(min_lat, max_lat))
    print('Longitude Min/Max: {} / {}'.format(min_lon, max_lon))
    print('Datetime (UTC) Min/Max: {} / {}'.format(min_time_str, max_time_str))
    print('Coverage duration: {}'.format(time_delta_str))
    print('Data length: {}'.format(data_len))

    #print('Resolucao: {}'.format(time_resolution_str))

    # Checa se arquivo atende padrao CF utilizando o cfchecks
    if RUN_CFCHECKS:
        print('\nRunning cfchecks')
        sys.argv = ['', nc_input_file]
        sys.exit(main())


def command_line():
    """
    Funcao para interpretacao de linha de comando
    :return:
    """

    #logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description=TOOL_NAME)
    parser.add_argument("input", type=str, help="hobo input file (.csv)", nargs='+')
    parser.add_argument('-o', '--output', type=str, help="output directory or file")
    parser.add_argument('-ow', '--overwrite', help='overwrite output files', action='store_true')
    parser.add_argument("-c", "--config", help="stations config file (.csv)")
    parser.add_argument("-n", "--netcdf", help="json file with NetCDF file information")

    args = parser.parse_args()

    if args.output is None:
        output = os.path.realpath('.')
    else:
        output = os.path.realpath(args.output)

    ow = args.overwrite

    # arquivo definido pelo usuario ou padrao
    if args.netcdf:
        json_file = os.path.realpath(args.netcdf)
    else:
        json_file = JSON_FILE

    # arquivo config definido pelo usuario ou padrao
    if args.config:
        config_file = os.path.realpath(args.config)
    else:
        config_file = CONFIG_FILE

    # loop para processar todos arquivos
    input_files = args.input
    logger.debug('Input files: {}'.format(input_files))
    for input_file in input_files:
        input_file = os.path.realpath(input_file)
        if os.path.isdir(input_file):
            continue
        else:
            hobo_to_netcdf(input_file, output,
                           config_file=config_file, json_file=json_file, overwrite=ow)


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        hobo_to_netcdf(DEBUG_INPUT_FILE, DEBUG_OUTPUT,
                       config_file=CONFIG_FILE, json_file=JSON_FILE, overwrite=DEBUG_OVERWRITE)
    else:
        command_line()
