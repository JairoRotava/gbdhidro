import pytest
import os
import subprocess

from gbdhidro.hobo import hobo

here = os.path.abspath(os.path.dirname(__file__))
DATA_FOLDER = os.path.join(here, './station_sample_files/hobo_ua_003_64')  # Diretorio com arquivos de entrada para teste
OUTPUT_FOLDER = os.path.join(here, './output/hobo_ua_003_64')  # Diretorio para salvar arquivos de saida
CONVERTER = os.path.join(here, '../station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')  # Nome do conversor a ser testado


def test_hobo_ua_003_64_convertion():
    """
    Faz um teste de conversao dos arquivo hobo. Se der algum pau ele gera um erro
    """

    # find all files in data folder
    files = []
    for path in os.listdir(DATA_FOLDER):
        full_path = os.path.join(DATA_FOLDER, path)
        if os.path.isfile(full_path):
            files.append(full_path)

    # Tenta abrir todos arquivos para ver se da algum erro
    for file in files:
        #title, serial_number, header, extra = hobo.get_info(file)
        #table = hobo.get_data(file)
        #proc_extra = hobo.process_details(extra)
        output = subprocess.run(['python', CONVERTER, '-i', file, '-d',OUTPUT_FOLDER])
        if output.returncode != 0:
            # Processo retornou erro
            assert False


    # Foi tudo ok. Lanca um True - não precisa...just in case.
    assert True




