import os
import glob
import subprocess
import logging

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_converters(folder):
    """
    Retorna todos os .py encontrados no diretorio e subdirecotrios folder
    """
    return glob.glob(os.path.join(folder, '**/*.py'), recursive=True)

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
input_files_path = get_input_files(INPUT_FOLDER)

converter_not_found = []
for input_file in input_files_path:
    logger.info('Processando arquivo {}'.format(input_file))
    # Passa arquivo por todos conversores disponiveis
    converted = False
    for converter in converters_path:
        logger.debug('Executando conversor {}'.format(converter))
        output = subprocess.run([converter, '-i', input_file, '-d', OUTPUT_FOLDER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if output.returncode == 0:
            logger.info('Convertido com sucesso por {}'.format(converter))
            converted = True
    if not converted:
        logger.error('Nenhum conversor encontrado')
        converter_not_found.append(input_file)


# Mostra arqvuios que não foram convertidos
logger.info('Arquivos não convertidos: {}'.format(converter_not_found))


