# Self-Checkout Log Parser Agent

Este projeto consiste num agente de monitorização de logs para terminais de self-checkout. O sistema lê continuamente um ficheiro de logs (`logSelfcheckout.log`), interpreta o conteúdo XML embebido nos registos e exporta os eventos estruturados para o ecrã e para um ficheiro JSON (`logParcer.json`).

O projeto inclui também um gerador de logs (`tester.py`) para simular transações e testar o funcionamento do parser em tempo real.

## 📂 Estrutura do Projeto

```text
/
├── main.py              # Script principal: monitoriza o log e guarda os dados processados
├── tester.py            # Script de teste: gera logs simulados de transações
├── logSelfcheckout.log  # Ficheiro de entrada: logs em bruto (criado pelo tester.py)
├── logParcer.json       # Ficheiro de saída: eventos processados em formato JSON
└── src/
    ├── parser.py        # Lógica de parsing (Regex + XML)
    ├── models.py        # Definição dos modelos de dados e eventos
    └── ...
```

## 🚀 Pré-requisitos

Para executar este projeto, necessita de:

*   **Sistema Operativo:** Linux (Recomendado)
*   **Python:** Versão 3.x (Utiliza apenas bibliotecas padrão: `re`, `xml`, `json`, `datetime`, etc.)

## 🛠️ Como Executar

O sistema funciona em duas partes: o **monitor** (que lê os dados) e o **gerador** (que escreve os dados). Recomendamos abrir dois terminais.

### 1. Iniciar o Monitor

No primeiro terminal, execute o `main.py`. Este ficará à espera de novos registos no ficheiro de log.

```bash
python3 main.py
```

*Deverá ver a mensagem: `Monitoring logSelfcheckout.log for new events...`*

### 2. Simular Transações

No segundo terminal, execute o `tester.py` para gerar eventos de transação (início, venda de item, intervenção, pagamento, fim).

```bash
python3 tester.py
```

À medida que o `tester.py` escreve no log, o `main.py` irá processar e apresentar os eventos instantaneamente.

## 📄 Output

Os dados processados são guardados em `logParcer.json` no formato JSON Lines (um objeto JSON por linha), permitindo fácil leitura e integração com outras ferramentas.

Exemplo de output:

```json
{
  "timestamp": "2026-02-01 16:16:02:879",
  "event_type": "ItemPicked",
  "details": {
    "Description": "LEITE UHT M/G 1L",
    "Price": 89,
    "Quantity": 1
  }
}
```

## 🐳 Docker (Opcional)

Para garantir um ambiente isolado e reproduzível (especialmente se não estiver em Linux nativo), recomenda-se a criação de um container.

Pode criar um `Dockerfile` na raiz do projeto com o seguinte conteúdo para executar o monitor:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copiar ficheiros do projeto
COPY . .

# Definir volume para persistir logs se necessário
VOLUME ["/app/logs"]

# Comando para iniciar o monitor
CMD ["python3", "-u", "main.py"]
```

Para construir e correr:

```bash
docker build -t logs-agent .
docker run -v $(pwd):/app logs-agent
```
