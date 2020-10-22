# GBDServer

Configuracao de servidor para uso no GBDHidro. 

## Servidor para teste local:

O servidor roda localmente através do docker, e conta com banco de dados MongoDB e um tranferencia de arquivo SFTP. 
Para iniciar o servidor: 

```docker-compose -f gbdserver_docker_test.yml up```

Para executar o servidor e retornar à linha de comando:

```docker-compose -f gbdserver_docker_test.yml up -d```

Para encerrar o servidor utilize ctrl+c. Caso ele esteja em segundo plano:

```docker-compose -f gbdserver_docker_test.yml stop```


As credenciais para acesso são:
- sftp: host: sftp://localhost, port: 2222, user: foo, password: pass
- mongodb: host: localhost, port: 17017, user: root, password: example 

## Dependencias

É necessário ter o docker e o docker-compose instalado para utilizar esta configuração.