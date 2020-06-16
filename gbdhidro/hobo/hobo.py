import pandas
import re

# Tamanho maximo em linhas do da informacao extra que pode estar dentro do arquivo
_MAX_EXTRA_SIZE = 500
_ENCODING = 'utf-8'
_DELIMITER = ','


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


def get_info(filename, delimiter=_DELIMITER, encoding=_ENCODING):
    """
    Extrai detalhes da aquisicao. O arquivo deve ser exportado
    no hoboware com a opcao de detalhes ativada, caso contrario retorna
    valor vazio
    """
    # Obtem nome das colunas
    header = list(pandas.read_csv(filename, delimiter=delimiter, header=0, skiprows=1, nrows=0, encoding=encoding))

    # Extrai titulo e informacoes extras se disponiveis
    fo = open(filename, 'rt', encoding=encoding)
    title = find_title(fo.readline())
    sn = find_serial_number(fo.readline())

    # Informacoes extras
    n_cols = len(header)
    extra = []
    for i in range(_MAX_EXTRA_SIZE):
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


def get_data(filename, delimiter=_DELIMITER, encoding=_ENCODING):
    """
    Retorna tabela pandas com os valores da aquisicao
    """
    # Extrai dados
    # Primeiro extrai o cabechalo e depois os dados pois arquivo hobo com informacaoes extra tem mais
    # colunas de dados que o header, oque quebra a conversao do pandas. Sabendo o cabacalho
    # limitamos a leitura somente nas colunas com dados e ignoramos os dados extras.
    header = pandas.read_csv(filename, delimiter=delimiter, header=0, skiprows=1, nrows=0, encoding=encoding)
    table = pandas.read_csv(filename, delimiter=delimiter, header=0, skiprows=1, encoding=encoding, usecols=header)
    return table


def process_data(text):
    levels = []
    levels.append(['Details'])
    levels.append(['Series:', 'Event Type:'])
    levels.append(['Devices', 'Deployment Info', 'Series Statistics', 'Filter Parameters'])
    levels.append(['Device Info'])
    # teste = re.split(r'[\n](?=Details|Series: |Event Type: )',extra)
    # r'(?:Series:|Event Type:).+?[\n](?=Series:|Event Type:|$)'
    return _get_all_groups(text, levels)


def _get_group(text, level):
    regex1 = '(?:'
    regex2 = '.+?[\n](?='
    first = True
    for m in level:
        if not first:
            regex1 += '|'
            regex2 += '|'
        else:
            first = False
        regex1 += m
        regex2 += m

    regex1 += ')'
    regex2 += '|$)'
    regex = regex1 + regex2
    match = re.compile(regex, re.S)
    return match.findall(text)


def _text_to_dict(text):
    fields = text.split('\n')
    d = {}
    for f in fields:
        s = f.split(':', 1)
        if len(s) == 2:
            d.update({s[0].strip(): s[1].strip()})
    return d


def _get_all_groups(text, levels, level_number=0):
    n_levels = len(levels)
    groups = []
    temp = _get_group(text, levels[level_number])

    output = {}
    level_number += 1
    for l in temp:
        [key, val] = l.split("\n", 1)
        new_val = None
        if level_number < n_levels:
            new_val = _get_all_groups(val, levels, level_number)
        if new_val:
            val = new_val
        else:
            val = _text_to_dict(val)

        output.update({key: val})
    return output


# Teste/Desenvolvimento do modulo
if __name__ == '__main__':
    import os
    here = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(here, './test/data/p08.csv')
    title, serial_number, header, extra = get_info(filename)
    table = get_data(filename)
    print('Title: {}'.format(title))
    print('Serial number: {}'.format(serial_number))
    print('Header: {}'.format(header))
    print('Extra: {}'.format(extra))
    print('Dados: {}'.format(table))
    print('Extra processado {}'.format(process_data(extra)))

