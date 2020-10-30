import getpass
import re


def extract(url):
    regex = "(((?P<user>[^:@]+)(:(?P<password>[^@]+))?)@)?(?P<hostname>[^:]+)(:(?P<port>[^/]+))?(/(?P<path>.+))?"
    pattern = re.compile(regex)
    m = pattern.match(url)
    credential = {
        'user': m.group('user'),
        'hostname': m.group('hostname'),
        'port': int(m.group('port')),
        'password': m.group('password'),
        'path': m.group('path')
    }
    return credential


def ask_user_and_pass(user=None, password=None, prompt='Credentials:'):
    if user is None or password is None:
        print(prompt)
    if user is None:
        # Pede user
        user = input('Username: ')
    if password is None:
        # Pede senha
        password = getpass.getpass(prompt='password for {}: '.format(user))
    return user, password
