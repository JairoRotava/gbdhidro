# Copia os arquivo com o identificador uuid desejado para pasta de destino

import argparse
import logging
import os
import shutil

DEBUG = False
HERE = os.path.abspath(os.path.dirname(__file__))
DEBUG_UUID = 'gbdhidro/estacoes/eh-p08/EH-P08_20200228T130000Z_20200508T184534Z.nc'
DEBUG_DB_FOLDER = os.path.realpath('../test/output/load_netcdf_to_db/database_root')
DEBUG_DST_FOLDER = os.path.realpath('../test/output/get_netcdf_from_db')
DEBUG_OVERWRITE = True

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
    src_file = os.path.join(db_folder, uuid + '.zip')
    logger.debug('src_file: {}'.format(src_file))
    # Checa se uuid (arquivo) existe
    if not os.path.exists(src_file):
        raise FileExistsError('ERROR: uuid not found')

    dst_file = os.path.join(dst_folder, os.path.basename(uuid) + '.zip')
    logger.debug('dst_file: {}'.format(dst_file))
    # checa se arquivo de saida ja existe
    if os.path.exists(dst_file) and overwrite is False:
        raise FileExistsError('ERROR: destination file already exist')

    # Copia arquivo para destina
    shutil.copyfile(src_file, dst_file)


def get_commandline():
    """
    Captura dados de linhas de comando
    """
    parser = argparse.ArgumentParser(description='Get NetCDF from database')
    parser.add_argument("uuid", type=str, help="NetCDF uuid")
    parser.add_argument("db", type=str, help="root database folder")
    parser.add_argument("dst", type=str, help="destination folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output file', action='store_true')
    args = parser.parse_args()

    db_folder = os.path.realpath(args.db)
    dst_folder = os.path.realpath(args.dst)
    uuid = args.uuid
    overwrite = args.ow

    return uuid, db_folder, dst_folder, overwrite


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        logger.setLevel(level=logging.DEBUG)
        uuid = DEBUG_UUID
        db_folder = DEBUG_DB_FOLDER
        dst_folder = DEBUG_DST_FOLDER
        overwrite = DEBUG_OVERWRITE
    else:
        uuid, db_folder, dst_folder, overwrite = get_commandline()

    get_from_db(uuid, db_folder, dst_folder, overwrite)
