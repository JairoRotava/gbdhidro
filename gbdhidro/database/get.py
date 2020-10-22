# Copia os arquivo com o identificador uuid desejado para pasta de destino

import argparse
import logging
import os
import shutil
import pysftp

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
DEBUG_UUID = 'gbdhidro/estacoes/eh-p05/EH-P05_20200226T190000Z_20200508T151000Z.nc'
DEBUG_DB_FOLDER = os.path.realpath('./test/output/database_root')
DEBUG_DST_FOLDER = os.path.realpath('./test/output')
DEBUG_OVERWRITE = True

# sftp
SFTP_HOSTNAME = 'localhost'
SFTP_USER = 'foo'
SFTP_PASSWORD = 'pass'
SFTP_PORT = 2222
SFTP_ROOT = 'gbdserver'

DATABASE_DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'gbdroot')

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def get_from_db(uuid, db_folder, dst_folder, overwrite=False):
    """
    Get a file from database
    :param uuid: file uuid
    :param db_folder: database root folder
    :param dst_folder: file destination folder
    :param overwrite: overwrite file if exit flag
    """
    logger.debug('uuid: {}'.format(uuid))
    logger.debug('database root: {}'.format(db_folder))
    src_file = os.path.join(SFTP_ROOT, uuid + '.zip')
    logger.debug('src_file: {}'.format(src_file))

    # Checa se uuid (arquivo) existe
    #if not os.path.exists(src_file):
    #    raise FileExistsError('ERROR: uuid not found')

    dst_file = os.path.join(dst_folder, os.path.basename(uuid) + '.zip')
    logger.debug('dst_file: {}'.format(dst_file))
    # checa se arquivo de saida ja existe
    if os.path.exists(dst_file) and overwrite is False:
        raise FileExistsError('ERROR: destination file already exist')

    # Copia arquivo para destina
    #shutil.copyfile(src_file, dst_file)
    # Pega arquivo do sftp

    read_sftp(src_file, dst_file, SFTP_HOSTNAME, SFTP_PORT, SFTP_USER, SFTP_PASSWORD)


def read_sftp(file, local_folder, hostname, port, username, password):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=hostname, username=username, password=password, port=port,
                           cnopts=cnopts) as sftp:
        sftp.get(file, local_folder)



def command_line():
    """
    Captura dados de linhas de comando
    """
    TOOL_DESCRIPTION = 'Get NetCDF from database'
    parser = argparse.ArgumentParser(description=TOOL_DESCRIPTION)
    parser.add_argument("uuid", type=str, help="NetCDF uuid")
    parser.add_argument("-db", '--database', type=str, help="root database folder")
    parser.add_argument("-dst", '--destination', type=str, help="destination folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output file', action='store_true')
    args = parser.parse_args()

    if args.database is None:
        db = DATABASE_DEFAULT_PATH
    else:
        db = os.path.realpath(args.database)

    if args.destination is None:
        dst = os.path.realpath('.')
    else:
        dst = os.path.realpath(args.destination)

    uuid = args.uuid

    ow = args.overwrite

    get_from_db(uuid, db, dst, ow)


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        logger.setLevel(level=logging.DEBUG)
        uuid = DEBUG_UUID
        db_folder = DEBUG_DB_FOLDER
        dst_folder = DEBUG_DST_FOLDER
        overwrite = DEBUG_OVERWRITE
        get_from_db(uuid, db_folder, dst_folder, overwrite)
    else:
        command_line()
