import pandas
import re

# Tamanho maximo em linhas do da informacao extra que pode estar dentro do arquivo
MAX_EXTRA_SIZE = 500
ENCODING = 'utf-8'
DELIMITER = ','

def find_title(str_line):
    # Extrai titulo de string
    match = re.search(r'(?:Plot Title: )([^"]+)', str_line)
    if match:
        return match.group(1)
    else:
        return None


def find_serial_number(str_line):
    """
    Extrai numero de serial de string
    """
    match = re.search(r'(?:LGR S/N: |Serial Number:)(\d+)', str_line)
    if match:
        return match.group(1)
    else:
        return None


def get_info(filename, delimiter=DELIMITER, encoding=ENCODING):
    # Obtem nome das colunas
    header = list(pandas.read_csv(filename, delimiter=delimiter, header=0, skiprows=1, nrows=0, encoding=encoding))

    # Extrai titulo e informacoes extras se disponiveis
    fo = open(filename, 'rt', encoding=encoding)
    title = find_title(fo.readline())
    sn = find_serial_number(fo.readline())

    # Informacoes extras
    n_cols = len(header)
    extra = []
    for i in range(MAX_EXTRA_SIZE):
        # separa nos separadores, mas não se tiver dentro de ""
        fields = re.split(delimiter + '(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', fo.readline())
        n_fields = len(fields)
        if n_fields > n_cols:
            extra.append(''.join(fields[n_cols:]))
        elif n_fields < n_cols:
            # Provavelmente uma linha invalida. ignora
            pass
        else:
            # numero de campos é igual ao de dados. termina procura por dados extra
            break
    extra = ''.join(extra)
    fo.close()

    return title, sn, header, extra


def get_data(filename, delimiter=DELIMITER, encoding=ENCODING):
    # Extrai dados
    # Primeiro extrai o cabechalo e depois os dados pois arquivo hobo com informacaoes extra tem mais
    # colunas de dados que o header, oque quebra a conversao do pandas. Sabendo o cabacalho
    # limitamos a leitura somente nas colunas com dados e ignoramos os dados extras.
    header = pandas.read_csv(filename, delimiter=delimiter, header=0, skiprows=1, nrows=0, encoding=encoding)
    table = pandas.read_csv(filename, delimiter=delimiter, header=0, skiprows=1, encoding=encoding, usecols=header)
    return table
