## Descrição
Subdiretorios contém os conversores para cada estação. Para automatização do processo de conversão é 
necessário que cada conversor atenda os seguitnes pontos:
- Deve ser capaz de identificar se o arquivo de entrada é do formato correto para a estação. Caso 
não seja deve retornar um código diferente de zero (0). Caso a conversão tenha sido realizada com
sucesso, deve retornar zero
- aceitar os comandos -i fileinput -d outputfolder
bla bla bla bla bla

## Funcionamento
O conversor vai percorrer todos os diretorios em busca de uma executavel .py, e tentar converter
o arquivo de entrada 