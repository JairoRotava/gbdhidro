import argparse
import os
import glob
import subprocess
import logging
import sys
import os

DEBUG = True
# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Converte os arquivos de entrada e salva no diretorio de saida mantendo a mesma estrutura de diretorio

HERE = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = os.path.realpath('../test/output/hobo_ua_003_64')
OUTPUT_FOLDER = os.path.realpath('../test/output/load_netcdf_to_db/gdb')
CONVERTER_LIST = [os.path.join(HERE, '../station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')]
FILE_OVERWRITE = True
ERROR_CODE = 1

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


def get_input_files(folder):
    """
    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
    """
    return glob.glob(os.path.join(folder, '**/*.*'), recursive=True)

from netCDF4 import Dataset
from shutil import copyfile
import zipfile

def load_all(input_folder, output_folder, overwrite=False):
    print('GDB-Hidro load  NetCDF to database V0.0.1')
    print('Input folder {}'.format(input_folder))
    print('Root database folder {}'.format(output_folder))

    input_file_paths = get_input_files(input_folder)
    logger.debug('Input files: ', input_file_paths)

    #relative_paths = [os.path.relpath(path, input_folder) for path in input_file_paths]
    #output_file_paths = [os.path.splitext(os.path.join(output_folder, path))[0] + '.nc' for path in relative_paths]

    for input_file in input_file_paths:
        rootgrp = Dataset(input_file, 'r')

        if not hasattr(rootgrp, 'database_uuid'):
            print('ERROR: database_uuid global attribute not found')
            rootgrp.close()
            exit(ERROR_CODE)

        dst_folder = os.path.join(out_folder, os.path.dirname(rootgrp.database_uuid))
        dst_file = os.path.basename(rootgrp.database_uuid)
        # Create folder is not exits
        os.makedirs(dst_folder, exist_ok=True)
        dst_file_path = os.path.join(dst_folder, dst_file)
        # Verifica se arquivo ja existe
        # Verifica se arquivo ja existe e gera erro caso flag de overwrite
        # nao esteja setada

        if not overwrite:
            if os.path.exists(dst_file_path):
                print('ERROR: file already exist. Use -ow flag to overwrite')
                exit(ERROR_CODE)

        # Se chegou aqui pode copiar o arquivo com o novo nome
        print('Copiando {} -> {}'.format(input_file, dst_file_path))
        # TODO: comprimir os arquivos antes de colocar no banco

        with zipfile.ZipFile(dst_file_path + '.zip', "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(input_file, os.path.basename(input_file))
        copyfile(input_file, dst_file_path)




        rootgrp.close()

    exit()

    succeed = []
    failed = []
    for input_file, output_file in zip(input_file_paths, output_file_paths):
        message = ''
        error = False

        # Passa arquivo por todos conversores disponiveis
        print('{} '.format(os.path.basename(input_file)), end='')

        output_folder = os.path.dirname(output_file)
        os.makedirs(output_folder, exist_ok=True)
        # Checa se arquivo ja existe
        if not overwrite:
            if os.path.exists(output_file):
                message = 'ERROR: file already exist'
                error = True

        # Tenta fazer a conversao
        if not error:
            for converter in CONVERTER_LIST:
                if overwrite:
                    output = subprocess.run(['python', converter, input_file, output_file, '-ow'], stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
                else:
                    output = subprocess.run(['python', converter, input_file, output_file], stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
                logger.debug('({}) {}'.format(os.path.basename(converter), output.stdout))
                if output.returncode == 0:
                    message = '(converted by {}) '.format(os.path.basename(converter))
                    error = False
                    break
                else:
                    error = True
                    message = 'ERROR'

        # Checa se conversao teve sucesso
        if error:
            failed.append('{} {}'.format(input_file, message))
        else:
            succeed.append('{} {}'.format(input_file, message))
        print(message)

    # Mostra arqvuios que não foram convertidos
    print('\nTotal converted: {}'.format(len(succeed)))
    print('Total failed: {}'.format(len(failed)))

    LOG_FILE = 'converter.log'
    with open(LOG_FILE, 'w') as fo:
        fo.write('Succeed conversion:\n')
        for item in succeed:
            fo.write('{}\n'.format(item))
        fo.write('\nFailed conversion:\n')
        for item in failed:
            fo.write('{}\n'.format(item))

    print('Check file {} for more details'.format(LOG_FILE))


def get_commandline():
    # nao esta em debug. Pega informações da linha de comando
    parser = argparse.ArgumentParser(description='Load NetCDF to GBD database')
    parser.add_argument("input", type=str, help="input file")
    parser.add_argument("output", type=str, help="root database folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output files', action='store_true')
    args = parser.parse_args()

    output_folder = os.path.realpath(args.output)
    input_folder = os.path.realpath(args.input)

    overwrite = args.overwrite

    if not output_folder or not input_folder:
        parser.print_help()
        exit(ERROR_CODE)

    return input_folder, output_folder, overwrite


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        print('WARNING: Debug mode')
        in_folder = os.path.realpath(INPUT_FOLDER)
        out_folder = os.path.realpath(OUTPUT_FOLDER)
        overwrite = FILE_OVERWRITE
    else:
        in_folder, out_folder, overwrite = get_commandline()
    load_all(in_folder, out_folder, overwrite)
