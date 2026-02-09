from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any
import json


class EventType(Enum):
    TRANSACTION_START = "StartTransaction"
    TRANSACTION_END = "EndTransaction"
    ITEM_SOLD = "ItemSold"
    ITEM_MODIFIER = "ItemModifier" # For discounts/modifications to items
    TRANSACTION_SUMMARY = "TransactionSummary" # For totals
    TENDER_START = "TenderStart"
    TENDER_ACCEPTED = "TenderAccepted"
    ASSIST_MODE_ENTER = "AssistModeEnter"
    ASSIST_MODE_EXIT = "AssistModeExit"
    GENERIC_MESSAGE = "GenericMessage" # For any unhandled XML messages


@dataclass
class LogEvent:
    timestamp: str
    event_type: EventType
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "details": self.details
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
