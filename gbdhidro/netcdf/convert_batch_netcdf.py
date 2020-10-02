import argparse
import os
import glob
import subprocess
import logging
import sys
import os

# TODO: isso aqui ainda nao esta bom. Os conversores são ligados por codigo interno oque não deixa a solução
# flexivel. Tentar fazer um conversor onde vc fornce as ferramentas de conversao e ele tenta aplicar automaitcamente
# e mantem a estrutura de saida de diretorio

# Inicia logging
logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

# Converte os arquivos de entrada e salva no diretorio de saida mantendo a mesma estrutura de diretorio

HERE = os.path.abspath(os.path.dirname(__file__))
DEBUG = False
DEBUG_INPUT_FOLDER = os.path.realpath('./test/station_files')
DEBUG_OUTPUT_FOLDER = os.path.realpath('./test/output/convert_batch_netcdf')
CONVERTER_LIST = [os.path.realpath(os.path.join(HERE, './station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py'))]
DEBUG_FILE_OVERWRITE = True
ERROR_CODE = 1

# Formato do diretorio de saida
# gbd/<projeto>/<fonte>/<id>/arquivos onde:
# por exemplo:
# gbd/estacoes/observacionais/EH-P02/<projeto>_<source>_<id>_20200101T010101Z_20200202T020202Z
# As informações de <projeto> <fonte> e <id> devem estra armazenadas em algum arquico e apartir do ID do arquivo
# deve ser enviado automaticamnete para o diretorio correot. Pensar melhor como fazer isso. Os arquivos nc devem ter
# o projeto e a fonte dos dados internamente
#
# Formato do rquivo: ID_Datainicail_datafinal
# O ID deve ser único dentro de um projeto/fonte


def get_converters(folder):
    """
    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
    """
    converters = glob.glob(os.path.join(folder, '**/*.py'), recursive=True)
    # Remove test files
    conv_out = []
    for c in converters:
        fname = os.path.basename(c)

        # Descarta nomes com a string test
        if fname.find('test') == -1:
            conv_out.append(c)
        else:
            print('Descartando conversor com test: {}'.format(c))
    return conv_out


def get_input_files(folder):
    """
    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
    """
    return glob.glob(os.path.join(folder, '**/*.*'), recursive=True)


def convert_all(input_folder, output_folder, overwrite=False):
    input_file_paths = get_input_files(input_folder)
    logger.debug('Input folder: '.format(input_folder))
    logger.debug('Input files: '.format(input_file_paths))
    relative_paths = [os.path.relpath(path, input_folder) for path in input_file_paths]
    output_file_paths = [os.path.splitext(os.path.join(output_folder, path))[0] + '.nc' for path in relative_paths]

    print('GDB-Hidro batch conversion tool to NetCDF V0.0.1')
    print('Input folder {}'.format(input_folder))
    print('Output folder {}'.format(output_folder))
    print('Converters {}'.format(CONVERTER_LIST))
    succeed = []
    failed = []
    for input_file, output_file in zip(input_file_paths, output_file_paths):
        message = ''
        error = False

        # Passa arquivo por todos conversores disponiveis
        print('{} '.format(os.path.basename(input_file)), end='')

        output_folder = os.path.dirname(output_file)
        # cria diretorio de saida
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
                    cmd = ['python', converter, input_file, '-o', output_file, '-ow']
                    output = subprocess.run(cmd , stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
                else:
                    output = subprocess.run(['python', converter, input_file, '-o', output_file], stdout=subprocess.PIPE,
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


def command_line():
    # nao esta em debug. Pega informações da linha de comando
    parser = argparse.ArgumentParser(description='Conversion tool arguments:')
    parser.add_argument("input", type=str, help="hobo input files folder")
    parser.add_argument("output", type=str, help="output files folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output files', action='store_true')
    args = parser.parse_args()

    output_folder = os.path.realpath(args.output)
    input_folder = os.path.realpath(args.input)

    overwrite = args.overwrite

    if not output_folder or not input_folder:
        parser.print_help()
        exit(ERROR_CODE)

    convert_all(input_folder, output_folder, overwrite)

#    return input_folder, output_folder, overwrite


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        #in_folder, out_folder, overwrite = get_commandline()
        convert_all(DEBUG_INPUT_FOLDER, DEBUG_OUTPUT_FOLDER, DEBUG_FILE_OVERWRITE)
    else:
        command_line()
        #in_folder, out_folder, overwrite = get_commandline()
        #convert_all(in_folder, out_folder, overwrite)
