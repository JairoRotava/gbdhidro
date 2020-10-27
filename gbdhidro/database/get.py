# Copia os arquivo com o identificador uuid desejado para pasta de destino

import argparse
import logging
import os
import shutil
import pysftp
import re

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
STFP_DEFAULT_PORT = 22

DATABASE_DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'gbdroot')

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def get_from_db(uuid, user, hostname, port, password, db_folder, dst_folder, overwrite=False):
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

    read_sftp(src_file, dst_file, user, hostname, port, password)


def read_sftp(file, local_folder, username, hostname, port, password):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=hostname, username=username, password=password, port=port,
                           cnopts=cnopts) as sftp:
        sftp.get(file, local_folder)


def command_line():
    """
    Captura dados de linhas de comando
    """
    TOOL_DESCRIPTION = 'Get file from database'
    parser = argparse.ArgumentParser(description=TOOL_DESCRIPTION)
    parser.add_argument('user', type=str, help="files access user@host:port")
    parser.add_argument("uuid", type=str, help="file uuid")
    parser.add_argument('-p', '--password', type=str, help="user access password")
    parser.add_argument("-r", '--root', type=str, help="root  folder")
    parser.add_argument("-dst", '--destination', type=str, help="destination folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output file', action='store_true')
    args = parser.parse_args()

    if args.root is None:
        root = SFTP_ROOT
    else:
        root = os.path.realpath(args.root)

    if args.user is None:
        user = SFTP_USER
        hostname = SFTP_HOSTNAME
        port = SFTP_PORT
    else:
        # Interpreta user@hostname:port
        regex = "((?P<user>\S+)@)?(?P<hostname>[^:]+)(:(?P<port>\d+))?"
        pattern = re.compile(regex)
        m = pattern.match(args.user)
        user = m.group('user')
        hostname = m.group('hostname')
        port = m.group('port')

        if port is None:
            port = STFP_DEFAULT_PORT
        else:
            port = int(port)

    if user is None:
        #TODO: Pede usuario
        pass

    if args.password is None:
        # TODO: Pede password
        password = ''
    else:
        password = args.password

    if args.destination is None:
        dst = os.path.realpath('.')
    else:
        dst = os.path.realpath(args.destination)

    uuid = args.uuid

    ow = args.overwrite
    #get_from_db(uuid, user, hostname, port, password, db_folder, dst_folder, overwrite=False):
    get_from_db(uuid, user, hostname, port, password, root, dst, ow)


# Chamado da linha de comando
if __name__ == "__main__":
    if DEBUG:
        logger.setLevel(level=logging.DEBUG)
        uuid = DEBUG_UUID
        db = DEBUG_DB_FOLDER
        dst = DEBUG_DST_FOLDER
        ow = DEBUG_OVERWRITE
        user = SFTP_USER
        hostname = SFTP_HOSTNAME
        port = SFTP_PORT
        password = SFTP_PASSWORD

        #get_from_db(uuid, db_folder, dst_folder, overwrite)
        get_from_db(uuid, user, hostname, port, password, db, dst, ow)
    else:
        command_line()
