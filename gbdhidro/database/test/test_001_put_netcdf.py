import pytest
import os
import subprocess
import glob
from gbdhidro.hobo import hobo
import db_test_credentials as cr

here = os.path.abspath(os.path.dirname(__file__))

INPUT_FILES = glob.glob(os.path.realpath(os.path.join(here, './station_files/*.nc')))
OUTPUT_FOLDER = os.path.realpath(os.path.join(here, './output/database_root'))
FILE_PATH = os.path.realpath(os.path.join(here, '../put_netcdf.py'))

# sftp user
USER = '{}:{}@{}:{}'.format(cr.SFTP_USER, cr.SFTP_PASSWORD, cr.SFTP_HOSTNAME, cr.SFTP_PORT)
# Mongodb user
INDEX_USER = '{}:{}@{}:{}'.format(cr.MONGO_USER, cr.MONGO_PASSWORD, cr.MONGO_HOSTNAME, cr.MONGO_PORT)


def test_insert_netcdf():
    # Teste insercao dos arquivos
    cmd = ['python', FILE_PATH] + INPUT_FILES + ['--user', USER, '--user_index', INDEX_USER, '-ow']
    print('\nComando teste -> ' + ' '.join(cmd))
    output = subprocess.run(cmd)
    print(output.stdout)
    if output.returncode != 0:
        # Processo retornou erro
        assert False


def test_insert_overwrite():
    # Testa se ele não sobreescreve os arquivos
    cmd = ['python', FILE_PATH] + INPUT_FILES + ['--user', USER, '--user_index', INDEX_USER]
    print('\nComando teste -> ' + ' '.join(cmd))
    output = subprocess.run(cmd, stderr=None)
    if output.returncode == 0:
        # Aqui esperamos que um erro seja gerado pois arquivo ja existe. Se nao gerar error (!=0) teste falha.
        assert False




