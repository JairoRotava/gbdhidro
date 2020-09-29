# GBD Hidro 
 
## Descrição
Projeto para armazenamento de dados de estações meteoroloǵicas. Os dados são armazenados em arquivos do
formato NetCDF, seguindo a padronização sugerida pelo padrão Climate Forecast (CF), onde os dados tem
nomes e estruturas contorlados para facilitar compartilhamento. Todos metadados necessários para interpretação
do arquivo são armazenados no arquivo. A partir dos metadados armazenado no arquivo NetCDF é gerado um índice
para busca das informações em um banco de dados MongoDB.

Foi escolhida esta estrutura pelos seguintes motivos:
- os dados são disponibilizados em forma de arquivo e organizados em diretórios. Isso permite 
busca manual dos dados e fácil acesso.
- a criação do índice permite uma busca facilitada e com maiores detalhes
- a padronzação CF vem sendo utilizada por diversos órgãos internacionais (NASA, ESA, MET) para armazenamento de dados
climáticos e vem sendo adotado como padrão para dados observacionais. O suporte para dados observacioanais
ainda não é completo, mas deve melhorar com o passar o tempo.
- Existem grupos ativos e bastante informação para o padrão CF, arquivos NetCDF e outros na internet. Isso
disponibiliza dados e ferramentas importantes.

Devido estes motivos foi optado por fazer um armazenamento dos dados em forma de arquivo NetCDF, organizado
num estrutura de diretórios, com um índice em MongoDB para facilitar a busca dos dados.

### Como funciona
Os dados a serem armazenados devem ser convertidos para um arquivo NetCDF seguindo o padrão CF. O padrão
CF ainda não atende a todos os tipos de medidas e variáveis, por isso em caso de falta da padrão deve-se 
atender ao padrão da melhor forma possível. Informações como tipo do dado, forma da medida, localização,
período de medida são informações importante para permitir o uso dos dados posteriormente sem problemas.

No arquivo NetCDF diferentes atributos globais podem ser armazenados, e estes atributos são utilizados
para a indexação do arquivos. O atributo mais importante é identificar único universal (database_uuid). Cada
arquivo deve ser um uuid único em tobo o banco de dados, arquivos com mesmo uuid são considerados iguais. 
o formato do uuid é rígodo e deve ser respeitado para correto funcionamento do banco. O usuário pode
utilizar mais ou menos subdivisões do uuid, mas o uuid completo não pode ser repetido. Os uuid devem
ser sempre com letra minuscula, evitar espaços e caracteres especias, ou sej, devem ser um nome de pasta valido.
Exemplos de uuid:
- <universidade>/<projeto>/<estacoes>/<idestacao>/<arquivo_data-inicio_data-final.nc>
- <projeto>/<estacoes>/<ID>/<nome do arquivo>
- <projeto>/<processado>/<ID>/<nome do arquivo>

A estrutura do armazenamento pode ser alterada para atender melhor ao projeto em questão, as recomendasse
tomar um tempo para definir a melhor estrutura. A estrutura não tem influencia nenhuma no índice, mas
pode facilitar bastante uma eventual busca manual.

Os atributor globais são armazenados no banco de dados, enquanto os arquivos são armazenados no diretório 
de armazenamento.

### Atributos globais obrigatórios
Alguns atributos são obrigatório para permite a busca dos dados. Atributos não obrigatoório também são 
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

## Link do projeto

## Travis CI [![Build Status](https://travis-ci.org/JairoRotava/gbdhidro.svg?branch=master)](https://travis-ci.org/JairoRotava/gbdhidro)
Travis CI é um serviço de integração contínua, e é utilizado nesse projeto para para garantir que
o código carregado no repositório esteja operacional. Ele instala o pacote e executa os testes sempre
que é feito um novo push.
 
## Quickstart
Para instalação no modo desenvolvedor copiar a pasta com a bilioteca e utilizar o comando:

```pip install -e gbdhidro```

Verifique os exemplos para ver como funciona.

Teste do sistema é realizado com pytest.

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

## TODO
- Reorganizar codigo
- Fazer exemplo
- Documentar
- Teste Travis