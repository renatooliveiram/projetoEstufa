# Estufa Inteligente utilizando Aprendizado por Reforço

Disciplina: Inteligência Artificial I — Engenharia da Computação.
Relatório técnico da implementação simulada. Confirmar autoria e identificação
acadêmica antes da entrega; não foram inferidas a partir do PDF de referência.

## 1. Objetivo e escopo

Implementou-se uma estufa simulada em Python, na qual um agente Q-Learning
aprende a controlar irrigação, ventilação e iluminação para manter temperatura,
umidade e luminosidade em faixas definidas. O escopo segue o PDF da Parte 1:
ambiente computacional, estados, ações, recompensas, treinamento, avaliação e
gráficos. Não há hardware, sensores ou redes neurais. Todos os parâmetros
ambientais são didáticos, não medições nem recomendações de uma cultura.

## 2. Modelagem

| Variável | Limites | Faixa desejada | Inicialização |
|---|---|---|---|
| Temperatura | 10–40 °C | 20–26 °C | 18–32 °C |
| Umidade (índice) | 0–100% | 50–70% | 30–85% |
| Luminosidade | 0–1.200 lux | 600–900 lux | 200–1.100 lux |

Cada variável é classificada como baixa (0), ideal (1) ou alta (2), incluindo
os limites na faixa ideal. Existem 27 estados e 8 combinações ligado/desligado
dos três equipamentos. A linha da Q-Table é 9T + 3U + L, usando categorias.
O ambiente mantém os valores contínuos internamente. Um passo é uma decisão,
sem duração física calibrada. As ações definem a configuração daquele passo.

Com I, V e L iguais a 0 ou 1, as transições implementadas são:

- T seguinte = T + 0,1(28 − T) − V.
- U seguinte = U − 2 + 6I.
- B seguinte = B + 0,5[(400 + 400L) − B].

T é temperatura, U umidade e B luminosidade. Os valores são limitados aos
intervalos da tabela. As transições são determinísticas e simplificadas.
As condições iniciais são sorteadas dentro dos intervalos indicados.

A pontuação por variável após a ação é +1 dentro da faixa; fora, é
−min(3, d/k), sendo d a distância à faixa e k igual a 5 °C, 20 pontos
percentuais ou 300 lux. A recompensa total soma as três pontuações e desconta
0,05 por equipamento ligado. A adequação ambiental tem prioridade sobre esse
custo abstrato, que não representa consumo físico ou monetário.

## 3. Algoritmo e treinamento

A Q-Table possui 27 × 8 valores, inicialmente zero, armazenados em listas Python.
A atualização é:

Q(s,a) ← Q(s,a) + α [r + γ max Q(s',a') − Q(s,a)].

Q(s,a) estima o retorno de uma ação no estado; r é a recompensa; s' é o novo
estado. α = 0,10 controla o ajuste e γ = 0,95 o desconto futuro. Com
probabilidade ε o agente sorteia uma ação; caso contrário escolhe um máximo
da linha, sorteando entre empates. ε começa em 1, é multiplicado por 0,995
uma vez por episódio e tem piso de 0,05. São valores iniciais, não otimizados.

O treino usa 1.000 episódios de 200 passos, totalizando 200.000 decisões.
As sementes são 42 para o ambiente e 43 para o agente. O corte de 200 passos
não é um terminal físico: o último passo preserva o valor futuro e é atualizado
antes do reset. Atingir a faixa ideal não encerra o episódio. A tabela é
mantida entre episódios, mas cada nova execução padrão começa do zero.

## 4. Testes e avaliação

Os 42 testes automatizados verificam ambiente (17), agente (13), treinamento
(5) e avaliação (7). Cobrem transições, limites, estados, recompensa, cálculo
Q, exploração, persistência, contagens e reprodutibilidade. A avaliação não
atualiza Q nem reduz ε. O fluxo completo foi integrado em main.py.

Na avaliação, 100 condições iniciais são sorteadas com semente 2026. Para cada
uma, executam-se 200 passos com cada estratégia, partindo dos mesmos valores.
A referência sorteia uniformemente as oito ações (semente 2027); o treinado usa
explorar=False e a tabela fixa, com semente 2028 para empates. Os percentuais
usam as condições após cada ação, incluindo recuperação inicial. É um
experimento separado, não os primeiros versus últimos episódios do treino.

## 5. Resultados de referência

No treinamento, a recompensa média passou de 113,18 nos primeiros 100 episódios
para 503,86 nos últimos 100. O tempo com todas as variáveis ideais passou de
4,84% para 66,07%. O ε final foi 0,05 e 176 dos 216 valores Q ficaram diferentes
de zero. Alterar a tabela, isoladamente, não comprova bom controle.

| Indicador da avaliação | Aleatório | Treinado |
|---|---:|---:|
| Recompensa média por episódio | 27,34 | 509,12 |
| Temperatura ideal | 98,08% | 98,75% |
| Umidade ideal | 6,26% | 66,68% |
| Luminosidade ideal | 50,04% | 99,78% |
| Todas simultaneamente ideais | 2,90% | 65,94% |
| Irrigação ligada | 49,73% | 32,74% |
| Ventilação ligada | 50,13% | 33,67% |
| Iluminação ligada | 49,98% | 99,78% |

O treinado teve maior recompensa nos 100 pares. A adequação simultânea aumentou
63,04 pontos percentuais. A temperatura já apresentava alta adequação com
ações aleatórias; os maiores ganhos estão na umidade e na luz. A principal
limitação observada é a umidade, adequada em 66,68% dos passos.

Irrigação e ventilação foram menos usadas, mas a iluminação permaneceu ligada
quase sempre. Isso é compatível com a dinâmica: desligada tende a 400 lux,
abaixo do alvo; ligada tende a 800 lux. Não se pode concluir economia global
de energia, pois potências e consumo físico não foram modelados.

## 6. Interpretação dos gráficos

- 01_treinamento.png: recompensa por episódio, média móvel de 50 episódios e
  epsilon. Há melhora geral e oscilações. A causa específica da queda temporária
  perto do episódio 500 não foi isolada experimentalmente.
- 02_faixas_ideais.png: adequação por variável e simultânea usando toda a avaliação.
- 03_recompensas_avaliacao.png: recompensa em cada par de episódios, sem omitir pontos.
- 04_condicoes_ambientais.png: trajetórias do episódio 1, escolhido previamente
  como exemplo, com faixas sombreadas. Não representa a média. Nesse episódio,
  a umidade oscila perto do limite inferior.
- 05_uso_equipamentos.png: proporção de passos ligados, não consumo real.

## 7. Conclusão e limitações

O objetivo mínimo foi atendido: uma simulação executável com Q-Learning,
treinamento, avaliação reproduzível, métricas e gráficos. Houve melhora em
relação à referência aleatória nas condições testadas, sem controle perfeito.

As três categorias por variável agrupam valores contínuos diferentes e perdem
informação sobre distância aos limites. O ambiente não inclui ruído, ciclo
dia/noite, espécies vegetais, calibração ou dinâmica física detalhada. Foi
avaliada uma tabela, sem múltiplas sementes independentes de treinamento.
Não se comparou com controle por regras ou PID. Portanto, não se demonstrou
convergência, otimalidade, superioridade a outros controladores ou aplicação real.

Próximos estudos podem repetir o treino com outras sementes, comparar com regras
fixas e refinar os estados se os resultados justificarem. Uma implementação
física exigiria sensores calibrados, atuadores, limites de segurança e validação
independente. Nada disso integra a versão atual.

## 8. Origem e reprodução

O escopo veio do PDF “Estufa Inteligente utilizando Aprendizado por Reforço”,
Parte 1, e das instruções em “Texto colado .txt”. Os parâmetros são decisões de
modelagem desta implementação. Os resultados vêm dos CSVs/JSONs das etapas 7
e 8, reproduzidos pelo usuário e preservados na pasta resultados deste pacote.
A execução integrada de conferência reproduziu esses números e foi gravada
separadamente. Não são resultados atribuídos aos artigos listados no PDF.

O relatório documenta esta versão experimental. python main.py executa o fluxo
padrão; o README detalha o comando no Windows atual. Alterações de parâmetros
exigem novos resultados e atualização do texto antes da entrega acadêmica.
