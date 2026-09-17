# Organização da cópia enviada

O ZIP recebido continha main.py e requirements.txt vazios e README da Etapa 4.
O main.py foi restaurado com a integração validada na Etapa 10; requirements.txt
passou a listar matplotlib. README foi atualizado para a nova pasta e um único
ambiente local .venv. A cópia original enviada permanece intacta.

| Arquivo anterior | Novo local |
|---|---|
| testesAgente.py | tests/test_agente.py |
| testesAmbiente.py | tests/test_ambiente.py |
| testesAvaliacao.py | tests/test_avaliacao.py |
| testesTreinamento.py | tests/test_treinamento.py |

As asserções dos testes e os seis módulos principais enviados foram preservados.
executar_testes.py permite executar os testes no VS Code a partir da raiz.
As configurações de VS Code usam caminhos relativos à pasta aberta. Escolha
manualmente o interpretador local caso o editor mantenha a seleção antiga.

Os 12 arquivos nas três pastas de resultados recebidas foram preservados com
os mesmos nomes e bytes, inclusive metadados históricos. Pastas mostradas em
prints mas ausentes no ZIP não foram inventadas. A execução feita para validar
a organização foi gravada fora da entrega para não misturar novos resultados
com os enviados.

Foram acrescentados docs/RELATORIO.md e docs/ROTEIRO_APRESENTACAO.md da Etapa 10.
O material documenta a configuração padrão e requer conferência de autoria.
Ambientes virtuais e caches não integram a entrega; crie .venv na pasta nova.
