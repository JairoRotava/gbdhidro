import argparse
import os
import glob
import subprocess
import logging
import sys
import os


# Aplica processamento em todos arquivos de forma recursiva, e salva resultados em diretorio de saido
# com mesma estrutura. Os processamento é fornecido atravez de arquivo de configuracao process.csv
# A estrutura do arquivo é:
# comando, comand,{file_name}, comand, comand onde {file_name} vai ser substituido automaticamente

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

HERE = os.path.abspath(os.path.dirname(__file__))

FILE_NAME_TAG = '{file_name}'
OUTPUT_FOLDER_TAG = '{output_folder}'

DEBUG = True
DEBUG_INPUT_FOLDER = os.path.realpath('./netcdf/test/station_files')
DEBUG_OUTPUT_FOLDER = os.path.realpath('./netcdf/test/output/convert_batch_netcdf')
DEBUG_PROCESS_LIST = [['python', os.path.realpath(os.path.join(HERE, './netcdf/station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')),
                  FILE_NAME_TAG, '-o', OUTPUT_FOLDER_TAG, '-ow'],
                   ['python', os.path.realpath(os.path.join(HERE, './netcdf/station_raw_to_netcdf/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py')),
                  FILE_NAME_TAG, '-o', OUTPUT_FOLDER_TAG, '-ow']
                  ]
DEBUG_LOG_FILE = os.path.realpath('log.txt')


def get_input_files(folder):
    """
    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
    """
    return glob.glob(os.path.join(folder, '**/*.*'), recursive=True)


def process_files(process_list, input_folder, output_folder=None, log=None):
    input_file_paths = get_input_files(input_folder)
    relative_paths = [os.path.relpath(path, input_folder) for path in input_file_paths]

    if output_folder:
        output_folder_paths = [os.path.join(output_folder, os.path.dirname(path)) for path in relative_paths]
    else:
        output_folder_paths = [None for path in relative_paths]

    print('GDB-Hidro batch conversion tool to NetCDF V0.0.1')
    print('Input folder {}'.format(input_folder))
    print('Output folder {}'.format(output_folder))
    print('Processes: \n    {}'.format('\n    '.join([' '.join(process) for process in process_list])))
    succeed = []
    failed = []

    for input_file, output_folder in zip(input_file_paths, output_folder_paths):
        message = ''
        error = False

        # Passa arquivo por todos conversores disponiveis
        print('File: {}'.format(os.path.basename(input_file)))

        # cria diretorio de saida
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)

        # Tenta fazer a conversao
        if not error:
            for process in process_list:
                cmd = process
                cmd = [c.replace(FILE_NAME_TAG, input_file) for c in cmd]
                if output_folder:
                    cmd = [c.replace(OUTPUT_FOLDER_TAG, output_folder) for c in cmd]
                command_text = ' '.join(cmd)
                output = subprocess.run(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

                if output.returncode == 0:
                    message = '    OK {}'.format(command_text)
                    print(message)
                    error = False
                    break
                else:
                    error = True
                    message = '    ERROR {}'.format(command_text)
                    print(message)

        # Checa se conversao teve sucesso
        if error:
            failed.append('{} {}'.format(input_file, message))
        else:
            succeed.append('{} {}'.format(input_file, message))

    # Mostra arqvuios que não foram convertidos
    print('\nTotal converted: {}'.format(len(succeed)))
    print('Total failed: {}'.format(len(failed)))

    if log is not None:
        with open(log, 'w') as fo:
            fo.write('Succeed conversion:\n')
            for item in succeed:
                fo.write('{}\n'.format(item))
            fo.write('\nFailed conversion:\n')
            for item in failed:
                fo.write('{}\n'.format(item))

        print('Check file {} for more details'.format(log))


def command_line():
    # nao esta em debug. Pega informações da linha de comando
    parser = argparse.ArgumentParser(description='Conversion tool arguments:')
    parser.add_argument("process", type=str, help="file with processes list")
    parser.add_argument("input", type=str, help="hobo input files folder")
    parser.add_argument('-o', '--output', type=str, help="output folder")
    parser.add_argument("-l", "--log", type=str, help="log file name")

    args = parser.parse_args()



    if args.output is None:
        output_folder = None
    else:
        output_folder = os.path.realpath(args.output)

    if args.log is None:
        log_file = None
    else:
        log_file = os.path.realpath(args.file)

    input_folder = os.path.realpath(args.input)

    process_filename = os.path.realpath(args.process)
    process_list = read_process_file(process_filename)

    process_files(process_list, input_folder, output_folder=output_folder, log=log_file)


def read_process_file(file_name):
    import csv

    # process_file = os.path.realpath(args.process)
    #process_file = 'process_list.csv'

    with open(file_name, newline='') as csvfile:
        csv_lines = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_ALL)
        process_list = []
        for row in csv_lines:
            # Pula comentarios #
            if (row[0]).strip()[0] == '#':
                continue
            process = [c.strip(' \"\'') for c in row]
            process_list.append(process)
    return process_list


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        # Abre arquivo process e processa para lista
        process_files(DEBUG_PROCESS_LIST, DEBUG_INPUT_FOLDER, output_folder=DEBUG_OUTPUT_FOLDER, log=DEBUG_LOG_FILE)
    else:
        command_line()
