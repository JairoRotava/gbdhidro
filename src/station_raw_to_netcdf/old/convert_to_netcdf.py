import os
import glob
import subprocess
import logging
import sys
import os

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

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


THIS_PATH = os.path.abspath(os.path.dirname(__file__))
CONVERTERS_FOLDER = os.path.join(THIS_PATH, 'converters')
OUTPUT_FOLDER = os.path.join(THIS_PATH, 'output')
INPUT_FOLDER = os.path.join(THIS_PATH, 'input')

# Ecnontra todos conversores disponiveis
converters_path = get_converters(CONVERTERS_FOLDER)
print(converters_path)
input_files_path = get_input_files(INPUT_FOLDER)

converter_not_found = []

print('Iniciando conversao em lote')
print('Diretorio de entrada {}'.format(INPUT_FOLDER))
print('Diretorio de saida {}'.format(OUTPUT_FOLDER))
for input_file in input_files_path:
    # Passa arquivo por todos conversores disponiveis
    converted = False
    print('{} '.format(os.path.basename(input_file)), end='')
    for converter in converters_path:
        output = subprocess.run([converter, '-i', input_file, '-d', OUTPUT_FOLDER], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        logger.debug('({}) {}'.format(os.path.basename(converter), output.stdout))
        if output.returncode == 0:
            print('(converted by {}) '.format(os.path.basename(converter)))
            converted = True
            break

    if converted:
        pass
    else:
        print('ERROR')
        converter_not_found.append(input_file)

# Mostra arqvuios que não foram convertidos
#logger.debug('Arquivos não convertidos: {}'.format(converter_not_found))


