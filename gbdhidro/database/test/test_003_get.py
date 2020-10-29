import pytest
import os
import subprocess
import db_test_credentials as cr


here = os.path.abspath(os.path.dirname(__file__))
UUID = 'gbdhidro/estacoes/eh-p02/eh-p02_20191212t150000z_20200226t200800z.nc'
DST_FOLDER = os.path.realpath(os.path.join(here, './output/get'))
os.makedirs(DST_FOLDER, exist_ok=True)
EXEC_PATH = os.path.realpath(os.path.join(here, '../get.py'))
USER = '{}:{}@{}:{}/{}'.format(cr.SFTP_USER, cr.SFTP_PASSWORD, cr.SFTP_HOSTNAME, cr.SFTP_PORT, cr.SFTP_ROOT)


def test_get_netcdf_to_db():
    """
    Teste para recuperar arquivo do banco de dados
    """

    cmd = ['python', EXEC_PATH, UUID, '--url', USER,  '-dst', DST_FOLDER, '-ow']
    print('\nComando teste -> ' + ' '.join(cmd))
    output = subprocess.run(cmd)
    print(output.stdout)
    if output.returncode != 0:
        # Processo retornou erro
        assert False
    else:
        assert True




