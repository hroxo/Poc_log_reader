# SCO Monitor — POS Transaction Event Bridge

A lightweight C daemon that tails the UniFO self-checkout log in real time, parses transaction events, and writes structured JSON payloads for consumption by downstream computer vision systems.

---

## Overview

The SCO Monitor acts as the integration bridge between the UniFO POS software and external computer vision solutions (e.g. Everseen). It monitors the application log file continuously, detects relevant transaction lifecycle events, and materialises them as a JSON file that the CV system polls.

```
UniFO / SCO  ──►  logSelfcheckout.log  ──►  sco_monitor  ──►  output.json  ──►  CV System
```

The solution requires **no changes to the POS software** and has no runtime dependencies beyond a standard C library. End-to-end latency from log write to JSON output is under 300 ms.

---

## Detected Events

The monitor detects the full transaction lifecycle across 7 event types:

| Event | Trigger | Description |
|---|---|---|
| `StartTransaction` | Customer begins session | Marks the start of a new transaction; includes transaction ID |
| `ItemSold` | Article scanned successfully | Records article details: barcode, description, price, quantity |
| `Discount` | Promotional discount applied | Records discount amount, description, and linked item number |
| `Totals` | Basket finalised | Aggregated basket values: total, item count, balance due, total discount |
| `TenderAccepted` | Payment processed | Records payment method, amount, and tender description |
| `EnterAssistMode` | Attendant intervention starts | Logs moment an operator takes control of the SCO |
| `ExitAssistMode` | Attendant intervention ends | Logs moment control is returned to the customer |
| `EndTransaction` | Session closed | Marks the end of the transaction cycle; includes transaction ID |

---

## Quick Start

### Prerequisites

- Linux (tested on Ubuntu 24)
- GCC
- Make

### Build & Run

```bash
# Clone the repository
git clone https://github.com/hroxo/Poc_log_reader.git
cd Poc_log_reader

# Compile
make

# Run the monitor
./sco_monitor <path_to_log_file> <path_to_output_json>

# Example
./sco_monitor /var/log/sco/logSelfcheckout.log ./output.json
```

### Run Tests

```bash
bash test.sh
```

The test suite compiles, starts the monitor, injects a full transaction cycle, and validates all 7 event types in `output.json`. Target: all tests pass within 300 ms.

```
============================================
 SCO Monitor - Test Suite
============================================
  [PASS] A - StartTransaction
  [PASS] B - ItemSold
  [PASS] C - Discount
  [PASS] D - Totals
  [PASS] E - TenderAccepted
  [PASS] F - AssistMode
  [PASS] G - EndTransaction

  Summary: 7/7 passed
  Latency: 187ms (target: <300ms)
============================================
```

---

## Repository Structure

```
Poc_log_reader/
├── src/                    # C source files
├── .vscode/                # Editor settings
├── Makefile                # Build rules (make / make re / make clean)
├── sco_monitor             # Compiled binary
├── logSelfcheckout.log     # Sample POS log for development/testing
├── output.json             # JSON output consumed by the CV system
└── test.sh                 # Automated test suite
```

---

---

## Technical Reference

### Architecture

The monitor runs as a background process. It uses **tail-follow semantics** (similar to `tail -f`) to read new log lines as they are appended by the UniFO process. When a line matching a known event pattern is detected, the relevant XML payload is parsed and the event is appended to `output.json`.

The polling interval is **50 ms**, which yields an end-to-end latency well under the 300 ms integration target.

```
┌─────────────────────────────────────────────┐
│                 sco_monitor                 │
│                                             │
│  inotify / poll ──► line parser             │
│                         │                  │
│                    XML field extractor      │
│                         │                  │
│                    JSON serialiser ──► output.json
└─────────────────────────────────────────────┘
```

### Log Format

The UniFO log uses the following line structure:

```
[YYYY-MM-DD HH:MM:SS:mmm][LEVEL]: TID(0x...) [ScoAdapter] CONTENT [<message id="..." name="...">...</message>]
```

Events without the `[ScoAdapter] CONTENT` wrapper (e.g. `EnterAssistMode`, `ExitAssistMode`) are matched directly by message name on the log line.

### Output JSON Schema

The monitor writes (or appends) one JSON object per event to `output.json`. Each object always contains `event_type` and `timestamp`. Additional fields depend on event type.

#### `StartTransaction`

```json
{
  "event_type": "StartTransaction",
  "timestamp": "2026-01-26 18:55:57:953",
  "id": "test-txn-001"
}
```

#### `ItemSold`

```json
{
  "event_type": "ItemSold",
  "timestamp": "2026-01-30 16:54:06:069",
  "description": "RTD JACK DANIEL",
  "upc": "5449000168481",
  "department": "1403",
  "item_number": 1,
  "price": 299,
  "extended_price": 299,
  "quantity": 1
}
```

> Prices are in **integer cents** (e.g. `299` = €2.99).

#### `Discount`

```json
{
  "event_type": "Discount",
  "timestamp": "2026-01-26 18:46:04:635",
  "upc": "56015173109791",
  "item_number": 1007,
  "discount_amount": 53,
  "discount_description": "POUPANCA",
  "associated_item_number": 7,
  "reward_location": 3
}
```

#### `Totals`

```json
{
  "event_type": "Totals",
  "timestamp": "2026-01-26 18:46:04:687",
  "total_amount": 3526,
  "item_count": 7,
  "balance_due": 3526,
  "discount_amount": 639
}
```

#### `TenderAccepted`

```json
{
  "event_type": "TenderAccepted",
  "timestamp": "2026-01-26 18:56:55:653",
  "amount": 231,
  "tender_type": "Credit",
  "description": "Cartao Credito"
}
```

#### `EnterAssistMode` / `ExitAssistMode`

```json
{
  "event_type": "EnterAssistMode",
  "timestamp": "2026-01-27 18:02:01:455"
}
```

```json
{
  "event_type": "ExitAssistMode",
  "timestamp": "2026-01-27 18:02:36:171"
}
```

#### `EndTransaction`

```json
{
  "event_type": "EndTransaction",
  "timestamp": "2026-01-26 18:57:00:911",
  "id": "test-txn-001"
}
```

### Build System

| Target | Description |
|---|---|
| `make` | Incremental build |
| `make re` | Clean rebuild (used by test suite) |
| `make clean` | Remove compiled objects and binary |

### Performance

| Metric | Value |
|---|---|
| Poll interval | 50 ms |
| End-to-end latency target | < 300 ms |
| Runtime dependencies | None (libc only) |
| Language | C (C99) |

---

## Context

This component is part of the **Everseen SCO** initiative within the *In Store — Checkouts and Pricing* domain. It was developed as a PoC to validate the feasibility of feeding structured transaction context to a computer vision silent-mode fraud detection system, without requiring changes to the UniFO/UniFO platform.
