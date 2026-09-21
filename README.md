# Bot WhatsApp

Script em Python que envia um texto pelo **WhatsApp Web**, uma mensagem por linha, de forma lenta e com pausas, para **uma pessoa ou um grupo**. Pensado para brincadeiras entre amigos (por exemplo, enviar aos poucos o roteiro de um filme).

Ele usa Selenium para controlar o Chrome. Não é uma API oficial do WhatsApp.

## Avisos

- Automatizar o WhatsApp Web **viola os termos de uso** do WhatsApp e pode levar ao **banimento do número**, mesmo indo devagar. Use por sua conta e risco, de preferência com um número secundário.
- Envie apenas para quem vai **gostar da brincadeira**. Bloqueios e denúncias são o principal motivo de banimento.
- Em **grupos** o risco é maior (mais gente para denunciar ou silenciar). Avise o grupo antes e considere um limite diário menor (`--limite 50`).
- Não coloque no roteiro conteúdo protegido por direitos autorais que você não tenha o direito de distribuir.

## Como funciona

- Lê o `roteiro.txt` e envia cada linha não vazia como uma mensagem.
- Intervalo **aleatório de 20 a 45 s** entre mensagens.
- Pausa longa de **3 a 5 min** a cada 25 mensagens.
- Limite de **150 mensagens por dia** (ajustável com `--limite`). O limite vale para a **conta inteira**, somando todos os destinos, porque o risco de banimento é da conta.
- Salva o progresso em `progresso.json`, separado por destino (cada pessoa ou grupo tem o seu ponto). Se você parar (Ctrl+C) ou o limite diário for atingido, é só rodar de novo com o mesmo destino que ele continua de onde parou.
- O login fica salvo na pasta `perfil_chrome`, então o QR code só é pedido na primeira vez.

Os valores (intervalos, lote e limite diário) ficam no topo do `enviar.py` e podem ser ajustados.

## Requisitos

- Python 3.9 ou superior
- Google Chrome (ou Chromium no Linux)
- Conexão com a internet e o WhatsApp instalado no celular

O driver do Chrome é baixado automaticamente pelo Selenium (versão 4.6 ou superior).

## Instalação

### Windows (PowerShell)

```powershell
git clone https://github.com/VitoEmanoel/Bot_whatsApp.git
cd Bot_whatsApp
python -m pip install -r requirements.txt
```

Opcional, para isolar as dependências em um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip chromium
git clone https://github.com/VitoEmanoel/Bot_whatsApp.git
cd Bot_whatsApp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se preferir o Google Chrome em vez do Chromium, instale o `.deb` oficial. O script precisa de uma interface gráfica (desktop), pois abre a janela do navegador para você escanear o QR code.

## Configuração do roteiro

O `roteiro.txt` **não vem no repositório** (está no `.gitignore`). Crie o seu a partir do exemplo:

```bash
# Linux / macOS
cp roteiro.exemplo.txt roteiro.txt
```

```powershell
# Windows
Copy-Item roteiro.exemplo.txt roteiro.txt
```

Abra o `roteiro.txt` e cole o seu texto: **uma mensagem por linha**. Linhas em branco são ignoradas. Emojis são removidos automaticamente, pois o Chrome não consegue digitá-los.

> Dica: textos muito grandes levam muito tempo. Com 150 mensagens por dia, 300 linhas levam 2 dias. Corte o texto para o tamanho que quiser enviar.

## Uso

Você escolhe **um** destino: uma pessoa (pelo número) ou um grupo (pelo nome).

### Para uma pessoa

Informe o número com **DDI + DDD + número**, só dígitos, sem `+`, espaços ou traços. Exemplo: (11) 99999-0000 no Brasil vira `5511999999999`.

Windows:

```powershell
python enviar.py 5511999999999
```

Linux:

```bash
python3 enviar.py 5511999999999
```

### Para um grupo

Informe o **nome** do grupo entre aspas. Sua conta precisa já participar do grupo.

Na comparação, o script **ignora** emojis, maiúsculas/minúsculas e espaços repetidos ou nas pontas. Portanto, não é preciso digitar o emoji: para um grupo chamado `Amigos 😎`, basta `--grupo "Amigos"`. Por outro lado, **acentos** e **espaços entre as palavras contam**: `Ação` e `Acao` são nomes diferentes, assim como `OsBrabos` e `Os Brabos`.

Windows:

```powershell
python enviar.py --grupo "Nome do Grupo"
```

Linux:

```bash
python3 enviar.py --grupo "Nome do Grupo"
```

O script procura o grupo na busca do WhatsApp Web e só abre um resultado cujo título combine com o nome informado. Se não achar, ele para com uma mensagem de erro e mostra os resultados que a busca retornou, sem enviar nada. Se houver dois grupos que só se diferenciam pelos emojis (por exemplo `Amigos 😎` e `Amigos 🔥`), ele também para e lista os dois; nesse caso, cole o nome completo com o emoji no comando ou renomeie um dos grupos.

### Opções

| Opção | Descrição |
|---|---|
| `--grupo "Nome"` | Envia para um grupo em vez de uma pessoa |
| `--limite N` | Máximo de mensagens por dia, somando todos os destinos (padrão 150) |

Exemplo: `python enviar.py --grupo "Amigos" --limite 50`

### Primeira execução

1. O Chrome abre o WhatsApp Web.
2. No celular: WhatsApp → **Aparelhos conectados** → **Conectar um aparelho**.
3. Escaneie o QR code.
4. Quando a conversa abrir, o envio começa sozinho.

Nas próximas execuções não é necessário escanear de novo.

### Durante o envio

- Deixe o computador ligado (sem hibernar) e a janela do Chrome aberta. Pode minimizar.
- Não mexa na conversa dentro dessa janela.
- O terminal mostra o andamento: `[12/300] texto...`
- Para parar: **Ctrl+C**. O progresso é salvo.

### Continuar depois

Rode o mesmo comando (mesmo número ou mesmo nome de grupo). Ele retoma da próxima mensagem. Se o limite diário foi atingido, o script avisa e você continua no dia seguinte.

Para **recomeçar do zero**, apague o `progresso.json`.

## Solução de problemas

| Problema | Solução |
|---|---|
| `SessionNotCreatedException` / "Chrome failed to start: crashed" | Ficou um Chrome do script aberto usando o `perfil_chrome`. Feche-o (veja abaixo) e rode de novo. |
| A conversa não abre / timeout | Confira o número (DDI + DDD) e se a pessoa tem WhatsApp. |
| `Grupo "..." não encontrado` | Confira acentos e espaços entre as palavras (emojis e maiúsculas não importam) e se sua conta está no grupo. O erro mostra os resultados da busca para você comparar. |
| `Mais de um grupo combina com esse nome` | Há grupos que só diferem nos emojis. Use o nome completo, com o emoji, ou renomeie um deles. |
| Não encontra a caixa de busca / dá timeout ao carregar | O WhatsApp Web mudou o layout. O seletor `CAIXA_BUSCA` no topo do `enviar.py` precisa de ajuste. |
| Não digita nada | O WhatsApp pode ter mudado o layout do site; o seletor em `enviar.py` precisa de ajuste. |
| `pip` não é reconhecido (Windows) | Use `python -m pip install -r requirements.txt`. |
| Pede QR code toda vez | A pasta `perfil_chrome` foi apagada ou está sem permissão de escrita. |

### Encerrar Chrome preso ao perfil

Windows (PowerShell):

```powershell
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -match 'perfil_chrome' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Linux:

```bash
pkill -f perfil_chrome
```

## Estrutura

```
.
├── enviar.py              # script principal
├── requirements.txt       # dependências (selenium)
├── roteiro.exemplo.txt    # modelo do roteiro
├── roteiro.txt            # seu texto (local, não versionado)
├── progresso.json         # progresso do envio (local, não versionado)
├── perfil_chrome/         # sessão do WhatsApp Web (local, não versionado)
└── README.md
```

Nunca publique o `perfil_chrome`: ele contém a sessão logada da sua conta.
