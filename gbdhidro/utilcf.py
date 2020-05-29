from datetime import datetime
import base64
from io import BytesIO

def datetime2str(date_time):
    """
    Retorna datetime em formato do CF em string. Utilizar somente valor UTC.
    """
    return date_time.strftime('%Y%m%dT%H%M%SZ')

def timedelta2str(value):
    """
    Converte timedelta para string no format iso8601
    TODO: corrigir para retornar ano tb.
    """
    # split seconds to larger units
    seconds = value.total_seconds()
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    days, hours, minutes = map(int, (days, hours, minutes))
    seconds = round(seconds, 6)

    ## build date
    date = ''
    if days:
        date = '%sD' % days

    ## build time
    time = u'T'
    # hours
    bigger_exists = date or hours
    if bigger_exists:
        time += '{:02}H'.format(hours)
    # minutes
    bigger_exists = bigger_exists or minutes
    if bigger_exists:
      time += '{:02}M'.format(minutes)
    # seconds
    if seconds.is_integer():
        seconds = '{:02}'.format(int(seconds))
    else:
        # 9 chars long w/leading 0, 6 digits after decimal
        seconds = '%09.6f' % seconds
    # remove trailing zeros
    seconds = seconds.rstrip('0')
    time += '{}S'.format(seconds)
    return u'P' + date + time

def bin2base64(value):
    """
    Converte binario para base64 e utf-8 para facilitar salvar como texto
    Bom para salvar imagens ou outros programas dentro do netcdf como texto.
    """
    bin_base64 = base64.b64encode(value).decode("utf-8")
    return bin_base64

def base642bin(value):
    """
    Converte de base64 para binario
    """
    bin_raw = BytesIO(base64.b64decode(value))
    return bin_raw
    