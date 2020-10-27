# Converte os arquivos de entrada e salva no diretorio de saida mantendo a mesma estrutura de diretorio

# Formato do diretorio de saida
# O arquivo é salvo no caminho definido pelo atributo global database_uuid no NetCDF. Sem esse atributo o
# metodo nao sabe onde colocar o arquivo. O atributo database_uuid deve ser um path de arquivo valido. A recomendacao
# é utilizar somente letras minusculas, evitar espacos e caracteres especiais e acentos. O uuid deve ser unico no universo,
# nao pode se repetir. Isso pode ser conseguido facilmente utilizando instituicao, projeto, sub projeto e outros valores.
# Exemplos:
# database_uuid = /ufpel/gbdhidro/estacao/eh-p01/eh-p01_fev2010-fev2020
# database_uuid = /ufpel/gbdhidro/estacao/precipitacao/eh-p01/eh-p01_fev2010-fev2020
# database_uuid = /ufpel/gbdhidro/estacao/processados/eh-p01/eh-p01_fev2010-fev2020
# o uuid é uam forma bastante flexivel para organizar os dados da forma que for considerada mais conveniente pelo
# usuario. Lembrar que ter isso de forma organizada ajuda em encontrar o arquivo porsterioemente.
# a parte final sera o nome do arquivo na estrutura de difetorio e recomendasse colocar o ID da estacao, e periodo dos
# dados para facilitar uma eventual busca manual dos dados.
# gbd/<projeto>/<fonte>/<id>/arquivos onde:
# por exemplo:
# gbd/estacoes/observacionais/EH-P02/<projeto>_<source>_<id>_20200101T010101Z_20200202T020202Z
# As informações de <projeto> <fonte> e <id> devem estra armazenadas em algum arquico e apartir do ID do arquivo
# deve ser enviado automaticamnete para o diretorio correot. Pensar melhor como fazer isso. Os arquivos nc devem ter
# o projeto e a fonte dos dados internamente
#
# Formato do rquivo: ID_Datainicail_datafinal
# O ID deve ser único dentro de um projeto/fonte
#
# root/instituicao/projeto/fonte/id
# institution/project/source/id
# Cada arquivo. nc deve fornecer um path_id que como deve ser salvo os arquivos automaticamente na base da dados.
# O formato é aberto ao dono do arquivo, mas deve ser com letras minusculas, e ser um nome de diretorio valido.
# id deve ser único
# id = gbdhidro/estacoes/ehp01/ehp01_2000123123_23042304
##


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
import pysftp
import tempfile
import shutil
import re

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = os.path.realpath('./test/output/hobo_ua_003_64')
OUTPUT_FOLDER = os.path.realpath('../test/output/load_netcdf_to_db/database_root')
CONVERTER_LIST = [os.path.join(HERE, '../station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')]
FILE_OVERWRITE = True
ERROR_CODE = 1
LOG_FILE = 'upload.log'
# Mongodb info
#MONGODB_URL = '127.0.0.1:27017'
#DATABASE = 'gbdhidro'
#COLLECTION = 'index'
# Docker mongodb
MONGODB_URL = 'localhost:17017'
DATABASE = 'gbdhidro'
COLLECTION = 'index'
USER = 'anonymous'
PASS = 'guest'

# mongo
MONGO_HOSTNAME = 'localhost'
MONGO_USER = 'anonymous'
MONGO_PASSWORD = 'guest'
MONGO_PORT = 17017
MONGO_DATABASE = 'gbdhidro'
MONGO_COLLECTION = 'index'


# sftp
SFTP_HOSTNAME = 'localhost'
SFTP_USER = 'anonymous'
SFTP_PASSWORD = 'guest'
SFTP_PORT = 2222
SFTP_ROOT = 'gbdserver'

DEFAULT_SFTP_ROOT = 'gbdserver'
DEFAULT_MONGO_DATABASE = 'gbdhidro'


DATABASE_DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'gbdroot')

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


# TODO: precisa verificar como fazer quando o arquivo é sobreescrito, e como atualizar isso no index
# mudar para put o nome da funcao


#def get_input_files(folder):
#    """
#    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
#    """
#    return glob.glob(os.path.join(folder, '**/*.*'), recursive=True)


#insert_entry_db(metadata, index_cred['hostname'], index_cred['port'], index_cred['user'], index_cred['password'])
def insert_entry_db(entry, hostname, port, user, password, database):
    client = MongoClient(hostname, port=port, username=user, password=password)
    gbd = client[database]
    index = gbd[COLLECTION]
    index.insert_one(entry)
    client.close()


# Converte os atribuito globais do NetCDF para formatos mais adequados do MongoDB
def convert_netcdf_attributes_to_mongo(dataset):
    attributes = dataset.__dict__.copy()
    d = {}
    for key, value in attributes.items():
        # Convert numpy type to native python
        if type(value).__module__ == numpy.__name__:
            value = value.item()
        # Convert time converage start/end to native mongodb
        if key == 'time_coverage_start':
            # value = datetime.datetime.strptime(value, '%Y%m%dT%H%M%SZ')
            value = cf.iso8601_to_datetime(value)
        if key == 'time_coverage_end':
            value = cf.iso8601_to_datetime(value)
        if key == 'time_coverage_duration':
            # Nao tem tipo de intervalo de tempo definido no mongodb. Guardar o intervalor em segundos
            # Calcula a partir da data de incio e fim pois e mais facil dq converter valor inserido
            # no netcdf. Nao sei direito com lidar com isso ainda
            start = cf.iso8601_to_datetime(attributes['time_coverage_start'])
            end = cf.iso8601_to_datetime(attributes['time_coverage_end'])
            interval = (end - start).total_seconds()
            value = int(interval)

        d.update({key: value})
    return d


def save_sftp(file, folder, hostname, port, username, password):
    # Envia pelo sftp
    # TODO: por hora ignora o key do host. Verificar como fazer nesse caso para evitar o man in the middle
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=hostname, username=username, password=password, port=port,
                           cnopts=cnopts) as sftp:
        sftp.makedirs(folder)
        sftp.chdir(folder)
        sftp.put(file)
    return


def put_netcdf(input_file, index_cred, ftp_cred, overwrite=False):
    logger.debug('Input file: ', input_file)
    logger.debug('Index credential: {}'.format(index_cred))
    logger.debug('SFTP credential: {}'.format(ftp_cred))

    with Dataset(input_file, 'r') as rootgrp:

        if not hasattr(rootgrp, 'database_uuid'):
            raise AttributeError('ERROR: database_uuid global attribute not found in netcdf file')

        try:
            metadata = convert_netcdf_attributes_to_mongo(rootgrp)
        except:
            raise AttributeError('ERROR: converting NetCDF metadata')

        relative_folder = os.path.dirname(rootgrp.database_uuid)

        # Gera nome e pasta de destino a partir do uuid. Deixa tudo em lowercase para manter padrao
        # TODO: Checar se nomes sao validos para armazenar no sftp
        relative_folder = os.path.dirname(rootgrp.database_uuid).lower()
        dst_file = os.path.basename(rootgrp.database_uuid).lower()

        tmpdir = tempfile.mkdtemp()
        dst_file_path = os.path.join(tmpdir, dst_file + '.zip')

        with zipfile.ZipFile(dst_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(input_file, os.path.basename(input_file))

        save_sftp(dst_file_path, ftp_cred['root'] + '/' + relative_folder, ftp_cred['hostname'], ftp_cred['port'],
                  ftp_cred['user'], ftp_cred['password'])
        shutil.rmtree(tmpdir)

        # Adiciona no index do mongodb
        insert_entry_db(metadata, index_cred['hostname'], index_cred['port'], index_cred['user'],
                        index_cred['password'], index_cred['database'])


def command_line():
    TOOL_NAME = 'Insert a netcdf file to the database'
    parser = argparse.ArgumentParser(description=TOOL_NAME)
    parser.add_argument("input", type=str, help="netcdf input file (.nc)", nargs='+')
    parser.add_argument("--user", type=str, help="files credential user:password@host:port/root")
    parser.add_argument("--user_index", type=str, help="index credential user:password@host:port")
    parser.add_argument('-ow', '--overwrite', help='overwrite output files', action='store_true')
    args = parser.parse_args()

    # Credenciais para sftp
    if args.user is None:
        sftp = {
            'user': SFTP_USER,
            'hostname': SFTP_HOSTNAME,
            'password': SFTP_PASSWORD,
            'port': SFTP_PORT,
            'root': SFTP_ROOT
        }
    else:
        # Interpreta user@hostname:port
        # regex = "((?P<user>\S+)@)?(?P<hostname>[^:]+)(:(?P<port>\d+))?"
        # BUG: existe um problema com isso, pois se o password tiver @/: vai dar pau. Nesse caso user e pass precisam ser
        # enconded (SEI LA OQUE SIGNIFICA ISSO) RESOLVER NO FUTURO
        # 'user:pass@hostname:port/path'
        regex = "(((?P<user>[^:@]+)(:(?P<password>[^@]+))?)@)?(?P<hostname>[^:]+)(:(?P<port>[^/]+))?(/(?P<path>.+))?"
        pattern = re.compile(regex)
        m = pattern.match(args.user)
        sftp = {
            'user': m.group('user'),
            'hostname': m.group('hostname'),
            'port': int(m.group('port')),
            'password': m.group('password'),
            'root': m.group('path')
        }

    # Use default root is not defined
    if sftp['root'] is None:
        sftp['root'] = DEFAULT_SFTP_ROOT

    # TODO: pedir pela senha no comando de linha. Isso é importante para permitir chamada segura sem a senha
    # exposta na linha de comando
    if sftp['password'] is None:
        raise ValueError('Senha para SFTP não declarada. TODO:Falta implementar')


    # Credenciais para index/Mongo
    if args.user_index is None:
        mongo = {
            'user': MONGO_USER,
            'hostname': MONGO_HOSTNAME,
            'port': MONGO_PORT,
            'password': MONGO_PASSWORD
        }
    else:
        #regex = "((?P<user>\S+)@)?(?P<hostname>[^:]+)(:(?P<port>\d+))?"
        # 'user:pass@hostname:port/path'
        regex = "(((?P<user>[^:@]+)(:(?P<password>[^@]+))?)@)?(?P<hostname>[^:]+)(:(?P<port>[^/]+))?(/(?P<path>.+))?"
        pattern = re.compile(regex)
        m = pattern.match(args.user_index)
        mongo = {
            'user': m.group('user'),
            'hostname': m.group('hostname'),
            'port': int(m.group('port')),
            'password': m.group('password'),
            'database': m.group('path')
        }

    if mongo['database'] is None:
        mongo['database'] = DEFAULT_MONGO_DATABASE

    # TODO: pedir pela senha no comando de linha. Isso é importante para permitir chamada segura sem a senha
    # exposta na linha de comando

    if mongo['password'] is None:
        raise ValueError('Senha para index não declarada. TODO:Falta implementar')

    overwrite = args.overwrite

    input_files = args.input

    #print('MongoDB information:')
    #print('  hostname: {}'.format(mongo['hostname']))
    #print('  database: {}'.format(MONGO_DATABASE))
    #print('  colection: {}'.format(MONGO_COLLECTION))

    logger.debug('Input files: {}'.format(input_files))
    for input_file in input_files:
        input_file = os.path.realpath(input_file)
        if os.path.isdir(input_file):
            # ignora diretorios
            continue
        else:
            print(input_file)
            put_netcdf(input_file, mongo, sftp, overwrite)


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        print('WARNING: Debug mode')
        in_folder = os.path.realpath(INPUT_FOLDER)
        out_folder = os.path.realpath(OUTPUT_FOLDER)
        overwrite = FILE_OVERWRITE
        put_netcdf(in_folder, out_folder, overwrite)
    else:
        command_line()
