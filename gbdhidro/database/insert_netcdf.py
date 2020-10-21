# Converte os arquivos de entrada e salva no diretorio de saida mantendo a mesma estrutura de diretorio

# Formato do diretorio de saida
# O arquivo é salvo no caminho definido pelo atributo global database_uuid no NetCDF. Sem esse atributo o
# metodo nao sabe onde colocar o arquivo. O atributo database_uuid deve ser um path de arquivo valido. A recomendacao
# é utilizar somente letras minusculas, evitar espacos e caracteres especiais e acentos. O uuid deve ser unico no universo,
# nao pode se repetir. Isso pode ser conseguido facilmente utilizando instituicao, projeto, sub projeto e outros valores.
# Exemplos:
# database_uuid = /ufpel/gbdhidro/estacao/eh-p01/eh-p01_fev2010-fev2020
# database_uuid = /ufpel/gbdhidro/estacao/precipitacao/eh-p01/eh-p01_fev2010-fev2020
# database_uuid = /ufpel/gbdhidro/estacao/processados/eh-p01/eh-p01_fev2010-fev2020
# o uuid é uam forma bastante flexivel para organizar os dados da forma que for considerada mais conveniente pelo
# usuario. Lembrar que ter isso de forma organizada ajuda em encontrar o arquivo porsterioemente.
# a parte final sera o nome do arquivo na estrutura de difetorio e recomendasse colocar o ID da estacao, e periodo dos
# dados para facilitar uma eventual busca manual dos dados.
# gbd/<projeto>/<fonte>/<id>/arquivos onde:
# por exemplo:
# gbd/estacoes/observacionais/EH-P02/<projeto>_<source>_<id>_20200101T010101Z_20200202T020202Z
# As informações de <projeto> <fonte> e <id> devem estra armazenadas em algum arquico e apartir do ID do arquivo
# deve ser enviado automaticamnete para o diretorio correot. Pensar melhor como fazer isso. Os arquivos nc devem ter
# o projeto e a fonte dos dados internamente
#
# Formato do rquivo: ID_Datainicail_datafinal
# O ID deve ser único dentro de um projeto/fonte
#
# root/instituicao/projeto/fonte/id
# institution/project/source/id
# Cada arquivo. nc deve fornecer um path_id que como deve ser salvo os arquivos automaticamente na base da dados.
# O formato é aberto ao dono do arquivo, mas deve ser com letras minusculas, e ser um nome de diretorio valido.
# id deve ser único
# id = gbdhidro/estacoes/ehp01/ehp01_2000123123_23042304
##


import argparse
import os
import glob
import subprocess
import logging
import sys
import os
from netCDF4 import Dataset
from shutil import copyfile
import zipfile
from pymongo import MongoClient
from gbdhidro.netcdf import cf
import numpy

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = os.path.realpath('./test/output/hobo_ua_003_64')
OUTPUT_FOLDER = os.path.realpath('../test/output/load_netcdf_to_db/database_root')
CONVERTER_LIST = [os.path.join(HERE, '../station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')]
FILE_OVERWRITE = True
ERROR_CODE = 1
LOG_FILE = 'upload.log'
# Mongodb info
#MONGODB_URL = '127.0.0.1:27017'
#DATABASE = 'gbdhidro'
#COLLECTION = 'index'
# Docker mongodb
MONGODB_URL = 'localhost:17017'
DATABASE = 'gbdhidro'
COLLECTION = 'index'
USER = 'root'
PASS = 'example'


DATABASE_DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'gbdroot')

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


# TODO: precisa verificar como fazer quando o arquivo é sobreescrito, e como atualizar isso no index


#def get_input_files(folder):
#    """
#    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
#    """
#    return glob.glob(os.path.join(folder, '**/*.*'), recursive=True)


def insert_entry_db(entry):
    client = MongoClient(MONGODB_URL, username=USER, password=PASS)
    gbd = client[DATABASE]
    index = gbd[COLLECTION]
    index.insert_one(entry)
    client.close()



# Converte os atribuito globais do NetCDF para formatos mais adequados do MongoDB
def convert_netcdf_attributes_to_mongo(dataset):
    attributes = dataset.__dict__.copy()
    d = {}
    for key, value in attributes.items():
        # Convert numpy type to native python
        if type(value).__module__ == numpy.__name__:
            value = value.item()
        # Convert time converage start/end to native mongodb
        if key == 'time_coverage_start':
            # value = datetime.datetime.strptime(value, '%Y%m%dT%H%M%SZ')
            value = cf.iso8601_to_datetime(value)
        if key == 'time_coverage_end':
            value = cf.iso8601_to_datetime(value)
        if key == 'time_coverage_duration':
            # Nao tem tipo de intervalo de tempo definido no mongodb. Guardar o intervalor em segundos
            # Calcula a partir da data de incio e fim pois e mais facil dq converter valor inserido
            # no netcdf. Nao sei direito com lidar com isso ainda
            start = cf.iso8601_to_datetime(attributes['time_coverage_start'])
            end = cf.iso8601_to_datetime(attributes['time_coverage_end'])
            interval = (end - start).total_seconds()
            value = int(interval)

        d.update({key: value})
    return d


def insert_netcdf(input_file, output_folder, overwrite=False):
    #print('GDB-Hidro load  NetCDF to database V0.0.1')
    #print('Input folder {}'.format(input_folder))
    #print('Root database folder {}'.format(output_folder))

    #input_file_paths = get_input_files(input_folder)
    logger.debug('Input file: ', input_file)

    if os.path.isdir(output_folder) is False:
        raise NotADirectoryError('ERROR: {} directory not found'.format(output_folder))


    succeed = []
    failed = []
    #for input_file in input_file_paths:
    #print('{} '.format(input_file), end='')


    #try:

    #rootgrp = Dataset(input_file, 'r')
    with Dataset(input_file, 'r') as rootgrp:

        if not hasattr(rootgrp, 'database_uuid'):
            raise AttributeError('ERROR: database_uuid global attribute not found in netcdf file')

        try:
            metadata = convert_netcdf_attributes_to_mongo(rootgrp)
        except:
            raise AttributeError('ERROR: converting NetCDF metadata')

        dst_folder = os.path.join(output_folder, os.path.dirname(rootgrp.database_uuid))
        dst_file = os.path.basename(rootgrp.database_uuid)
        # Create folder if not exits
        os.makedirs(dst_folder, exist_ok=True)
        dst_file_path = os.path.join(dst_folder, dst_file + '.zip')

        # Verifica se arquivo ja existe
        if not overwrite:
            if os.path.exists(dst_file_path):
                raise FileExistsError('ERROR: file already exist. Use -ow flag to overwrite')

        # Se chegou aqui pode copiar o arquivo com o novo nome
        #print(' -> {}'.format(dst_file_path))
        # compresslevel: 0 - (no compress) 9 (max compress)
        # with zipfile.ZipFile(dst_file_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        #compress level nao existe em python 3.6
        with zipfile.ZipFile(dst_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(input_file, os.path.basename(input_file))

        # Adiciona no index
        insert_entry_db(metadata)

    #except (AttributeError, FileExistsError) as error:
        # Algum erro foi gerado
        #failed.append(input_file)
        #print(error)
        #raise error
    #else:
        # Nenhum erro gerado
        #succeed.append(input_file)
     #   pass
    #finally:
    #    if 'rootgrp' in locals():
    #        rootgrp.close()

    # Mostra arqvuios que não foram convertidos
    #print('\nTotal uploaded: {}'.format(len(succeed)))
    #print('Total failed: {}'.format(len(failed)))

    #with open(LOG_FILE, 'w') as fo:
    #    fo.write('Succeed upload:\n')
    #    for item in succeed:
    #        fo.write('{}\n'.format(item))
    #    fo.write('\nFailed upload:\n')
    #    for item in failed:
    #        fo.write('{}\n'.format(item))

    #print('Check file {} for more details'.format(LOG_FILE))


def command_line():
    TOOL_NAME = 'Insert a netcdf file to the database'
    parser = argparse.ArgumentParser(description=TOOL_NAME)
    parser.add_argument("input", type=str, help="netcdf input file (.nc)", nargs='+')
    parser.add_argument('-db', "--database", type=str, help="root database folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output files', action='store_true')
    args = parser.parse_args()

    if args.database is None:
        # Usa diretorio generico se nao foi especificado
        output = DATABASE_DEFAULT_PATH
    else:
        output = os.path.realpath(args.database)

    #in_folder = os.path.realpath(args.input)
    overwrite = args.overwrite

    input_files = args.input

    print('MongoDB information:')
    print('  url: {}'.format(MONGODB_URL))
    print('  database: {}'.format(DATABASE))
    print('  colection: {}'.format(COLLECTION))
    print('Output directory: {}'.format(output))


    logger.debug('Input files: {}'.format(input_files))
    for input_file in input_files:
        input_file = os.path.realpath(input_file)
        if os.path.isdir(input_file):
            # ignora diretorios
            continue
        else:
            print(input_file)
            insert_netcdf(input_file, output, overwrite)


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        print('WARNING: Debug mode')
        in_folder = os.path.realpath(INPUT_FOLDER)
        out_folder = os.path.realpath(OUTPUT_FOLDER)
        overwrite = FILE_OVERWRITE
        insert_netcdf(in_folder, out_folder, overwrite)
    else:
        command_line()
