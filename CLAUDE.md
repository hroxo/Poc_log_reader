Project Context: Self-Checkout Log Reader & JSON Converter

1. Objective

Build a C-based application to continuously monitor a specific log file (logSelfcheckout.log). The system must act as a "tail -f" utility that filters specific events, extracts relevant business data, converts it into a structured JSON format, and outputs it to both stdout and a local file output.json.

2. Architecture & File Structure

The project is structured in the src/ directory. The codebase must be written in C.

src/get_next_line_bonus.c (Existing): Handles reading the file line-by-line.

src/get_next_line_utils_bonus.c (Existing): Helper functions for the line reader.

src/main.c (To Create): The orchestrator. Initializes the file reading, manages the main loop, and handles resource cleanup.

src/log_reader.c (To Create):

Opens the log file.

Crucial: Seeks to the end of the file (SEEK_END) immediately upon opening to ignore historical data.

Monitors for new lines continuously.

Filters lines: detects if a line contains relevant SCO (Self-Checkout) messages.

src/info_extractor.c (To Create):

Parses the raw string buffer.

Identifies the start/end of XML-like message blocks (e.g., <message ...>, </message>).

Extracts specific fields (UPC, Price, Weight, etc.) from the XML structure.

src/info_convert.c (To Create):

Takes the extracted C-structures/data.

Formats them into a valid JSON string.

Writes to stdout and appends to output.json.

3. Log Parsing Logic (The State Machine)

The log entries consist of timestamps followed by an XML payload. The XML payload is often spread across multiple lines (pretty-printed).

Parsing Strategy:
Since get_next_line reads line-by-line, you must implement a simple state machine or buffer system:

Detect Start: Look for [ScoAdapter] CONTENT [<message. Extract the name or id attribute (e.g., ItemSold, StartTransaction).

Accumulate/Parse: While inside a message block, look for <field ... name="KEY">VALUE</field>. Extract Key and Value.

Detect End: Look for </message>] or </message>.

Trigger: Upon detecting the end, generate the JSON.

Key Events to Monitor

A. Transaction State

Start: <message id="StartTransaction" ...>

End: <message id="EndTransaction" ...>

B. Item Sales (ItemSold)

Identifier: <message id="ItemSold" ...>

Relevant Fields:

Description (String)

UPC (String)

ItemNumber (Int)

Price (Int) - Usually in cents.

Quantity (Int)

DiscountAmount (Int) - Note: Sometimes "ItemSold" is actually a discount update. Check if DiscountAmount > 0.

C. Totals

Identifier: <message id="Totals" ...>

Relevant Fields:

TotalAmount (Int)

BalanceDue (Int)

ItemCount (Int)

D. Payments (Tender)

Identifier: <message id="TenderAccepted" ...>

Relevant Fields:

Amount (Int)

TenderType (String) - e.g., "Credit"

Description (String)

E. Assist Mode

Enter: <message name="EnterAssistMode">

Exit: <message name="ExitAssistMode">

Note: These often appear as single-line XML or self-closing tags depending on the log version. Handle both.

4. JSON Output Format

The output must be a single JSON object per event.

Example Format:

{
  "timestamp": "2026-01-26 18:46:04:584",
  "event_type": "ItemSold",
  "data": {
    "description": "PIRI PIRI EX.FOR.SAC.PALADIN 75",
    "upc": "5601517310979",
    "price": 209,
    "quantity": 1
  }
}


5. Technical Requirements & Constraints

Continuous Reading (Tail -f behavior):

Use fseek(file, 0, SEEK_END) at startup.

Inside the while(1) loop, if get_next_line returns NULL (end of file), use usleep() (e.g., 10000 microseconds) to wait, then clear the file error flags (re-read) to catch new appended data.

Memory Management:

Strictly no memory leaks.

Every malloc must have a corresponding free.

Use valgrind --leak-check=full ./your_program to verify.

Parsing Robustness:

The parser should be resilient to empty lines or log lines that do not contain ScoAdapter.

Strings inside the log might have whitespace padding (e.g., POUPANCA          ). Trim whitespace before putting it into JSON.

C Library:

Use standard libraries (stdio.h, stdlib.h, string.h, unistd.h, fcntl.h).

Do not use external JSON libraries (like cJSON) unless explicitly allowed. Construct the JSON strings manually using snprintf or string concatenation to keep dependencies low.

6. Implementation Plan

main.c: Setup signal handlers (Ctrl+C to exit gracefully and free memory) and call start_monitoring().

log_reader.c: Implement start_monitoring. Loop reading lines. If a line indicates the start of a message, pass control to info_extractor.

info_extractor.c: maintain a static struct or state. Fill the struct as lines come in. When the closing tag is found, call convert_to_json.

info_convert.c: Take the struct, print the JSON to stdout, and append to

7. Reference Log Data for Testing

ImportantÇ Never ask for tests automate them all!
Use the following exact raw log entries to validate the parser logic.

A. Item Sold (Standard):

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


B. Item Sold (Discount/Coupon):

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


C. Totals:

[2026-01-26 18:46:04:687][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="Totals" msgid="b2" name="Totals">
    <fields>
      <field ftype="int" name="TotalAmount">3526</field>
      <field ftype="int" name="ItemCount">7</field>
      <field ftype="int" name="BalanceDue">3526</field>
      <field ftype="int" name="DiscountAmount">639</field>
    </fields>
  </message>]


D. Transaction Start/End:

[2026-01-26 18:55:57:953][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="StartTransaction" msgid="b2" name="StartTransaction">
[2026-01-26 18:57:00:911][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="EndTransaction" msgid="b2" name="EndTransaction">


E. Tender (Payment):

[2026-01-26 18:56:55:653][INFO]: TID(0x7f2c51073700) [ScoAdapter] CONTENT [<message id="TenderAccepted" msgid="b2" name="TenderAccepted">
    <fields>
      <field ftype="int" name="Amount">231</field>
      <field ftype="string" name="TenderType">Credit</field>
      <field ftype="string" name="Description">Cartao Credito</field>
    </fields>


F. Assist Mode (One-liners):

[2026-01-27 18:02:01:455][INFO]: TID(0x7fbc8b0cf700) <message name="EnterAssistMode"><fields/></message>
[2026-01-27 18:02:36:171][INFO]: TID(0x7fbc8b0cf700) <message name="ExitAssistMode"><fields/></message>

8. Clean and make sure everything is ready for production this means no DEBUG messages
9. The code must run in continuon till ended by user using ctrl+C, it must read new addition to the EOF (tail -f)