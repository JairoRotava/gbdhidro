# GBD Hidro 
 
## Descrição

Projeto para armazenamento de dados de estações meteoroloǵicas. Os dados são armazenados em arquivos do
formato NetCDF, seguindo a padronização sugerida pelo padrão Climate Forecast (CF). Todos metadados 
necessários para interpretação dos dados são armazenados junto no arquivo. A partir dos metadados do arquivo 
NetCDF é gerado um índice para busca das informações em um banco de dados MongoDB.

Foi escolhida esta estrutura pelos seguintes motivos:
- os dados são disponibilizados em forma de arquivo e organizados em diretórios. Isso permite 
busca automatizada e manual dos dados.
- a criação do índice permite uma busca facilitada e com maiores detalhes.
- a padronzação CF vem sendo utilizada por diversos órgãos internacionais (NASA, ESA, MET) para armazenamento 
de dados climáticos e vem sendo adotado como padrão para dados observacionais. 
O suporte para dados observacionais ainda não é completo, mas deve melhorar com o passar o tempo.
- Existem grupos ativos e bastante informação para o padrão CF, arquivos NetCDF e outros na internet. Isso
disponibiliza dados e ferramentas importantes.

Devido estes motivos foi optado por fazer um armazenamento dos dados em forma de arquivo NetCDF, organizado
numa estrutura de diretórios, com um índice em MongoDB para facilitar a busca dos dados.

## Como funciona
Os dados a serem armazenados devem ser convertidos para um arquivo NetCDF seguindo o padrão CF. O padrão
CF ainda não atende a todos os tipos de medidas e variáveis, por isso em caso de falta da padrão deve-se 
atender ao padrão da melhor forma possível. Informações como tipo do dado, forma da medida, localização,
período de medida são informações importante para permitir o uso dos dados posteriormente sem problemas.

No arquivo NetCDF diferentes atributos globais podem ser armazenados, e estes atributos são utilizados
para a indexação do arquivos. O atributo mais importante é identificar único universal (database_uuid). Cada
arquivo deve ser um uuid único em todo o banco de dados, arquivos com mesmo uuid são considerados iguais. 
O formato do uuid é rígido e deve ser respeitado para correto funcionamento do banco. O usuário pode
utilizar mais ou menos subdivisões do uuid, mas o uuid completo não pode ser repetido. Os uuid devem
ser sempre com letra minuscula, evitar espaços e caracteres especias, ou seja, devem ser um nome de pasta 
valido.

Exemplos válidos de uuid:
- ufpel/cnpq/estacoes hidrologicas/eh-01/eh-01.nc
- ufpel/projeto alpha/dados modelados/mapa temperatura.nc
- ufpel/projeto alpha/dados medidos/temperatura.nc

A estrutura do armazenamento pode ser alterada para atender melhor ao projeto em questão, mas é recomendado
tomar um tempo para definir a melhor estrutura. A estrutura não tem influencia nenhuma no índice, mas
pode facilitar bastante na busca manual.

Os atributos globais dos arquivos NetCDF são armazenados também no índice, para facilitar a busca. Os dados
são armazenados somente nos arquivos NetCDF.

## Atributos globais obrigatórios
Alguns atributos são obrigatório para permiter a busca dos dados. Atributos não obrigatoório também são 
armazenados no índice, e isso permite uma maior flexibilidade para diferentes projetos, lembrando que
atributos não obrigatórios não são documentados, então o usuário deve tomar conta disso de alguma forma
na hora da busca.

Atributos obrigatórios:
- database_uuid: identificador universal único, em forma de estrutura de diretório. Exemplo: gbdhidro/estacoes/eh-p09/EH-P09_20200228T140000Z_20200511T134927Z.nc
- geospatial_lat_min: latitude e longitude max e min. Utilizada para localizado dos dados espacialmente
- geospatial_lat_max
- geospatial_lon_min
- geospatial_lon_max
- time_coverage_start: data de inicio das medidas, em UTC
- time_coverage_end: data de fim das medidas em UTC. Utilizado para encontrar os dados na escala temporal

Estes são atributos obrigatórios. Demais atributos opcionais e recomendados podem ser encontados no 
padrão CF.

## Referencias

- Informações sobre Climate Forecast (CF): https://cfconventions.org/
- Informações sobre NetCDF em python: https://unidata.github.io/netcdf4-python/netCDF4/index.html


## Quickstart
Para instalação  do pacote fazer o download do mesmo, e instalar:

```pip install -e gbdhidro```

Também é necessário instalar mongodb e cfunits. 

Para teste utilize pytest.
Para visualização dos arquivos nc utilizar *ncview* ou *panoply*

## Dependencias
Os pacotes python utilizados por esse projeto são:
- netcdf4 (escrita/leitura arquivos NetCDF): ```pip install netcdf4```
- cfchecker (verificador de padrão de dados CF): ```pip install cfchecker```
- pandas (manipulação de dados): ```pip install pandas```
- numpy (manipulação de dados): ```pip install numpy```
- python-dateutil (manipulação de intervalo de datas): ```pip install python-dateutil```
- cfunits (manipulação de unidades do padrão de dados CF): ```pip install cfunits```
- pymongo (banco de dados MongoDB): ```pip install pymongo```

O pacote cfunits precisa est biblioteca instalada para funcionar (ubuntu): ```sudo apt-get -y install udunits-bin```
Também é necessário instalar o MongoDB. Verificar instruções para instalação do MongoDB na internet.

