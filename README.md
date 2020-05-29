# GBD Hidro 
 
## Descrição
Projeto para padrõnização e armazenamento de dados de estações meteorológicas. Os dados são convertidos 
para arquivos netCDF (.nc).
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
- netcdf4: biblioteca para escrita e leitura de arquivos .nc.

```pip install netcdf4```
- cfchecker: biblioteca para verificação de padrão CF do arquivo .nc

```pip install cfchecker```
