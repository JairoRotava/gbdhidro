# Insere arquivo netcdf no gbdserver

import argparse
import logging
import os
from netCDF4 import Dataset
import zipfile
from pymongo import MongoClient
from gbdhidro.netcdf import cf
import numpy
import pysftp
import tempfile
import shutil
import re

DEFAULT_MONGO_DATABASE = 'gbdhidro'
DEFAULT_MONGO_COLLECTION = 'index'
DEFAULT_MONGO_PORT = 27017

DEFAULT_SFTP_PORT = 22
DEFAULT_SFTP_ROOT = 'gbdserver'


# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


# TODO: precisa verificar como fazer quando o arquivo é sobreescrito, e como atualizar isso no index


#insert_entry_db(metadata, index_cred['hostname'], index_cred['port'], index_cred['user'], index_cred['password'])
def insert_entry_db(entry, hostname, port, user, password, database):
    client = MongoClient(hostname, port=port, username=user, password=password)
    gbd = client[database]
    index = gbd[DEFAULT_MONGO_COLLECTION]
    # TODO: ver como utilizar entrada unique uuid - database_uuid é o padrão? Acho estranho isso
    uuid = entry['database_uuid']
    filter = {'database_uuid': uuid}
    # Substitui ou insere novo parametro.
    index.find_one_and_replace(filter, entry, upsert=True)
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


def save_sftp(file, folder, hostname, port, username, password, overwrite=False):
    # Envia pelo sftp
    # TODO: por hora ignora o key do host. Verificar como fazer nesse caso para evitar o man in the middle
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=hostname, username=username, password=password, port=port,
                           cnopts=cnopts) as sftp:
        if not overwrite:
            if sftp.exists(os.path.join(folder, os.path.basename(file))):
                raise FileExistsError('Arquivo ja existe no banco de dados.')

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




        # Gera nome e pasta de destino a partir do uuid. Deixa tudo em lowercase para manter padrao
        # TODO: Checar se nomes sao validos para armazenar no sftp
        relative_folder = os.path.dirname(rootgrp.database_uuid).lower()
        dst_file = os.path.basename(rootgrp.database_uuid).lower()

        # Comprime arquivo e envia pelo sftp
        tmpdir = tempfile.mkdtemp()
        dst_file_path = os.path.join(tmpdir, dst_file + '.zip')
        with zipfile.ZipFile(dst_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(input_file, os.path.basename(input_file))
        save_sftp(dst_file_path, ftp_cred['root'] + '/' + relative_folder, ftp_cred['hostname'], ftp_cred['port'],
                  ftp_cred['user'], ftp_cred['password'], overwrite=overwrite)
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
        raise ValueError('credencial arquivos não fornecidda')
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

    if sftp['port'] is None:
        sftp['port'] = DEFAULT_SFTP_PORT


    # TODO: pedir pela senha no comando de linha. Isso é importante para permitir chamada segura sem a senha
    # exposta na linha de comando
    if sftp['password'] is None:
        raise ValueError('Senha para SFTP não declarada. TODO:Falta implementar')

    # Credenciais para index/Mongo
    if args.user_index is None:
        raise ValueError('credencial index não fornecidda')
    else:
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
    if mongo['port'] is None:
        mongo['port'] = DEFAULT_MONGO_PORT

    if mongo['database'] is None:
        mongo['database'] = DEFAULT_MONGO_DATABASE

    if mongo['password'] is None:
        # TODO: pedir pela senha no comando de linha. Isso é importante para permitir chamada segura sem a senha
        # exposta na linha de comando
        raise ValueError('Senha para index não declarada. TODO:Falta implementar')

    overwrite = args.overwrite

    input_files = args.input

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
    command_line()
