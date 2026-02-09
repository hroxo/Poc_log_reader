import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
import json
import os

from .models import LogEvent, EventType

class LogParser:
    # Regex to match the start of a log line and capture timestamp and content.
    LOG_ENTRY_PATTERN = re.compile(
        r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d{3})\]\[INFO\]:.*?(<message.*?</message>)",
        re.DOTALL
    )

    XML_CONTENT_PATTERN = re.compile(r"<message.*?/message>", re.DOTALL)

    def __init__(self, config_file: str = "logParcer.json"):
        self.config = self._load_config(config_file)

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Loads the event parsing configuration from a JSON file."""
        script_dir = os.path.dirname(__file__)
        # Look for config in parent directory (project root)
        config_path = os.path.join(script_dir, '..', config_file)
        
        if not os.path.exists(config_path):
            # Fallback to current directory (ncr_monitor) if not found in parent
            config_path = os.path.join(script_dir, config_file)
            
        if not os.path.exists(config_path):
            # Fallback to the working directory if not found in either
            config_path = os.path.abspath(config_file)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at any expected path: {config_file}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_log_line(self, line: str) -> Optional[LogEvent]:
        """
        Parses a single log line, extracts timestamp and XML content,
        and converts it into a structured LogEvent.
        """
        match = self.LOG_ENTRY_PATTERN.search(line)
        if not match:
            return None

        timestamp_str = match.group(1)
        raw_xml_content = match.group(2) # This is the full content including the <message> tag

        return self._process_xml_content(timestamp_str, raw_xml_content)

    def _process_xml_content(self, timestamp: str, xml_string: str) -> Optional[LogEvent]:
        """
        Parses the XML string and maps it to a specific LogEvent type using loaded configuration.
        """
        try:
            xml_string = xml_string.strip()
            if not xml_string:
                return None

            root = ET.fromstring(xml_string)
            message_id = root.get('id')
            message_name = root.get('name')

            # Extract all fields from XML initially
            raw_details = {}
            fields_node = root.find('fields')
            if fields_node is not None:
                for field_node in fields_node.findall('field'):
                    key = field_node.get('name')
                    value = field_node.text
                    ftype = field_node.get('ftype') # Get ftype from XML if available
                    if key:
                        raw_details[key] = {'value': value, 'ftype': ftype} # Store ftype with value

            event_config = None
            
            # Try to find a matching event definition
            for definition in self.config.get("event_definitions", []):
                if self._matches_definition(definition, message_id, message_name, raw_details):
                    event_config = definition
                    break
            
            if event_config:
                event_type = EventType[event_config["event_type"]]
                processed_details = self._extract_and_transform_fields(raw_details, event_config["fields_to_extract"], message_id=message_id, message_name=message_name)
            else:
                # Use default event if no specific definition matched
                default_config = self.config.get("default_event", {})
                event_type = EventType[default_config.get("event_type", "GENERIC_MESSAGE")]
                processed_details = self._extract_and_transform_fields(raw_details, default_config.get("fields_to_extract", {}), message_id=message_id, message_name=message_name)

            return LogEvent(
                timestamp=timestamp,
                event_type=event_type,
                details=processed_details
            )

        except ET.ParseError as e:
            # print(f"Warning: XML Parse error: {e} in '{xml_string[:200]}...'")
            return None # Return None for malformed XML
        except Exception as e:
            # print(f"Warning: General error processing XML content: {e} in '{xml_string[:200]}...'")
            return None

    def _matches_definition(self, definition: Dict[str, Any], message_id: Optional[str], message_name: Optional[str], raw_details: Dict[str, Any]) -> bool:
        """Checks if the current XML message matches the given event definition."""
        match_type = definition.get("match_type")
        match_value = definition.get("match_value")
        conditions = definition.get("conditions")

        primary_match = False
        if match_type == "id" and message_id == match_value:
            primary_match = True
        elif match_type == "name" and message_name == match_value:
            primary_match = True
        elif match_type == "any_field_present":
            for field_name in definition.get("match_values", []):
                if field_name in raw_details and raw_details[field_name]['value'] is not None and str(raw_details[field_name]['value']).strip() != '':
                    primary_match = True
                    break
        
        if not primary_match:
            return False

        if conditions:
            return self._check_conditions(conditions, raw_details)
        return True

    def _check_conditions(self, conditions: List[Dict[str, Any]], raw_details: Dict[str, Any]) -> bool:
        """Evaluates a list of conditions against the raw_details."""
        if not conditions:
            return True

        # Initialise with the first condition
        first_condition = conditions[0]
        final_result = self._evaluate_single_condition(first_condition, raw_details)

        # Process subsequent conditions
        for i in range(1, len(conditions)):
            condition = conditions[i]
            current_result = self._evaluate_single_condition(condition, raw_details)
            logical_operator = condition.get("logical_operator", "and").lower()

            if logical_operator == "and":
                final_result = final_result and current_result
            elif logical_operator == "or":
                final_result = final_result or current_result
            # Add other logical operators if necessary
        return final_result

    def _evaluate_single_condition(self, condition: Dict[str, Any], raw_details: Dict[str, Any]) -> bool:
        field_name = condition["field"]
        operator = condition["operator"]
        field_info = raw_details.get(field_name)
        field_value = field_info['value'] if field_info else None

        if operator == "is_null_or_empty":
            return (field_value is None or str(field_value).strip() == '')
        elif operator == "is_not_null_or_empty":
            return (field_value is not None and str(field_value).strip() != '')
        # Extend with other operators (e.g., "equals", "greater_than", etc.) as needed
        return False

    def _extract_and_transform_fields(self, raw_details: Dict[str, Any], fields_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Extracts and transforms fields based on the configuration."""
        processed_details = {}
        for source_key, config in fields_config.items():
            target_key = config.get("target_name", source_key)
            
            source_value_info = raw_details.get(source_key)
            source_value = source_value_info['value'] if source_value_info else None
            xml_ftype = source_value_info['ftype'] if source_value_info else None

            # Handle special source_name for default_event or virtual fields
            if "source_name" in config:
                source_value = kwargs.get(config["source_name"])
            
            if source_value is not None:
                # Apply transformations
                if "transform" in config:
                    if config["transform"] == "divide":
                        try:
                            source_value = float(source_value) / config["value"]
                        except (ValueError, TypeError):
                            pass # Keep original if conversion fails

                # Apply type conversions from config or XML
                ftype = config.get('ftype', xml_ftype) # Config ftype takes precedence
                if ftype == 'int':
                    try:
                        source_value = int(float(source_value)) # Convert to float first to handle "10.0"
                    except (ValueError, TypeError):
                        pass
                elif ftype == 'float':
                    try:
                        source_value = float(source_value)
                    except (ValueError, TypeError):
                        pass
                elif ftype == 'boolean':
                    source_value = True if str(source_value).lower() in ['1', 'true', 'yes'] else False

                processed_details[target_key] = source_value
        return processed_details