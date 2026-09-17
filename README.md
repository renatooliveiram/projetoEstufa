# Estufa inteligente — projeto organizado

Simulação em Python com Q-Learning tabular: 27 estados, 8 ações, treinamento,
avaliação e gráficos. Abra ESTA pasta no VS Code, a que contém main.py.

## Começar no VS Code (Windows)

1. Extraia o ZIP para uma pasta nova, mantendo sua versão anterior como backup.
2. Em Arquivo → Abrir Pasta, escolha a pasta projeto_estufa que contém main.py.
3. Abra Terminal → Novo Terminal e execute, um comando por vez:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se o comando py não existir e python funcionar, use python -m venv .venv.
Este ambiente é novo e está DENTRO da pasta organizada. Não use os antigos
caminhos ..\.venv ou ..\.venv-1.

4. Pressione Ctrl+Shift+P → Python: Select Interpreter → escolha
   .venv\Scripts\python.exe desta pasta.
5. Abra main.py e use Executar Arquivo Python no Terminal (▶).
   Alternativa: F5 → Executar estufa (main.py).

Requer a extensão Python da Microsoft. O pacote sugere a extensão, mas não a
instala automaticamente. Não precisa ativar o ambiente no PowerShell.

A execução cria novas subpastas de resultados, sem apagar as anteriores.
Ela faz treino de 1.000 episódios, avaliação de 100 episódios por estratégia
e cinco gráficos. Aguarde PROJETO CONCLUÍDO. Os PNGs devem ser abertos na pasta
indicada; não aparecem automaticamente em uma janela.

## Organização

| Local | Conteúdo |
|---|---|
| main.py | Entrada principal do projeto |
| ambiente.py, agente.py, config.py | Simulação, Q-Learning e parâmetros |
| treinamento.py, avaliacao.py, graficos.py | Etapas de execução |
| tests/ | Quatro módulos de testes, com 42 testes |
| executar_testes.py | Executa todos os testes pelo botão ▶ |
| docs/ | Relatório, roteiro e registro desta organização |
| resultados/ | Dados e gráficos enviados, preservados |
| requirements.txt | Dependência para os gráficos |
| .vscode/ | Configuração local do interpretador, execução e testes |

Os módulos principais permanecem juntos para manter os imports simples.
Não foi alterada a dinâmica da estufa, a recompensa ou os parâmetros.

## Testar

Abra executar_testes.py e clique em ▶. A saída deve terminar em 42 testes e OK.
Pelo terminal, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Não execute individualmente os arquivos dentro de tests pelo botão ▶; use o
executar_testes.py, o comando acima ou o painel de testes do VS Code.

## Reutilizar resultados

O ZIP contém exatamente as três pastas de resultados recebidas:

- resultados/treino_ncns8x9r
- resultados/avaliacao_qykoc4xa
- resultados/graficos_qu9_0z8l

Para avaliar a tabela preservada e gerar novos gráficos sem novo treinamento:

```powershell
.\.venv\Scripts\python.exe main.py --treino "resultados/treino_ncns8x9r"
```

Para somente gerar gráficos a partir dos dados já salvos:

```powershell
.\.venv\Scripts\python.exe graficos.py --treino "resultados/treino_ncns8x9r" --avaliacao "resultados/avaliacao_qykoc4xa"
```

A pasta execucao_plsmwbzf mostrada anteriormente na conversa NÃO veio neste ZIP.
Ela pode continuar na sua pasta antiga. Não foi apagada ou recriada como se
fosse um resultado enviado. Caminhos absolutos dentro dos JSONs antigos são
registros históricos; foram preservados. Os comandos acima usam caminhos novos.

## Dependências e documentos

requirements.txt lista matplotlib; NumPy é instalado como dependência dele.
A organização foi testada com Python 3.12 e Matplotlib 3.10.8. O ambiente do
usuário mostrou Python 3.14 e Matplotlib 3.11.2; essa combinação não foi testada
neste executor. O arquivo não força uma versão antiga sobre a instalação nova.

Abra docs/RELATORIO.md ou docs/ROTEIRO_APRESENTACAO.md e pressione Ctrl+Shift+V
para ler formatado. Foram incluídos os documentos preparados na Etapa 10.
Confirme autoria e identificação antes da entrega acadêmica.

## Resultados de referência e limites

Na avaliação já registrada, recompensa média: 27,34 (aleatório) versus 509,12
(treinado). Todas as variáveis ideais: 2,90% versus 65,94%. A umidade ainda limita
o controle. A simulação é didática, sem comprovação de desempenho físico,
convergência ou superioridade a um controlador por regras.

## Problemas comuns

- main.py não aparece: abra a pasta que contém o arquivo, não a pasta externa.
- Falta matplotlib: instale requirements.txt com o Python desta .venv.
- Interpretador antigo: selecione o .venv desta pasta em Select Interpreter.
- Falta resultado: confira os nomes das três pastas acima.
- Uma execução interrompida pode deixar arquivos parciais: aguarde a confirmação
  PROJETO CONCLUÍDO para considerar o fluxo completo.
