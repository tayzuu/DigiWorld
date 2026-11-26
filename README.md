# DigiWorld — bot inicial de captura de Digimon

Este é um MVP em Python para Discord. Ele já inclui:
- aparições automáticas em um canal configurado;
- captura por adivinhação do nome;
- coleção individual (`!dex`);
- perfil e estatísticas (`!perfil`);
- banco de dados SQLite local;
- comando manual de aparição para administradores (`!spawn`).

## 1. Criar o bot no Discord
1. Acesse https://discord.com/developers/applications
2. Crie uma aplicação chamada **DigiWorld**.
3. Abra a aba **Bot** e crie/adicionar o bot.
4. Em **Privileged Gateway Intents**, habilite **Message Content Intent**.
5. Em OAuth2 > URL Generator, marque `bot` e `applications.commands` (o projeto usa comandos com prefixo).
6. Dê permissões de ver canais, enviar mensagens, incorporar links e ler histórico de mensagens.
7. Abra o link gerado e adicione o bot ao seu servidor.
8. Copie o token do bot. **Não compartilhe esse token com ninguém.**

## 2. Instalar e configurar
Requer Python 3.10 ou superior.

```bash
python -m venv .venv
```

Ative o ambiente virtual:

Windows:
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e coloque o token em `DISCORD_TOKEN`.

## 3. Executar
```bash
python bot.py
```

No servidor Discord:
- use `!configurar` no canal onde quer que os Digimons apareçam;
- use `!spawn` para testar uma aparição;
- use `!dex` para consultar sua coleção;
- use `!perfil` para ver suas estatísticas;
- use `!ajuda` para ver os comandos.

## Observações
- O banco `digworld.sqlite3` é criado automaticamente na primeira execução.
- A lista de Digimons fica no início de `bot.py`, na variável `DIGIMONS`.
- Esta versão usa dicas em texto no lugar de imagens/silhuetas oficiais. O próximo passo pode adicionar imagens próprias/licenciadas, raridades, variantes, evolução e batalhas.
- Para manter o bot online 24 horas, ele precisa rodar em um computador ou serviço de hospedagem que suporte processos Python contínuos. Não coloque o token em repositórios públicos.
