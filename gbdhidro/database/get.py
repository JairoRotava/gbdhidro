# Faz download do arquivo do banco de dados a partir do uuid

import argparse
import logging
import os
import pysftp
import re
import getpass
import gbdhidro.database.credentials as cred

DEFAULT_SFTP_ROOT = 'gbdserver'
DEFAULT_SFTP_PORT = 22

# Inicia logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


def get_credentials(user=None, password=None):
    if user is None:
        # Pede user
        user = input('Username: ')
    if password is None:
        # Pede senha
        password = getpass.getpass(prompt='password for {}: '.format(user))
    return user, password


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
    src_file = os.path.join(db_folder, uuid + '.zip')
    logger.debug('src_file: {}'.format(src_file))

    dst_file = os.path.join(dst_folder, os.path.basename(uuid) + '.zip')
    logger.debug('dst_file: {}'.format(dst_file))
    # checa se arquivo de saida ja existe
    if os.path.exists(dst_file) and overwrite is False:
        raise FileExistsError('ERROR: destination file already exist')

    read_sftp(src_file, dst_file, user, hostname, port, password)


def read_sftp(file, local_folder, username, hostname, port, password):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    logger.debug('SFTP file: {}'.format(file))
    with pysftp.Connection(host=hostname, username=username, password=password, port=port,
                           cnopts=cnopts) as sftp:
        sftp.get(file, local_folder)


def command_line():
    """
    Captura dados de linhas de comando
    """
    TOOL_DESCRIPTION = 'Get file from database'
    parser = argparse.ArgumentParser(description=TOOL_DESCRIPTION)
    parser.add_argument("uuid", type=str, help="file uuid")
    parser.add_argument('--url', type=str, help="access url user:password@host:port/root")
    parser.add_argument("-dst", '--destination', type=str, help="destination folder")
    parser.add_argument('-ow', '--overwrite', help='overwrite output file', action='store_true')
    args = parser.parse_args()


    if args.url is None:
        raise ValueError('Credencial para acesso dos arquivos nao fornecida')
        # TODO: pedir credencial
    else:
        # Interpreta user@hostname:port
        #regex = "(((?P<user>[^:@]+)(:(?P<password>[^@]+))?)@)?(?P<hostname>[^:]+)(:(?P<port>[^/]+))?(/(?P<path>.+))?"
        #pattern = re.compile(regex)
        #m = pattern.match(args.url)
        ##user = m.group('user')
        #hostname = m.group('hostname')
        #port = m.group('port')
        #password = m.group('password')
        #root = m.group('path')

        sftp = cred.extract(args.url)
        user = sftp['user']
        hostname = sftp['hostname']
        port = sftp['port']
        password = sftp['password']
        root = sftp['path']

    # Pede user e password se nao foram fornecidos
    user, password = cred.ask_user_and_pass(user, password)

    if port is None:
        port = DEFAULT_SFTP_PORT
    else:
        port = int(port)

    if root is None:
        root = DEFAULT_SFTP_ROOT

    if args.destination is None:
        dst = os.path.realpath('.')
    else:
        dst = os.path.realpath(args.destination)

    uuid = args.uuid

    ow = args.overwrite
    get_from_db(uuid, user, hostname, port, password, root, dst, ow)


# Chamado da linha de comando
if __name__ == "__main__":
    command_line()
