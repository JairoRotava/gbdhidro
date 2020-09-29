# Conversor HOBO Pendant Event 64K (UA-003-64) para NetCDF
Ferramenta para conversao de arquivos .csv exportados pelo HOBOWare para arquivos NetCDF, padrão CF (Climate and 
Forecast). Os dados de precipitação devem ser exportados utilizando o formato default do Hoboware. Somente o evento
da medida é salvo, e qualquer outra informação do arquivo é descartado. Dessa forma os dados são os 
valores acumulados da precipitação desde que o valor foi zerado. As vantagens de armazenar
 somente os eventos são:
 - apenas os eventos são armazenandos oque evita  salvar dados sem informação (zero).
 - a partir desses valores é possível calcular a taxa de precipitação para qualquer intervalo.
 - evita a perda de dados devido configuração incorreta dos filtros na hora do deploy do sensor
 
## Uso
Para uso deve instalar o pacote GBD-Hidro (pip instal GBD-Hidro) e Unidata udunits (sudo apt-get -y install udunits-bin).
O comando básico ```pyhton hobo_ua_003_64_to_netcdf.py NORME_DO_ARQUIVO.csv``` executada o conversor no arquivo.
Utilize ```pyhton hobo_ua_003_64_to_netcdf.py``` --help para ver opções de uso.

O conversor utiliza dois arquivos extras: precipitation_netcdf.json e station_info.csv. O primeiro arquivo
define a estrutura do arquivo de saída NetCDF, e geralmente não precisa ser alterado. Ele contem também
metadados das medidas que devem ser alterada uma vez. No arquivo station_inf.csv estão informações sobre
cada estação que o conversor pode converter. Informações como código ID, texto de identificação, coordenadas
GPS e outros são lidas desse arquivo. Isso permite utilizar o conversor com diferentes estações desse modelo.

Não é possível utilizar o conversor sem as informações adicionais fornecidas pelos arquivos acima, pois
os dados que estão no arquivo da estação são incompletos, não são auto decritos. Por exemplo: os arquivos
das estação não tem informações como a coordenada GPS dos mesmos, nem informações extras suficientes
para identificar as informações internas de forma única. As informações extras são fornecidas pelos
dois arquivos de configuração.

##Objetivo
O objetivo desse tipo de conversão dos arquivos para padrão NetCDF CF é que os dados sejam auto contidos, 
ou seja, uma vez que o usuário tenha o arquivo NetCDF ele contém todas as informações relevantes para 
uso do mesmo. O usuário não precisa procurar informações adicionais como posição GPS da estação, tipo de 
equipamento, medidas e unidades, intervalo de amostragem, etc. O padrão CF vem sendo adotado por
diversos institutos pelo mundo para distribuição de dados de Clima e Previsão. Este formato também vem
sendo utilizado por agências de dados climáticos observacionais, entretanto ainda existem alguns problemas
sem resposta para esse tipo de aplicação. Acreditasse que isso deve ser corrigido no padrão em breve.
Todos os metadados incluídos no arquivo NetCDF podem ser utilizados em um serviço de indexação para que os
mesmos sejam encontrador facilmente. 
 
 