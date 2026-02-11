# TODO.md — Self-Checkout Log Reader

## Phase 1: Foundation
- [ ] `sco_monitor.h` — Define `t_event` struct, all prototypes, includes
- [ ] `main.c` — Entry point, `argv[1]` parsing, SIGINT handler skeleton, call `start_monitoring()`
- [ ] `Makefile` — Verify it compiles with `-Wall -Wextra -Werror` (even with stub functions)
- [ ] Verify GNL files compile and work (check if GNL uses `int fd` or `FILE*`, adapt accordingly)

## Phase 2: Core — Log Reader (State Machine)
- [ ] `log_reader.c` — `start_monitoring()`: open file, `fseek`/`lseek` to end
- [ ] Implement tail-f loop: `get_next_line` → `usleep(10000)` → `clearerr`/retry on NULL
- [ ] Implement IDLE state: detect `[ScoAdapter] CONTENT [<message` trigger lines
- [ ] Implement IDLE state: detect `<message name="EnterAssistMode"` / `ExitAssistMode"` single-line events
- [ ] Implement ACCUMULATING state: buffer lines until `</message>` found
- [ ] Handle edge case: single-line events (`StartTransaction`, `EndTransaction`) without `</message>`
- [ ] Handle edge case: `TenderAccepted` without closing `</message>]` — emit on next event start

## Phase 3: Core — Extraction & Conversion
- [ ] `info_extractor.c` — `extract_info()`: detect event type from `<message id="..." name="...">`
- [ ] Extract timestamp from `[YYYY-MM-DD HH:MM:SS:mmm]` prefix
- [ ] Parse `<field ftype="..." name="KEY">VALUE</field>` patterns
- [ ] Trim leading/trailing whitespace from all extracted string values
- [ ] Distinguish standard ItemSold vs Discount ItemSold (check DiscountAmount > 0)
- [ ] `info_convert.c` — `convert_to_json()`: build JSON with `snprintf`
- [ ] Write JSON to `stdout` (one object per line)
- [ ] Append JSON to `output.json`
- [ ] Free all strings in `t_event` after writing

## Phase 4: Signal Handling & Cleanup
- [ ] SIGINT handler: free all allocated memory, close all file descriptors/handles
- [ ] Verify graceful shutdown leaves no leaks (test with valgrind + Ctrl+C)

## Phase 5: Testing & Hardening
- [x] Create `test.sh` with all 7 test cases (A–G) from spec
- [x] Test A passes — Standard ItemSold
- [x] Test B passes — Discount ItemSold
- [x] Test C passes — Totals
- [x] Test D passes — StartTransaction
- [x] Test E passes — TenderAccepted
- [x] Test F passes — EndTransaction
- [x] Test G passes — EnterAssistMode / ExitAssistMode
- [x] Valgrind clean: zero leaks, zero errors
- [x] No compiler warnings with `-Wall -Wextra -Werror`
- [x] No debug prints in any source file

## Phase 6: Production Polish
- [ ] Code review: clean, readable, well-commented where non-obvious
- [ ] Stress test: large log file with rapid appends
- [ ] Final `make fclean && make && bash test.sh && valgrind` pass
- [ ] Remove any temp/test artifacts from source tree
