# gbdhidro.database

Manipulação do arquivo netcdf para salvar e recuperar do banco de dados.
Carrega arquivos NetCDF para banco de dados e gera metadados para indexar o arquivo

## Exemplos
- Obtem arquivo do banco de dados: ```python get.py foo@localhost:2222 eh-p02_20191212t150000z_20200226t200800z.nc -p pass -r gbdserver -dst /media/jairo/Dados/Jairo/Projetos/Samuel data/git/GBD-Hidro/gbdhidro/database/test/output/get_netcdf -ow```
- 