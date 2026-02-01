import time
import re
import json
import sys
import os

# Caminhos dos ficheiros
INPUT_LOG = 'logSelfcheckout.log'
OUTPUT_LOG = 'parser.log'

# Padrões Regex Compilados para Performance
REGEX = {
    'start': re.compile(r'<message id="StartTransaction".*?name="Id">(.*?)<', re.DOTALL),
    'end': re.compile(r'<message id="EndTransaction"'),
    # Item: Captura Descrição, Preço Unitário, Preço Extendido e Quantidade
    'item': re.compile(
        r'<message id="ItemSold".*?name="Description">(.*?)<.*?'
        r'name="Price">(\d+)<.*?'
        r'name="ExtendedPrice">(\d+)<.*?'
        r'name="Quantity">(\d+)<',
        re.DOTALL
    ),
    # Intervenções (Start/End) - Captura EnterAssistMode OU DataNeeded relevante
    'intervention_start': re.compile(r'<message name="(EnterAssistMode|DataNeeded)".*?name="SummaryInstruction\.1">(.*?)<', re.DOTALL),
    'intervention_end': re.compile(r'<message name="(ExitAssistMode|DataNeededReply)"'),
    # Pagamento
    'tender_start': re.compile(r'<message name="EnterTenderMode"'),
    'tender_done': re.compile(r'<message id="TenderAccepted".*?name="Amount">(\d+)<.*?name="TenderType">(.*?)<', re.DOTALL)
}

class TransactionMonitor:
    def __init__(self):
        self.current_tx = None

    def init_transaction(self, tx_id, timestamp):
        # Se já existe uma aberta, fecha-a antes de criar nova (caso o log tenha sido cortado)
        if self.current_tx:
            self.save_transaction("FORCE_CLOSE_NEW_STARTED")
        
        self.current_tx = {
            "id": tx_id,
            "start_time": timestamp,
            "end_time": None,
            "status": "IN_PROGRESS",
            "items": [],
            "events": [], # Intervenções e Pagamentos
            "total_value": 0.0
        }
        print(f"[{timestamp}] 🟢 Nova Transação Iniciada: {tx_id}")

    def add_item(self, name, qty, price_cents, ext_price_cents, timestamp):
        if not self.current_tx: return

        # Lógica de preço: Se unitário for 0, usa o extendido
        final_cents = ext_price_cents if price_cents == 0 else (price_cents * qty) # Assumindo price unitário
        # Nota: Nos logs NCR, às vezes Price é unitário, às vezes zero. Extended é o total da linha.
        # Vamos confiar no ExtendedPrice se Price for 0.
        val = ext_price_cents if price_cents == 0 else ext_price_cents # Geralmente ExtendedPrice é o valor cobrado final
        
        price_euro = val / 100
        
        item = {
            "timestamp": timestamp,
            "description": name,
            "quantity": qty,
            "value": price_euro
        }
        self.current_tx["items"].append(item)
        self.current_tx["total_value"] += price_euro
        print(f"[{timestamp}] 🛒 Item: {name} ({qty}x) - {price_euro:.2f}€")

    def add_event(self, event_type, details, timestamp):
        if not self.current_tx: return
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "details": details
        }
        self.current_tx["events"].append(event)
        print(f"[{timestamp}] ℹ️  Evento: {event_type} - {details}")

    def save_transaction(self, status="COMPLETED", end_time=None):
        if not self.current_tx: return

        self.current_tx["status"] = status
        if end_time:
            self.current_tx["end_time"] = end_time

        # Escrever no parser.log (Append mode)
        try:
            with open(OUTPUT_LOG, 'a', encoding='utf-8') as f:
                json.dump(self.current_tx, f, ensure_ascii=False)
                f.write('\n') # Nova linha para o próximo JSON (JSON Lines format)
            print(f"[{end_time or '---'}] 💾 Transação Guardada em {OUTPUT_LOG}")
        except Exception as e:
            print(f"Erro ao gravar JSON: {e}")
        
        # Reset
        self.current_tx = None

def follow(thefile):
    '''Gerador que simula o tail -f'''
    thefile.seek(0, 2) # Vai para o final do ficheiro
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1) # Aguarda nova escrita
            continue
        yield line

def main():
    print(f"--- A monitorizar {INPUT_LOG} ---")
    print("Pressione Ctrl+C para parar.")
    
    monitor = TransactionMonitor()
    
    try:
        with open(INPUT_LOG, 'r', encoding='utf-8', errors='ignore') as logfile:
            # Loop infinito a ler novas linhas
            for line in follow(logfile):
                # Extrair Timestamp da linha
                ts_match = re.search(r'^\[(.*?)]', line)
                timestamp = ts_match.group(1) if ts_match else "Unknown"

                # 1. Início
                start_match = REGEX['start'].search(line)
                if start_match:
                    monitor.init_transaction(start_match.group(1), timestamp)
                    continue

                # Se não temos transação ativa, ignoramos o resto (ou criamos uma dummy se necessário)
                if not monitor.current_tx:
                    continue

                # 2. Artigos
                item_match = REGEX['item'].search(line)
                if item_match:
                    monitor.add_item(
                        name=item_match.group(1).strip(),
                        price_cents=int(item_match.group(2)),
                        ext_price_cents=int(item_match.group(3)),
                        qty=int(item_match.group(4)),
                        timestamp=timestamp
                    )

                # 3. Intervenções
                if "DataNeeded" in line or "EnterAssistMode" in line:
                    int_start = REGEX['intervention_start'].search(line)
                    if int_start:
                        instr = int_start.group(2)
                        if "NcrKey_Please_wait" not in instr and "Loading" not in instr:
                            monitor.add_event("INTERVENTION_NEEDED", instr, timestamp)
                
                if "DataNeededReply" in line or "ExitAssistMode" in line:
                    if REGEX['intervention_end'].search(line):
                         monitor.add_event("INTERVENTION_RESOLVED", "Input Recebido", timestamp)

                # 4. Pagamento
                if REGEX['tender_start'].search(line):
                    monitor.add_event("PAYMENT_MODE", "Iniciou Pagamento", timestamp)
                
                tender_match = REGEX['tender_done'].search(line)
                if tender_match:
                    amount = int(tender_match.group(1)) / 100
                    method = tender_match.group(2)
                    monitor.add_event("PAYMENT_SUCCESS", f"{amount} via {method}", timestamp)

                # 5. Fim
                if REGEX['end'].search(line):
                    monitor.save_transaction("COMPLETED", timestamp)

    except KeyboardInterrupt:
        # Salva o estado atual se o utilizador cancelar a meio
        if monitor.current_tx:
             monitor.save_transaction("ABORTED_BY_USER")
        print("\nMonitorização parada pelo utilizador.")
        sys.exit(0)
    except FileNotFoundError:
        print(f"Erro: O ficheiro {INPUT_LOG} não existe.")

if __name__ == "__main__":
    main()
