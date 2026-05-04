# Monitoramento de Sites com Telegram

Este projeto testa os sites e envia um resumo para o Telegram em toda execução.

## O que ele envia

Se estiver tudo certo:

✅ Monitoramento - Tudo certo
Total testado: 3
OK: 3
Problemas: 0

Se tiver erro:

⚠️ Monitoramento - ATENÇÃO
Mostra qual site falhou e o detalhe.

## Arquivos principais

- monitorar.py
- config.json
- executar_monitoramento.bat
- executar_monitoramento_silencioso.bat

## Como configurar Telegram

### 1. Criar o bot

1. Abra o Telegram.
2. Pesquise por BotFather.
3. Envie:

/newbot

4. Escolha um nome.
5. Escolha um usuário para o bot, terminando com bot.
6. Copie o token que ele entregar.

### 2. Ativar conversa com o bot

1. Abra o bot que você criou.
2. Clique em Start ou envie qualquer mensagem para ele.

### 3. Descobrir seu chat_id

No navegador, acesse:

https://api.telegram.org/botSEU_TOKEN_AQUI/getUpdates

Troque SEU_TOKEN_AQUI pelo token real.

Procure por:

"chat":{"id":123456789

Esse número é o seu chat_id.

### 4. Preencher config.json

Abra o arquivo config.json e preencha:

"telegram": {
    "ativo": true,
    "bot_token": "COLE_SEU_TOKEN_AQUI",
    "chat_id": "COLE_SEU_CHAT_ID_AQUI"
}

## Como testar

Dê dois cliques em:

executar_monitoramento.bat

## Como usar no Agendador de Tarefas

Use este arquivo:

executar_monitoramento_silencioso.bat

Assim o Windows roda a automação sem ficar esperando apertar tecla.

## Rodar a cada 30 minutos

No Agendador de Tarefas:

1. Criar Tarefa Básica
2. Nome: Monitoramento Sites
3. Diariamente
4. Iniciar um programa
5. Programa/script:
   C:\monitoramento_sites\executar_monitoramento_silencioso.bat
6. Depois abra a tarefa criada
7. Aba Disparadores
8. Editar
9. Marcar: Repetir tarefa a cada 30 minutos
10. Duração: Indefinidamente