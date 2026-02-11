#!/bin/bash
# test.sh — Fast automated test suite for sco_monitor
# Target: full cycle < 300ms (excluding compilation)

LOG_FILE="/tmp/test_sco.log"
OUTPUT="output.json"
PASSED=0
FAILED=0
TOTAL=7

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "  SCO Monitor - Test Suite"
echo "============================================"
echo ""

# --- Cleanup ---
rm -f "$OUTPUT" "$LOG_FILE"
touch "$LOG_FILE"

# --- Compile ---
echo "[1/4] Compiling with 'make re'..."
if ! make re; then
    echo -e "${RED}FATAL: Compilation failed.${NC}"
    exit 1
fi
echo ""

# --- Start monitor ---
echo "[2/4] Starting monitor..."
./sco_monitor "$LOG_FILE" "$OUTPUT" > /dev/null 2>&1 &
MONITOR_PID=$!
sleep 0.2

if ! kill -0 "$MONITOR_PID" 2>/dev/null; then
    echo -e "${RED}FATAL: Monitor failed to start.${NC}"
    exit 1
fi

# --- Inject ALL test blocks at once + measure latency ---
echo "[3/4] Injecting test data + measuring latency..."
T_START=$(date +%s%N)

cat <<'EOF' >> "$LOG_FILE"
[2026-01-26 18:55:57:953][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="StartTransaction" msgid="b2" name="StartTransaction">

    <fields>

      <field ftype="string" name="Id">test-txn-001</field>

    </fields>

  </message>]
[2026-01-30 16:54:06:069][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="ItemSold" msgid="b2" name="ItemSold">

    <fields>

      <field ftype="string" name="Description">RTD JACK DANIEL</field>

      <field ftype="string" name="UPC">5449000168481</field>

      <field ftype="string" name="Department">1403</field>

      <field ftype="int" name="ItemNumber">1</field>

      <field ftype="int" name="Price">299</field>

      <field ftype="int" name="ExtendedPrice">299</field>

      <field ftype="int" name="Quantity">1</field>

    </fields>

  </message>]
[2026-01-26 18:46:04:635][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="ItemSold" msgid="b2" name="ItemSold">

    <fields>

      <field ftype="string" name="UPC">56015173109791</field>

      <field ftype="int" name="ItemNumber">1007</field>

      <field ftype="int" name="DiscountAmount">53</field>

      <field ftype="string" name="DiscountDescription.1">POUPANCA</field>

      <field ftype="int" name="AssociatedItemNumber">7</field>

      <field ftype="int" name="RewardLocation">3</field>

    </fields>

  </message>]
[2026-01-26 18:46:04:687][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="Totals" msgid="b2" name="Totals">

    <fields>

      <field ftype="int" name="TotalAmount">3526</field>

      <field ftype="int" name="ItemCount">7</field>

      <field ftype="int" name="BalanceDue">3526</field>

      <field ftype="int" name="DiscountAmount">639</field>

    </fields>

  </message>]
[2026-01-26 18:56:55:653][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="TenderAccepted" msgid="b2" name="TenderAccepted">

    <fields>

      <field ftype="int" name="Amount">231</field>

      <field ftype="string" name="TenderType">Credit</field>

      <field ftype="string" name="Description">Cartao Credito</field>

    </fields>

  </message>]
[2026-01-27 18:02:01:455][INFO]: TID(0x7fbc8b0cf700) <message name="EnterAssistMode"><fields/></message>
[2026-01-27 18:02:36:171][INFO]: TID(0x7fbc8b0cf700) <message name="ExitAssistMode"><fields/></message>
[2026-01-26 18:57:00:911][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="EndTransaction" msgid="b2" name="EndTransaction">

    <fields>

      <field ftype="string" name="Id">test-txn-001</field>

    </fields>

  </message>]
EOF

# Wait for processing — poll is 50ms, 200ms is plenty
sleep 0.2

T_END=$(date +%s%N)
LATENCY_MS=$(( (T_END - T_START) / 1000000 ))

# --- Stop monitor ---
kill "$MONITOR_PID" 2>/dev/null
wait "$MONITOR_PID" 2>/dev/null || true

# --- Validate ---
echo ""
echo "[4/4] Validating output.json..."
echo ""

if [ ! -f "$OUTPUT" ]; then
    echo -e "${RED}FATAL: $OUTPUT not found!${NC}"
    rm -f "$LOG_FILE"
    exit 1
fi

run_test() {
    local label="$1"
    shift
    local pass=1
    local failed_pattern=""
    for pattern in "$@"; do
        if ! grep -qF "$pattern" "$OUTPUT"; then
            pass=0
            failed_pattern="$pattern"
            break
        fi
    done
    if [ $pass -eq 1 ]; then
        echo -e "  ${GREEN}[PASS]${NC} $label"
        ((PASSED++))
    else
        echo -e "  ${RED}[FAIL]${NC} $label  (missing: $failed_pattern)"
        ((FAILED++))
    fi
}

run_test "A - StartTransaction" \
    '"event_type":"StartTransaction"' \
    '"timestamp":"2026-01-26 18:55:57:953"'

run_test "B - ItemSold" \
    '"event_type":"ItemSold"' \
    '"description":"RTD JACK DANIEL"' \
    '"upc":"5449000168481"' \
    '"price":299' \
    '"quantity":1'

run_test "C - Discount" \
    '"event_type":"Discount"' \
    '"upc":"56015173109791"' \
    '"discount_amount":53' \
    '"discount_description":"POUPANCA"'

run_test "D - Totals" \
    '"event_type":"Totals"' \
    '"total_amount":3526' \
    '"item_count":7' \
    '"balance_due":3526'

run_test "E - TenderAccepted" \
    '"event_type":"TenderAccepted"' \
    '"amount":231' \
    '"tender_type":"Credit"' \
    '"description":"Cartao Credito"'

run_test "F - AssistMode" \
    '"event_type":"EnterAssistMode"' \
    '"event_type":"ExitAssistMode"'

run_test "G - EndTransaction" \
    '"event_type":"EndTransaction"' \
    '"timestamp":"2026-01-26 18:57:00:911"'

echo ""
echo "============================================"
echo -e "  Summary: ${PASSED}/${TOTAL} passed"
echo -e "  Latency: ${LATENCY_MS}ms (target: <300ms)"
echo "============================================"

# --- Cleanup ---
rm -f "$LOG_FILE"

if [ "$PASSED" -eq "$TOTAL" ]; then
    if [ "$LATENCY_MS" -le 300 ]; then
        echo -e "  ${GREEN}ALL TESTS PASSED — within 300ms target${NC}"
    else
        echo -e "  ${GREEN}ALL TESTS PASSED${NC} — ${RED}latency ${LATENCY_MS}ms exceeds 300ms${NC}"
    fi
    echo ""
    exit 0
else
    echo -e "  ${RED}SOME TESTS FAILED${NC}"
    echo ""
    echo "  --- output.json ---"
    cat "$OUTPUT"
    echo "  --------------------"
    echo ""
    exit 1
fi
