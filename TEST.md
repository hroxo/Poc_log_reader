# TEST.md — Self-Checkout Log Reader Test Specification

## Test Runner: `test.sh`

### Execution Flow
1. Remove any previous `output.json` and temp files
2. Create a temporary empty log file (`/tmp/test_sco.log`)
3. Start `./sco_monitor /tmp/test_sco.log` in the background (capture PID)
4. Wait 1 second for the monitor to initialize
5. Append test log blocks to `/tmp/test_sco.log` one block at a time with `sleep 0.1` between blocks
6. Wait 2 seconds for processing
7. Kill the monitor process (`kill $PID`)
8. Validate `output.json` against expected results
9. Report PASS/FAIL per test case
10. Print summary (X/7 passed)
11. Clean up temp files
12. Exit with code 0 if all pass, 1 if any fail

---

## Test Log Blocks

Append these **exact** blocks to the test log file. Each block is separated by a blank line here for readability — in the actual test file, append them sequentially with `sleep 0.1` between blocks.

### Block A — Standard ItemSold
```
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
```

### Block B — Discount ItemSold
```
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
```

### Block C — Totals
```
[2026-01-26 18:46:04:687][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="Totals" msgid="b2" name="Totals">
    <fields>
      <field ftype="int" name="TotalAmount">3526</field>
      <field ftype="int" name="ItemCount">7</field>
      <field ftype="int" name="BalanceDue">3526</field>
      <field ftype="int" name="DiscountAmount">639</field>
    </fields>
  </message>]
```

### Block D — StartTransaction
```
[2026-01-26 18:55:57:953][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="StartTransaction" msgid="b2" name="StartTransaction">
```

### Block E — TenderAccepted
```
[2026-01-26 18:56:55:653][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="TenderAccepted" msgid="b2" name="TenderAccepted">
    <fields>
      <field ftype="int" name="Amount">231</field>
      <field ftype="string" name="TenderType">Credit</field>
      <field ftype="string" name="Description">Cartao Credito</field>
    </fields>
```
> **Note:** This block intentionally has NO closing `</message>]`. The program must handle this gracefully — it should emit the event when the next event block starts or when no more data arrives.

### Block F — EndTransaction
```
[2026-01-26 18:57:00:911][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="EndTransaction" msgid="b2" name="EndTransaction">
```

### Block G — EnterAssistMode & ExitAssistMode
```
[2026-01-27 18:02:01:455][INFO]: TID(0x7fbc8b0cf700) <message name="EnterAssistMode"><fields/></message>
[2026-01-27 18:02:36:171][INFO]: TID(0x7fbc8b0cf700) <message name="ExitAssistMode"><fields/></message>
```
> **Note:** These lines do NOT contain `[ScoAdapter] CONTENT`. They use a different log format. Both are single-line events.

---

## Expected JSON Output

After all blocks are appended and processed, `output.json` should contain these JSON objects (one per line, in order):

### Test A — Standard ItemSold
```json
{"timestamp":"2026-01-26 18:46:04:584","event_type":"ItemSold","data":{"description":"PIRI PIRI EX.FOR.SAC.PALADIN 75","upc":"5601517310979","price":209,"quantity":1}}
```
**Validation checks:**
- Contains `"event_type":"ItemSold"`
- Contains `"description":"PIRI PIRI EX.FOR.SAC.PALADIN 75"` (trailing whitespace TRIMMED)
- Contains `"price":209`
- Contains `"quantity":1`
- Contains `"upc":"5601517310979"`

### Test B — Discount ItemSold
```json
{"timestamp":"2026-01-26 18:46:04:635","event_type":"Discount","data":{"upc":"56015173109791","discount_amount":53,"discount_description":"POUPANCA"}}
```
**Validation checks:**
- Contains `"event_type":"Discount"` (NOT "ItemSold")
- Contains `"discount_amount":53`
- Contains `"discount_description":"POUPANCA"` (trailing whitespace TRIMMED)
- Contains `"upc":"56015173109791"`

### Test C — Totals
```json
{"timestamp":"2026-01-26 18:46:04:687","event_type":"Totals","data":{"total_amount":3526,"item_count":7,"balance_due":3526}}
```
**Validation checks:**
- Contains `"event_type":"Totals"`
- Contains `"total_amount":3526`
- Contains `"item_count":7`
- Contains `"balance_due":3526`

### Test D — StartTransaction
```json
{"timestamp":"2026-01-26 18:55:57:953","event_type":"StartTransaction","data":{}}
```
**Validation checks:**
- Contains `"event_type":"StartTransaction"`
- Contains `"data":{}`
- Contains `"timestamp":"2026-01-26 18:55:57:953"`

### Test E — TenderAccepted
```json
{"timestamp":"2026-01-26 18:56:55:653","event_type":"TenderAccepted","data":{"amount":231,"tender_type":"Credit","description":"Cartao Credito"}}
```
**Validation checks:**
- Contains `"event_type":"TenderAccepted"`
- Contains `"amount":231`
- Contains `"tender_type":"Credit"`
- Contains `"description":"Cartao Credito"`

### Test F — EndTransaction
```json
{"timestamp":"2026-01-26 18:57:00:911","event_type":"EndTransaction","data":{}}
```
**Validation checks:**
- Contains `"event_type":"EndTransaction"`
- Contains `"data":{}`

### Test G — AssistMode (two events)
```json
{"timestamp":"2026-01-27 18:02:01:455","event_type":"EnterAssistMode","data":{}}
{"timestamp":"2026-01-27 18:02:36:171","event_type":"ExitAssistMode","data":{}}
```
**Validation checks:**
- Contains `"event_type":"EnterAssistMode"`
- Contains `"event_type":"ExitAssistMode"`
- Contains `"timestamp":"2026-01-27 18:02:01:455"` (for Enter)
- Contains `"timestamp":"2026-01-27 18:02:36:171"` (for Exit)

---

## Validation Method

For each test, use `grep` against `output.json`. A test passes if ALL its validation checks match.

```bash
check() {
    TEST_NAME="$1"
    PATTERN="$2"
    if grep -q "$PATTERN" output.json; then
        return 0
    else
        echo "  FAIL: expected to find: $PATTERN"
        return 1
    fi
}
```

A test case function should call `check` for every required pattern. Only if all checks pass does the test case pass.

---

## Edge Case Tests (Phase 6 — optional hardening)

These are additional scenarios to test after the 7 core tests all pass:

### H — Noise Lines (should be ignored)
```
[2026-01-26 18:45:00:000][INFO]: TID(0x7f2c51073700) Some random log line that is not an SCO event
[2026-01-26 18:45:00:001][DEBUG]: TID(0x7f2c51073700) Another irrelevant line
[2026-01-26 18:45:00:002][INFO]: TID(0x7f2c51073700) [ScoAdapter] STATUS [connected]
```
**Validation:** These lines should NOT produce any JSON output. `output.json` line count should not increase after appending these.

### I — Empty Lines (should be ignored)
```


```
**Validation:** Empty lines should not crash the program or produce output.

### J — Rapid Succession (stress)
Append blocks A through G with `sleep 0.01` instead of `sleep 0.1`. All 7+ JSON objects should still appear in `output.json`.

---

## Test Output Format

```
========================================
 SCO Monitor — Test Suite
========================================

[TEST A] Standard ItemSold ........... PASS
[TEST B] Discount ItemSold ........... PASS
[TEST C] Totals ...................... PASS
[TEST D] StartTransaction ........... PASS
[TEST E] TenderAccepted .............. PASS
[TEST F] EndTransaction .............. PASS
[TEST G] AssistMode .................. PASS

========================================
 Results: 7/7 PASSED
========================================
```

If a test fails, show which specific check failed:
```
[TEST B] Discount ItemSold ........... FAIL
  FAIL: expected to find: "discount_description":"POUPANCA"
```

---

## Post-Test Checks (run after test.sh)

### Memory Leak Check
```bash
# Create a mini test: start monitor, append one block, kill, check valgrind
valgrind --leak-check=full --show-leak-kinds=all --error-exitcode=1 \
    timeout 5 ./sco_monitor /tmp/test_sco.log
```

### Compilation Check
```bash
make fclean && make 2>&1 | grep -i "warning\|error"
# Expected: no output (zero warnings, zero errors)
```

### Debug Print Check
```bash
grep -rn 'printf.*[Dd][Ee][Bb][Uu][Gg]\|fprintf.*stderr.*[Dd][Ee][Bb][Uu][Gg]\|printf.*TODO\|printf.*FIXME\|printf.*TEST' src/
# Expected: no output
```
