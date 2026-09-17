# Roteiro de apresentação — aproximadamente 5 minutos

## Objetivo (40 segundos)

“O projeto é uma estufa simulada em Python. Usamos Q-Learning para aprender a
controlar temperatura, umidade e luminosidade, ligando e desligando irrigação,
ventilação e iluminação. Esta versão não utiliza hardware e seus parâmetros
são didáticos.”

## Funcionamento (1 minuto)

“Cada variável pode estar baixa, ideal ou alta: são 27 estados. Os três
equipamentos formam 8 ações. O agente observa, age, recebe uma recompensa e
atualiza a tabela Q. Condições adequadas aumentam a pontuação, enquanto desvios
e uso dos equipamentos têm penalidades. Não fornecemos regras prontas de controle.”

## Treinamento (45 segundos)

Abra 01_treinamento.png.

“Executamos mil episódios com 200 decisões cada. A exploração começa alta e
diminui até 5%. A recompensa melhora, com oscilações. Esse gráfico sozinho não
comprova a qualidade final, então fazemos uma avaliação separada.”

## Avaliação (1 minuto)

Abra 02_faixas_ideais.png e, se necessário, 03_recompensas_avaliacao.png.

“Comparamos o agente treinado e ações aleatórias em cem episódios, com as
mesmas condições iniciais em cada par. A tabela fica fixa. O tempo com tudo
adequado passou de 2,90% no aleatório para 65,94% no treinado. A recompensa
média foi 27,34 contra 509,12. A umidade ainda precisa melhorar.”

## Demonstração e conclusão (1 minuto)

Abra 04_condicoes_ambientais.png.

“Este é o episódio 1, apenas um exemplo; a faixa verde indica o intervalo
desejado. A avaliação geral usa todos os episódios. O projeto demonstra
aprendizado por reforço, mas não é um modelo agronômico validado. Próximos
passos incluem várias sementes de treino e comparação com regras fixas.”

Se houver tempo, execute main.py com o comando do README. Ele cria novas pastas
e preserva o trabalho anterior. Instale dependências e teste antes da aula;
tenha também as imagens prontas para não depender da execução ao vivo.

## Perguntas prováveis

**Por que Q-Learning?** A tabela pequena permite uma implementação simples,
inspecionável e compatível com o objetivo didático.

**O que é epsilon?** A probabilidade de explorar uma ação. Na avaliação,
explorar=False ignora epsilon e escolhe entre os máximos conhecidos.

**O agente melhorou?** Sim, frente à referência aleatória neste experimento,
em recompensa e adequação ambiental. Não é prova de otimalidade.

**Por que a umidade oscila?** No exemplo, as ações alternam perto do limite
inferior: irrigar soma 4 pontos líquidos e não irrigar remove 2. As categorias
perdem informação sobre distância ao limite; avaliar uma discretização melhor
exigiria outro experimento. Não identificamos uma causa única comprovada.

**Por que a luz fica ligada?** Desligada tende a 400 lux, abaixo do alvo;
ligada tende a 800 lux. Isso decorre do modelo implementado.

**Economiza energia?** Não medimos energia; só passos ligados e custo abstrato.

**Construíram a estufa física?** Não. O escopo é uma simulação computacional.
