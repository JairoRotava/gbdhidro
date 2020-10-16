import pytest
import os
import subprocess

from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))

INPUT_FOLDER = os.path.realpath(os.path.join(here, './station_files/p02/p02.nc'))
OUTPUT_FOLDER = os.path.realpath(os.path.join(here, './output/database_root'))
# Cria diretorio de saida
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
FILE_PATH = os.path.realpath(os.path.join(here, '../insert_netcdf.py'))



def test_insert_netcdf():
    """
    Faz um teste de conversao dos arquivo hobo. Se der algum pau ele gera um erro
    """


    cmd = ['python', FILE_PATH, INPUT_FOLDER, '-db', OUTPUT_FOLDER, '-ow']
    print('\nComando teste -> ' + ' '.join(cmd))
    output = subprocess.run(cmd)
    print(output.stdout)
    if output.returncode != 0:
        # Processo retornou erro
        assert False
    else:
        assert True




