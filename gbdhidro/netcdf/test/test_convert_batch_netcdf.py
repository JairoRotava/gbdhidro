import pytest
import os
import subprocess

from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = os.path.join(here, './station_files')
OUTPUT_FOLDER = os.path.join(here, './output/convert_batch_netcdf')
# Cria diretorio de saida
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
FILE_PATH = os.path.join(here, '../convert_batch_netcdf.py')


def test_convert_batch_netcdf():
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




