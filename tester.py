import time
import uuid
import datetime

# Configuration
FILE_PATH = "logSelfcheckout.log"
TID = "TID(0x7fc9adb6e700)"


def get_timestamp():
    # Format: [YYYY-MM-DD HH:MM:SS:MS]
    now = datetime.datetime.now()
    return (
        f"[{now.strftime('%Y-%m-%d %H:%M:%S')}:"
        f"{now.microsecond // 1000:03d}]"
    )


def write_packet(xml_content):
    """Writes a log packet to the file, appending to existing content."""
    ts = get_timestamp()
    log_line = f"{ts}[INFO]: {TID} [ScoAdapter] CONTENT [{xml_content}]\n"
    
    try:
        with open(FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
            f.flush()
        print(f"Logged event at {ts}")
    except IOError as e:
        print(f"Error writing to file: {e}")


def generate_scenario():
    transacao_id = str(uuid.uuid4())
    print(f"--- Generating New Transaction: {transacao_id} ---")
    print("Ensure main.py is running to see the parsed output.")

    # 1. START TRANSACTION
    xml_start = f"""<message id="StartTransaction" msgid="b2"
     name="StartTransaction">
    <fields>
      <field ftype="string" name="Id">{transacao_id}</field>
      <field ftype="int" name="SuspendAllowed">1</field>
    </fields>
  </message>"""
    write_packet(xml_start)
    time.sleep(1)

    # 2. ITEM 1: Leite
    xml_item1 = """<message id="ItemSold" msgid="b2" name="ItemSold">
    <fields>
      <field ftype="string" name="Description">LEITE UHT M/G 1L</field>
      <field ftype="int" name="Price">89</field>
      <field ftype="int" name="ExtendedPrice">89</field>
      <field ftype="int" name="Quantity">1</field>
      <field ftype="boolean" name="VoidFlag">0</field>
    </fields>
  </message>"""
    write_packet(xml_item1)
    
    # Totals (Usually accompanies items)
    time.sleep(2)

    # 3. INTERVENTION (Age Check)
    print("Simulating Intervention...")
    xml_intervencao = """<message id="DataNeeded" msgid="b2" name="DataNeeded">
    <fields>
      <field ftype="string" name="SummaryInstruction.1">
      NcrKey_ConfirmAge</field>
      <field ftype="int" name="EnterAssistMode">1</field>
    </fields>
  </message>"""
    write_packet(xml_intervencao)
    time.sleep(3)
    
    # 4. INTERVENTION FINISH
    print("Resolving Intervention...")
    xml_intervencao_fim = """<message name="DataNeededReply">
    <fields>
      <field ftype="string" name="Id">OperatorOverride</field>
    </fields>
  </message>"""
    write_packet(xml_intervencao_fim)
    time.sleep(1)

    # 5. PAYMENT START
    print("Starting Payment...")
    xml_tender_mode = """<message name="EnterTenderMode">
    <fields>
      <field ftype="boolean" name="TrainingMode">0</field>
    </fields>
  </message>"""
    write_packet(xml_tender_mode)
    time.sleep(2)

    # 6. END TRANSACTION
    print("Finishing Transaction...")
    xml_end = f"""<message id="EndTransaction" msgid="b2"
     name="EndTransaction">
    <fields>
      <field ftype="string" name="Id">{transacao_id}</field>
      <field ftype="int" name="Complete">1</field>
    </fields>
  </message>"""
    write_packet(xml_end)
    print("--- Transaction Complete ---")


if __name__ == "__main__":
    generate_scenario()