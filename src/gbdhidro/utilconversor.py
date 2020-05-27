import re

# Processa coluna de data e hora, tranforma para datetime nativo e adiciona informacao de timezone
def get_gmt_offset(gmt_str):
    """
    Procura por string com o termo GMT e retira oque pode ser hora e minuto
    Em caso de falha ele gera uma exception
    """
    p = re.compile(r'GMT(?P<hour>[-+]*\d+):*(?P<minute>\d+)*', re.IGNORECASE)
    m = p.search(gmt_str)
    hour = 0
    minute = 0
    if m is not None:
        if m['hour'] is not None:
            hour = int(m['hour'])
        if m['minute'] is not None:
            minute = int(m['minute'])
    else:
        raise ValueError("GMT offset not found")
    return hour, minute

def find_matches(line, substrings):
    for substring in substrings:
        find = re.compile(substring, re.IGNORECASE)
        found = find.search(line)
        if found is None:
            return False
    return True

def isnotebook():
    """
    Checa se esta script esta dentro de um jupyter notebook (True) ou rodando python
    convencional (False).
    Utilizado para alterar comportamento do código. Se estiver dentro do juyter é modo
    debug, se fora, modo full power.
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter