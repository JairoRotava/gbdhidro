import os
import glob
import subprocess
import logging
import sys
import os

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Converte os arquivos de entrada e salva no diretorio de saida mantendo a mesma estrutura de diretorio

HERE = os.path.abspath(os.path.dirname(__file__))
INPUT_FOLDER = '../station_raw_to_netcdf/input'
OUTPUT_FOLDER = './converted'
CONVERTER_LIST = ['../station_raw_to_netcdf/converters/hobo_ua_003_64/hobo_ua_003_64_to_netcdf.py']

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


input_file_paths = get_input_files(INPUT_FOLDER)
logger.debug('Input files: ', input_file_paths)
relative_paths = [os.path.relpath(path, INPUT_FOLDER) for path in input_file_paths]
output_file_paths = [os.path.splitext(os.path.join(OUTPUT_FOLDER, path))[0] + '.nc' for path in relative_paths]


#exit()

#CONVERTERS_FOLDER = os.path.join(THIS_PATH, 'converters')
#OUTPUT_FOLDER = os.path.join(THIS_PATH, 'output')
#INPUT_FOLDER = os.path.join(THIS_PATH, 'input')

# Ecnontra todos conversores disponiveis
#converters_path = get_converters(CONVERTERS_FOLDER)
#print(converters_path)
#input_files_path = get_input_files(INPUT_FOLDER)

converter_not_found = []
print('GDB-Hidro batch conversion tool to NetCDF V0.0.1')
print('Input folder {}'.format(INPUT_FOLDER))
print('Output folder {}'.format(OUTPUT_FOLDER))
succeed = []
failed = []
for input_file, output_file in zip(input_file_paths, output_file_paths):
    # Passa arquivo por todos conversores disponiveis
    converted = False
    print('{} '.format(os.path.basename(input_file)), end='')

    output_folder = os.path.dirname(output_file)
    os.makedirs(output_folder, exist_ok=True)
    # Checa se arquivo ja existe
    if os.path.exists(output_file):
        message = 'ERROR: file already exist'
        print(message)
        continue

    # Tenta fazer a conversao
    for converter in CONVERTER_LIST:
        output = subprocess.run([converter, '-i', input_file, '-o', output_file], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        logger.debug('({}) {}'.format(os.path.basename(converter), output.stdout))
        if output.returncode == 0:
            print('(converted by {}) '.format(os.path.basename(converter)))
            succeed.append(input_file)
            converted = True
            break

    # Checa se conversao teve sucesso
    if converted:
        pass
    else:
        print('ERROR: no converter found')
        failed.append(input_file)

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
#logger.debug('Arquivos não convertidos: {}'.format(converter_not_found))


