import pytest
import os
import subprocess
import db_test_credentials as cr


from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))

UUID = 'gbdhidro/estacoes/eh-p02/eh-p02_20191212t150000z_20200226t200800z.nc'
#DB_FOLDER = os.path.realpath(os.path.join(here, './database'))
DST_FOLDER = os.path.realpath(os.path.join(here, './output/get_netcdf'))
# Cria diretorio de saida
os.makedirs(DST_FOLDER, exist_ok=True)
# Caminho para executavel
EXEC_PATH = os.path.realpath(os.path.join(here, '../get.py'))
#USER = 'foo@localhost:2222'
USER = '{}@{}:{}'.format(cr.SFTP_USER, cr.SFTP_HOSTNAME, cr.SFTP_PORT)
PASSWORD = cr.SFTP_PASSWORD
ROOT = cr.SFTP_ROOT


#SFTP_USER = 'sftp_user'
#SFTP_HOSTNAME = 'localhost'
#SFTP_PASSWORD = 'sftp_password'
#SFTP_PORT = 2222
#SFTP_ROOT = 'gbdserver'



def test_get_netcdf_to_db():
    """
    Teste para recuperar arquivo do banco de dados
    """

    cmd = ['python', EXEC_PATH, USER,  UUID, '-p', PASSWORD, '-r', ROOT, '-dst', DST_FOLDER, '-ow']
    print('\nComando teste -> ' + ' '.join(cmd))
    output = subprocess.run(cmd)
    print(output.stdout)
    if output.returncode != 0:
        # Processo retornou erro
        assert False
    else:
        assert True




