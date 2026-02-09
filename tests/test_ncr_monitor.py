import unittest
import json
from ncr_monitor.log_parser import LogParser
from ncr_monitor.models import EventType, LogEvent

class TestLogParser(unittest.TestCase):

    def setUp(self):
        self.parser = LogParser()

    def test_start_transaction(self):
        log_line = """[2026-02-01 16:16:01:879][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message id="StartTransaction" name="Transaction" version="1" primary="1"><fields><field name="Id" ftype="string">4801bb8b-4744-4920-84fe-1cd79cf10c36</field><field name="SuspendAllowed" ftype="boolean">1</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:01:879",
            event_type=EventType.TRANSACTION_START,
            details={
                "TransactionId": "4801bb8b-4744-4920-84fe-1cd79cf10c36",
                "SuspendAllowed": True
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_item_sold_normal(self):
        log_line = """[2026-02-01 16:16:02:879][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message id="ItemSold" name="Item" version="1" primary="1"><fields><field name="Description" ftype="string">LEITE UHT M/G 1L</field><field name="UPC" ftype="string">123456789012</field><field name="Price" ftype="int">89</field><field name="ExtendedPrice" ftype="int">89</field><field name="Quantity" ftype="int">1</field><field name="VoidFlag" ftype="boolean">0</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:02:879",
            event_type=EventType.ITEM_SOLD,
            details={
                "Description": "LEITE UHT M/G 1L",
                "UPC": "123456789012",
                "Price": 89,
                "Quantity": 1,
                "ExtendedPrice": 89,
                "VoidFlag": False
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_item_sold_modifier(self):
        log_line = """[2026-02-01 16:16:03:123][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message id="ItemSold" name="Item" version="1" primary="0"><fields><field name="Description" ftype="string">Discount</field><field name="DiscountAmount" ftype="int">10</field><field name="AssociatedItemNumber" ftype="int">1</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:03:123",
            event_type=EventType.ITEM_MODIFIER,
            details={
                "Description": "Discount",
                "DiscountAmount": 10,
                "AssociatedItemNumber": 1
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_tender_accepted(self):
        log_line = """[2026-02-01 16:16:10:880][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message id="TenderAccepted" name="Payment" version="1" primary="1"><fields><field name="Amount" ftype="int">500</field><field name="TenderType" ftype="string">Cash</field><field name="Description" ftype="string">EUR</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:10:880",
            event_type=EventType.TENDER_ACCEPTED,
            details={
                "Amount": 5.0, # 500 cents
                "TenderType": "Cash",
                "Description": "EUR"
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_end_transaction(self):
        log_line = """[2026-02-01 16:16:10:880][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message id="EndTransaction" name="Transaction" version="1" primary="1"><fields><field name="Id" ftype="string">4801bb8b-4744-4920-84fe-1cd79cf10c36</field><field name="Complete" ftype="boolean">1</field><field name="TotalAmount" ftype="int">89</field><field name="ItemCount" ftype="int">1</field><field name="BalanceDue" ftype="int">0</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:10:880",
            event_type=EventType.TRANSACTION_END,
            details={
                "TransactionId": "4801bb8b-4744-4920-84fe-1cd79cf10c36",
                "Complete": True,
                "TotalAmount": 89,
                "ItemCount": 1,
                "BalanceDue": 0
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_enter_assist_mode(self):
        log_line = """[2026-02-01 16:16:04:879][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message name="EnterAssistMode" version="1" primary="1"><fields><field name="SummaryInstruction.1" ftype="string">      NcrKey_ConfirmAge</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:04:879",
            event_type=EventType.ASSIST_MODE_ENTER,
            details={
                "SummaryInstruction.1": "      NcrKey_ConfirmAge"
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_exit_assist_mode(self):
        log_line = """[2026-02-01 16:16:07:879][INFO]: TID(4801bb8b-4744-4920-84fe-1cd79cf10c36) [ScoAdapter] CONTENT [<message name="ExitAssistMode" version="1" primary="1"><fields><field name="Id" ftype="string">OperatorOverride</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:07:879",
            event_type=EventType.ASSIST_MODE_EXIT,
            details={
                "Id": "OperatorOverride"
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

    def test_malformed_xml(self):
        log_line = """[2026-02-01 16:16:00:000][INFO]: TID(...) [ScoAdapter] CONTENT [<message id="MalformedXML"<field>value</field></message>]"""
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNone(parsed_event)

    def test_no_xml_content(self):
        log_line = """[2026-02-01 16:16:00:000][INFO]: TID(...) [ScoAdapter] Some plain text content here."""
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNone(parsed_event)

    def test_generic_message(self):
        # A message not explicitly handled, should fall back to GENERIC_MESSAGE
        log_line = """[2026-02-01 16:16:00:000][INFO]: TID(...) [ScoAdapter] CONTENT [<message id="UnknownMessage" name="Generic" version="1"><fields><field name="Status" ftype="string">OK</field></fields></message>]"""
        expected_event = LogEvent(
            timestamp="2026-02-01 16:16:00:000",
            event_type=EventType.GENERIC_MESSAGE,
            details={
                "MessageId": "UnknownMessage",
                "MessageName": "Generic",
                "Status": "OK"
            }
        )
        parsed_event = self.parser.parse_log_line(log_line)
        self.assertIsNotNone(parsed_event)
        self.assertEqual(parsed_event.timestamp, expected_event.timestamp)
        self.assertEqual(parsed_event.event_type, expected_event.event_type)
        self.assertEqual(parsed_event.details, expected_event.details)
        self.assertEqual(json.loads(parsed_event.to_json()), json.loads(expected_event.to_json()))

if __name__ == '__main__':
    unittest.main()