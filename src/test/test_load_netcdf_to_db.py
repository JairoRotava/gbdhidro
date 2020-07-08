import pytest
import os
import subprocess

from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))

#INPUT_FOLDER = os.path.realpath('../test/output/hobo_ua_003_64')
#OUTPUT_FOLDER = os.path.realpath('../test/output/load_netcdf_to_db/database_root')

INPUT_FOLDER = os.path.realpath(os.path.join(here, './station_sample_files/netcdf'))
OUTPUT_FOLDER = os.path.realpath(os.path.join(here, './output/load_netcdf_to_db/database_root'))
# Cria diretorio de saida
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
FILE_PATH = os.path.realpath(os.path.join(here, '../load_netcdf_to_db/load_netcdf_to_db.py'))


def test_load_netcdf_to_db():
    """
    Faz um teste de conversao dos arquivo hobo. Se der algum pau ele gera um erro
    """


    cmd = ['python', FILE_PATH, INPUT_FOLDER, OUTPUT_FOLDER, '-ow']
    output = subprocess.run(cmd)
    if output.returncode != 0:
        # Processo retornou erro
        assert False


    # Foi tudo ok. Lanca um True - não precisa...just in case.
    assert True




