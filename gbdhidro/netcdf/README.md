# netcdf

Pacote com rotinas para conversão dos arquivos das estações para padrão NetCDF.

Cada modelo de estação tem um conversor próprio no diretorio station_raw_to_netcdf. 

O arquivo convert_batch_netcdf chama todos os conversores disponiveis e faz a conversão dos arquivos
mantendo a estrutura de diretorio.

     