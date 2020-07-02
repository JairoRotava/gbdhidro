import pytest
import os
import subprocess

from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = os.path.join(here, './station_sample_files')
OUTPUT_FOLDER = os.path.join(here, './output/convert_batch_netcdf')
FILE_PATH = os.path.join(here, '../convert_batch_netcdf/convert_to_netcdf.py')


def test_convert_batch_netcdf():
    """
    Faz um teste de conversao dos arquivo hobo. Se der algum pau ele gera um erro
    """


    cmd = ['python', FILE_PATH, '-i', INPUT_FOLDER, '-o', OUTPUT_FOLDER, '-ow']
    output = subprocess.run(cmd)
    if output.returncode != 0:
        # Processo retornou erro
        assert False


    # Foi tudo ok. Lanca um True - não precisa...just in case.
    assert True




