import pytest
import os

from gbdhidro import hobo

here = os.path.abspath(os.path.dirname(__file__))


def test_files():
    """
    Faz um teste de conversao dos arquivo hobo. Se der algum pau ele gera um erro
    """
    files = [os.path.join(here, './data/p01.csv'), os.path.join(here, './data/p08.csv')]

    for file in files:
        title, serial_number, header, extra = hobo.get_info(file)
        table = hobo.get_data(file)
        print('Filename: ', file)
        print('Title: ', title)
        print('Serial numbeer: ', serial_number)
        print('Header: ', header)
        print('Extra: ', extra)
        print('Table: ', table)


    #assert True




