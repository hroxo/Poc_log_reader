#!/bin/bash

# SCO Monitor — Test Suite
# Based on TEST.md specification

LOG_FILE="/tmp/test_sco.log"
MONITOR="./sco_monitor"
PASS_COUNT=0
FAIL_COUNT=0

cleanup() {
    rm -f "$LOG_FILE" output.json
    if [ -n "$MONITOR_PID" ] && kill -0 "$MONITOR_PID" 2>/dev/null; then
        kill "$MONITOR_PID" 2>/dev/null
        wait "$MONITOR_PID" 2>/dev/null
    fi
}

trap cleanup EXIT

check() {
    local TEST_NAME="$1"
    local PATTERN="$2"
    if grep -q "$PATTERN" output.json; then
        return 0
    else
        echo "  FAIL: expected to find: $PATTERN"
        return 1
    fi
}

# --- Setup ---
rm -f output.json "$LOG_FILE"
touch "$LOG_FILE"

# Start monitor in background
$MONITOR "$LOG_FILE" > /dev/null 2>&1 &
MONITOR_PID=$!
sleep 1

# --- Append test blocks ---

# Block A — Standard ItemSold
cat >> "$LOG_FILE" << 'BLOCK_A'
[2026-01-26 18:46:04:584][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="ItemSold" msgid="b2" name="ItemSold">
    <fields>
      <field ftype="string" name="Description">PIRI PIRI EX.FOR.SAC.PALADIN 75         </field>
      <field ftype="string" name="UPC">5601517310979</field>
      <field ftype="string" name="Department">102</field>
      <field ftype="int" name="ItemNumber">7</field>
      <field ftype="int" name="Price">209</field>
      <field ftype="int" name="ExtendedPrice">156</field>
      <field ftype="int" name="Quantity">1</field>
    </fields>
  </message>]
BLOCK_A
sleep 0.1

# Block B — Discount ItemSold
cat >> "$LOG_FILE" << 'BLOCK_B'
[2026-01-26 18:46:04:635][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="ItemSold" msgid="b2" name="ItemSold">
    <fields>
      <field ftype="string" name="UPC">56015173109791</field>
      <field ftype="int" name="ItemNumber">1007</field>
      <field ftype="int" name="DiscountAmount">53</field>
      <field ftype="string" name="DiscountDescription.1">POUPANCA                  </field>
      <field ftype="int" name="AssociatedItemNumber">7</field>
      <field ftype="int" name="RewardLocation">3</field>
    </fields>
  </message>]
BLOCK_B
sleep 0.1

# Block C — Totals
cat >> "$LOG_FILE" << 'BLOCK_C'
[2026-01-26 18:46:04:687][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="Totals" msgid="b2" name="Totals">
    <fields>
      <field ftype="int" name="TotalAmount">3526</field>
      <field ftype="int" name="ItemCount">7</field>
      <field ftype="int" name="BalanceDue">3526</field>
      <field ftype="int" name="DiscountAmount">639</field>
    </fields>
  </message>]
BLOCK_C
sleep 0.1

# Block D — StartTransaction
cat >> "$LOG_FILE" << 'BLOCK_D'
[2026-01-26 18:55:57:953][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="StartTransaction" msgid="b2" name="StartTransaction">
BLOCK_D
sleep 0.1

# Block E — TenderAccepted
cat >> "$LOG_FILE" << 'BLOCK_E'
[2026-01-26 18:56:55:653][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="TenderAccepted" msgid="b2" name="TenderAccepted">
    <fields>
      <field ftype="int" name="Amount">231</field>
      <field ftype="string" name="TenderType">Credit</field>
      <field ftype="string" name="Description">Cartao Credito</field>
    </fields>
BLOCK_E
sleep 0.1

# Block F — EndTransaction
cat >> "$LOG_FILE" << 'BLOCK_F'
[2026-01-26 18:57:00:911][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="EndTransaction" msgid="b2" name="EndTransaction">
BLOCK_F
sleep 0.1

# Block G — EnterAssistMode & ExitAssistMode
cat >> "$LOG_FILE" << 'BLOCK_G'
[2026-01-27 18:02:01:455][INFO]: TID(0x7fbc8b0cf700) <message name="EnterAssistMode"><fields/></message>
[2026-01-27 18:02:36:171][INFO]: TID(0x7fbc8b0cf700) <message name="ExitAssistMode"><fields/></message>
BLOCK_G

# Wait for processing
sleep 2

# Kill monitor
kill "$MONITOR_PID" 2>/dev/null
wait "$MONITOR_PID" 2>/dev/null
MONITOR_PID=""

# --- Validation ---
echo "========================================"
echo " SCO Monitor — Test Suite"
echo "========================================"
echo ""

# Test A — Standard ItemSold
TEST_PASS=true
check "A" '"event_type":"ItemSold"' || TEST_PASS=false
check "A" '"description":"PIRI PIRI EX.FOR.SAC.PALADIN 75"' || TEST_PASS=false
check "A" '"price":209' || TEST_PASS=false
check "A" '"quantity":1' || TEST_PASS=false
check "A" '"upc":"5601517310979"' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST A] Standard ItemSold ........... PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST A] Standard ItemSold ........... FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test B — Discount ItemSold
TEST_PASS=true
check "B" '"event_type":"Discount"' || TEST_PASS=false
check "B" '"discount_amount":53' || TEST_PASS=false
check "B" '"discount_description":"POUPANCA"' || TEST_PASS=false
check "B" '"upc":"56015173109791"' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST B] Discount ItemSold ........... PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST B] Discount ItemSold ........... FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test C — Totals
TEST_PASS=true
check "C" '"event_type":"Totals"' || TEST_PASS=false
check "C" '"total_amount":3526' || TEST_PASS=false
check "C" '"item_count":7' || TEST_PASS=false
check "C" '"balance_due":3526' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST C] Totals ...................... PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST C] Totals ...................... FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test D — StartTransaction
TEST_PASS=true
check "D" '"event_type":"StartTransaction"' || TEST_PASS=false
check "D" '"data":{}' || TEST_PASS=false
check "D" '"timestamp":"2026-01-26 18:55:57:953"' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST D] StartTransaction ........... PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST D] StartTransaction ........... FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test E — TenderAccepted
TEST_PASS=true
check "E" '"event_type":"TenderAccepted"' || TEST_PASS=false
check "E" '"amount":231' || TEST_PASS=false
check "E" '"tender_type":"Credit"' || TEST_PASS=false
check "E" '"description":"Cartao Credito"' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST E] TenderAccepted .............. PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST E] TenderAccepted .............. FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test F — EndTransaction
TEST_PASS=true
check "F" '"event_type":"EndTransaction"' || TEST_PASS=false
check "F" '"data":{}' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST F] EndTransaction .............. PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST F] EndTransaction .............. FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test G — AssistMode
TEST_PASS=true
check "G" '"event_type":"EnterAssistMode"' || TEST_PASS=false
check "G" '"event_type":"ExitAssistMode"' || TEST_PASS=false
check "G" '"timestamp":"2026-01-27 18:02:01:455"' || TEST_PASS=false
check "G" '"timestamp":"2026-01-27 18:02:36:171"' || TEST_PASS=false
if $TEST_PASS; then
    echo "[TEST G] AssistMode .................. PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "[TEST G] AssistMode .................. FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

echo ""
echo "========================================"
TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo " Results: $PASS_COUNT/$TOTAL PASSED"
echo "========================================"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "--- output.json contents ---"
    cat output.json 2>/dev/null || echo "(empty or missing)"
    exit 1
fi
exit 0
