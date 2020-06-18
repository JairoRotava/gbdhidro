import pytest
import os

from gbdhidro.hobo import hobo




def test_files():
    """
    Faz um teste de conversao dos arquivo hobo. Se der algum pau ele gera um erro
    """

    # TODO: carregar automaticamente arquivos do diretorio data
    here = os.path.abspath(os.path.dirname(__file__))
    DATA_FOLDER = os.path.join(here, './data')

    # find all files in data folder
    files = []
    for path in os.listdir(DATA_FOLDER):
        full_path = os.path.join(DATA_FOLDER, path)
        if os.path.isfile(full_path):
            files.append(full_path)

    # Tenta abrir todos arquivos para ver se da algum erro
    for file in files:
        title, serial_number, header, extra = hobo.get_info(file)
        table = hobo.get_data(file)
        proc_extra = hobo.process_details(extra)


    # Foi tudo ok. Lanca um True - não precisa...just in case.
    assert True




