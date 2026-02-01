from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any
import json


class EventType(Enum):
    TRANSACTION_START = "TransactionStart"
    ITEM_PICKED = "ItemPicked"
    INTERVENTION_START = "InterventionStart"
    INTERVENTION_FINISH = "InterventionFinish"
    PAYMENT_START = "PaymentStart"
    PAYMENT_FINISH = "PaymentFinish"


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
