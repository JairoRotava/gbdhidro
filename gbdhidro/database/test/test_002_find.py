import pytest
import os
import subprocess

from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))

UUID = 'gbdhidro/estacoes/eh-p05/EH-P05_20200226T190000Z_20200508T151000Z.nc'
DB_FOLDER = os.path.realpath(os.path.join(here, './database'))
DST_FOLDER = os.path.realpath(os.path.join(here, './output/get_netcdf'))
# Cria diretorio de saida
os.makedirs(DST_FOLDER, exist_ok=True)
# Caminho para executavel
EXEC_PATH = os.path.realpath(os.path.join(here, '../find.py'))


def test_get_netcdf_to_db():
    """
    Teste para recuperar arquivo do banco de dados
    """

    cmd = ['python', EXEC_PATH, '-k', 'EH-P02']
    print('\nComando teste -> ' + ' '.join(cmd))
    output = subprocess.run(cmd)
    print(output.stdout)
    if output.returncode != 0:
        # Processo retornou erro
        assert False
    else:
        assert True




