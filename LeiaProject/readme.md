Fala Reinaldo, segue as instruções para teste (sem Esp32);

°°°°°°Garantir que Notebook e Pepper estejam na MESMA rede wi-fi°°°°°°
1- Rodar Flask no notebook;
2- IP do seu notebook nos códigos : {scriptComTablet.py; Fetchs nos html's}
3- Criar bloco python no choregraphe, colar o código (com o IP correto)
4- Testes de requisições de esp (nao esqueça de trocar o IP) com:
º http://IP:5000/estado?ouvindo=1
º http://IP:5000/update?grupo=1&nivel=1

5- Teste falando "laser" para o robô

Resultados esperados no robô (em ordem):
“Estou ouvindo vocês”
“Indo até o grupo 1”
“Cheguei no grupo 1”
- fala após comando de voz -
troca tela no tablet 


HTTPS caso queira dar uma olhada no JSON:
http://IP:5000/estado_sistema
http://IP:5000/estado?ouvindo=1
http://IP:5000/estado_sistema
http://IP:5000/update?grupo=1&nivel=2
http://IP:5000/update?grupo=2&nivel=1
http://IP:5000/estado_sistema
http://IP:5000/next
http://IP:5000/estado_sistema
http://IP:5000/atendimento_start?grupo=2
http://IP:5000/conteudo_set?tipo=laser
http://IP:5000/conteudo
