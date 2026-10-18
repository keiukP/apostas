# Odds e sinais de valor

Ferramenta informativa: lê odds pré-jogo da [The Odds API](https://the-odds-api.com), compara a melhor odd de cada seleção com a probabilidade média do mercado (sem margem) e mostra os palpites como uma conversa em `site/index.html`, com a liquidação de cada palpite (green, red ou void), contagens e uma banca simulada de 100 €. Odds completas ficam em `site/odds.html`.

Não prevê resultados nem garante lucro. O consenso de mercado também erra.

## Configuração (PowerShell)

```powershell
$env:ODDS_API_KEY = "a_tua_chave"
$env:TELEGRAM_BOT_TOKEN = "token_do_bot"    # só para Telegram
$env:TELEGRAM_CHAT_ID = "id_do_chat"         # só para Telegram
```

Para não ter de repetir, usa `setx` (depois abre um terminal novo).

## Execução

```powershell
python main.py --listar-desportos            # lista desportos ativos, sem gastar quota
python main.py --atualizar                   # uma atualização: odds, resultados, palpites e site
python main.py --atualizar --dia-jogo 2026-10-19 # prepara palpites para 19/10 (Lisboa)
python main.py --continuo --preparar-amanha --intervalo 1440 # prepara o dia seguinte uma vez por dia
python main.py --continuo --intervalo 360    # repete a atualização de 6 em 6 horas (Ctrl+C para parar)
python main.py --site                        # regenera o site a partir de data/palpites.json, sem API
python main.py --atualizar --telegram        # atualiza e envia o resumo
python main.py --telegram --dry-run          # mostra o resumo sem enviar
```

Cada atualização:

1. Pede os resultados dos jogos com palpites pendentes (`/scores`).
2. Fecha os palpites com resultado como green, red ou void. Sem resultado 4 dias após o início, fica void.
3. Pede as odds dos desportos configurados e grava um snapshot em `historico/`.
4. Na simulação diária, regista até 5 favoritos do mercado por jogo (maior probabilidade média), exigindo pelo menos 5 casas e sem odds suspeitas. Os sinais de valor continuam calculados e apresentados separadamente. Com `--dia-jogo AAAA-MM-DD`, escolhes uma data; com `--preparar-amanha`, o próximo dia é recalculado em cada ciclo. A stake é 2% da banca (mínimo 1 €, máximo 5%). Os jogos já iniciados não entram.
5. Grava `data/palpites.json`, `site/index.html` e `site/odds.html`.

A chave `ODDS_API_KEY` é lida só do ambiente. Não é gravada em disco.

Desportos por omissão: Premier League, La Liga, Serie A, Bundesliga, Ligue 1 e Liga dos Campeões. Podes mudar com `--desporto soccer_epl --desporto soccer_spain_la_liga` ou com a variável `ODDS_DESPORTOS`.

## Quota

- Odds: 1 crédito por desporto por atualização (com `--regiao eu` e mercado 1X2).
- Resultados: 2 créditos por desporto, e só quando há palpites pendentes.
- Listagem de desportos: sem custo.

Com 6 desportos e 4 atualizações por dia, o consumo é cerca de 24 créditos/dia, mais os resultados. O plano gratuito tem cerca de 500 créditos por mês, por isso não chega para isto. Opções: menos desportos (`--desporto`), intervalo maior (`--intervalo`), ou um plano pago. Confirma sempre o limite no teu plano.

## Funcionamento contínuo

`--continuo` só corre enquanto o terminal estiver aberto. Para correr sem terminal aberto, cria uma tarefa no Agendador de Tarefas do Windows que execute `python main.py --atualizar` nesta pasta, com `ODDS_API_KEY` definida nas variáveis de ambiente da conta.

O site é um ficheiro estático, mas precisa de um servidor local para o botão de ativar/desativar e a atualização automática. Corre `python servidor.py` (fica em `http://127.0.0.1:8800/index.html`). O servidor expõe `/api/estado` e `/api/ativo`. O estado de ativo/inativo fica em `data/controlo.json` (`controlo.py`) e é lido pelo modo `--continuo`.

Dependências: `pip install tzdata`. O Windows não tem a base de fusos horários do Python, e sem este pacote o horário de Lisboa falha.

## Ficheiros

- `odds_api.py`: cliente da The Odds API.
- `valor.py`: compara odds entre casas e marca sinais de valor. Exige pelo menos 5 casas e uma vantagem de 2 pontos percentuais. Odds isoladas muito acima da mediana são marcadas como suspeitas.
- `relatorio.py`: texto para Telegram, página HTML e envio.
- `analise.py`: matemática base (probabilidade implícita, valor esperado, Kelly limitado, backtest).
- `palpites.py`: regista até 5 palpites por dia de jogo (hora de Lisboa) antes do início, liquida-os contra resultados oficiais (green, red ou void após 4 dias sem resultado).
- `banca.py`: banca simulada de 100 € com stake de 2%, limite de exposição de 10% e stop-loss a 50%.
- `chat.py`: página em formato de conversa com palpites, resultados e contagens.
- `controlo.py`: estado ativo/inativo do modo contínuo (`data/controlo.json`).
- `servidor.py`: servidor local em `127.0.0.1:8800` para o site e o botão de controlo.
- `forma.py`: validação de forma recente (últimos 5 jogos). Só aceita registos completos e com fonte; não estima valores em falta. Ainda não está ligado ao site.
- `data/palpites.json`: estado dos palpites. Não editar à mão.
- `data/palpites_arquivo.json`: palpites retirados de propostas por não serem do dia pedido, com o motivo.
- `site/index.html`: conversa de palpites. `site/odds.html`: odds completas.
- `historico/`: snapshots diários das odds. Servem para validar mais tarde com resultados reais.

## Limitações

- Os dados são só de odds. Forma recente, lesões e estatísticas de jogadores exigem outra fonte (por exemplo, API-Football).
- Os palpites e a banca são simulados, com dinheiro fictício. Não há ligação a casas de apostas e a ferramenta não aposta.
- Nenhum palpite garante lucro. Os resultados passados não garantem resultados futuros.
- Em Portugal, só são legais apostas em operadores licenciados pelo SRIJ.

## Testes

```powershell
python -m pytest -q
```
