# Conversor HOBO Pendant Event 64K (UA-003-64) para NetCDF

Ferramenta para conversão de arquivos dos medidores de precipitação HOBO Pendant Event, UA-003-64 
para formato  CF (Climate and Forecast)  em arquivo NetCDF. Os arquivos deve ser primeiramente convertidos para aqruivos .csv com o software 
HOBOware, que pode ser encontrado no link abaixo. Não é possível utilizar o arquivo no formato original pois
ele é proprietario e fechado.
 
https://www.onsetcomp.com/hoboware-free-download/

## Formato de conversão do arquivo .csv

Os dados de precipitação devem ser exportados utilizando o formato defualt do Hoboware. Verifique se
a configuração para exportar dados no HOBOware esteja de acordo com o seguinte:
1. separação de campo por virgula (,).
2. formato data: mes/dia/ano. O ano contem somente os dois ultimos digitos
3. formato hora: 12 h com AM/PM

Somente os eventos é salvo por esta ferramenta, ou seja, somente a hora em que foi detectado o movimento da
caçambinha do medidor. Armazenar somente os eventos tem as seguintes vantagens:
- menor quantidade de dados: armazenar somente os eventos elimina informações como zero de precipitação.
- é possivel calcular a taxa de precipitação para qualquer intervalo a partir dos eventos.
- a configuração dos filtros no sensor não influenciam nos dados armazenados, por isso mesmo que ele
seja configurado errado os dados podem ser utilizados.
 
## Uso

A ferrameta de conversão pode ser utilizado pela linha de comando. Para isso é necessário instalar o pacote 
python gbdhidro e dependencias. Verifique documentação para instruções como instalar o gbdhidro.

Exemplos para utilizar a ferramenta na linha de comando:
- ```gbd-hobo2netcdf *.csv -o . -ow```
- ```gbd-hobo2netcdf EHP08040.csv```
- ```gbd-hobo2netdcf --help```

Também é possivel chamar diretamente o arquivo python:
- ```python hobo_ua_003_64_to_netcdf.py --help```
 
## Como ajustar configurações

O conversor utiliza dois arquivos extras: precipitation_netcdf.json e station_info.csv:
- precipitation_netdcf.json define a estrutura do arquivo de saída NetCDF, e geralmente não precisa ser alterado. Ele contem também
metadados das medidas que devem ser alterada uma vez.
- station_inf.csv estão informações sobre cada estação que o conversor pode converter. Informações como código ID, texto de identificação, coordenadas
GPS e outros são lidas desse arquivo. Isso permite utilizar o conversor com diferentes estações desse modelo.

Não é possível utilizar o conversor sem as informações adicionais fornecidas pelos arquivos acima, pois
os dados que estão no arquivo da estação são incompletos, não são auto decritos. Por exemplo: os arquivos
das estação não tem informações como a coordenada GPS dos mesmos, nem informações extras suficientes
para identificar as informações internas de forma única. As informações extras são fornecidas pelos
dois arquivos de configuração.

É possível fornecer arquivos de coniguração customizados à ferramenta. Para isso copie e edit os arquivos
default e utilize:
- ```gbd-hobo2netcdf EHP08040.csv -c stations_info.csv -n precipitation_netcdf.json -ow```

## Objetivo

O objetivo desse tipo de conversão dos arquivos para padrão NetCDF CF é que os dados sejam auto contidos, 
ou seja, uma vez que o usuário tenha o arquivo NetCDF ele contém todas as informações relevantes para 
uso do mesmo. O usuário não precisa procurar informações adicionais como posição GPS da estação, tipo de 
equipamento, medidas e unidades, intervalo de amostragem, etc. O padrão CF vem sendo adotado por
diversos institutos pelo mundo para distribuição de dados de Clima e Previsão. Este formato também vem
sendo utilizado por agências de dados climáticos observacionais, entretanto ainda existem alguns problemas
sem resposta para esse tipo de aplicação. Acreditasse que isso deve ser corrigido no padrão em breve.
Todos os metadados incluídos no arquivo NetCDF podem ser utilizados em um serviço de indexação para que os
mesmos sejam encontrador facilmente. 

## Como fazer o dump dos arquivos netcdf
```ncdump {nome_do_arquivo} -h```
 