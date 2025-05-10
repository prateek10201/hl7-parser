#!/usr/bin/env python3
"""
HL7 SIU Parser for Appointments

This module parses HL7 SIU^S12 messages and converts them into structured JSON
representing appointment information.
"""

import json
import re
import datetime
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union

# Optional jsonschema for validation
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class HL7ParserError(Exception):
    """Base exception for HL7 parsing errors."""
    pass


class ValidationError(HL7ParserError):
    """Exception raised when validation fails."""
    pass


class SchemaValidationError(ValidationError):
    """Exception raised when JSON schema validation fails."""
    pass


class HL7Parser:
    """Parser for HL7 SIU^S12 messages."""
    
    def __init__(self, schema_path: Optional[str] = None, debug: bool = False):
        # Define default separators
        self.segment_separator = '\r'
        self.default_field_separator = '|'
        self.default_component_separator = '^'
        self.default_subcomponent_separator = '&'
        self.default_repetition_separator = '~'
        self.default_escape_character = '\\'
        self.debug = debug
        
        # Load schema if provided
        self.schema = None
        if schema_path and os.path.exists(schema_path):
            try:
                with open(schema_path, 'r') as f:
                    self.schema = json.load(f)
            except json.JSONDecodeError:
                raise HL7ParserError(f"Invalid JSON schema file: {schema_path}")
    
    def debug_print(self, msg):
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print(msg)
    
    def parse_file(self, file_path: str, multiple: bool = False) -> Union[dict, List[dict]]:
        """Parse an HL7 file and return JSON representation(s) of appointments."""
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                
                if multiple:
                    return self.parse_multiple_messages(content)
                else:
                    return self.parse_message(content)
        except FileNotFoundError:
            raise FileNotFoundError(f"HL7 file not found: {file_path}")
    
    def parse_multiple_messages(self, content: str) -> List[dict]:
        """Parse multiple HL7 messages from a single string."""
        # Normalize line endings
        content = content.replace('\r\n', '\r').replace('\n', '\r')
        
        # Find MSH segments to identify message boundaries
        msh_indices = [m.start() for m in re.finditer(r"MSH[|\$]", content)]
        
        if not msh_indices:
            raise HL7ParserError("No valid HL7 messages found")
        
        # Parse each message
        messages = []
        for i in range(len(msh_indices)):
            start = msh_indices[i]
            end = msh_indices[i + 1] if i + 1 < len(msh_indices) else len(content)
            message = content[start:end]
            
            try:
                parsed = self.parse_message(message)
                messages.append(parsed)
            except (HL7ParserError, ValidationError) as e:
                # We'll log the error but continue with other messages
                self.debug_print(f"Warning: Skipping message {i+1} due to error: {str(e)}")
        
        if not messages:
            raise HL7ParserError("Could not parse any valid messages from the file")
        
        return messages
    
    def parse_message(self, message: str) -> dict:
        """Parse an HL7 message string and return a JSON representation."""
        # Normalize line endings
        message = message.replace('\r\n', '\r').replace('\n', '\r')
        
        # Split message into segments
        segments = message.split(self.segment_separator)
        segments = [seg for seg in segments if seg.strip()]
        
        if not segments:
            raise HL7ParserError("Empty or invalid HL7 message")
        
        # Get separators from MSH segment
        msh_segment = segments[0]
        if not msh_segment.startswith("MSH"):
            raise HL7ParserError("Missing MSH segment or not a valid HL7 message")
        
        field_separator = msh_segment[3:4]
        encoding_chars = msh_segment[4:8] if len(msh_segment) > 4 else "^~\\&"
        component_separator = encoding_chars[0] if encoding_chars else self.default_component_separator
        repetition_separator = encoding_chars[1] if len(encoding_chars) > 1 else self.default_repetition_separator
        escape_character = encoding_chars[2] if len(encoding_chars) > 2 else self.default_escape_character
        subcomponent_separator = encoding_chars[3] if len(encoding_chars) > 3 else self.default_subcomponent_separator
        
        # Check if this is an SIU message
        msh_fields = msh_segment.split(field_separator)
        if len(msh_fields) > 9 and msh_fields[9]:
            message_type = msh_fields[9].split(component_separator)[0] if component_separator in msh_fields[9] else msh_fields[9]
            if message_type != "SIU^S12" and not message_type.startswith("SIU"):
                self.debug_print(f"Warning: Expected SIU message type, got {message_type}")
        
        # Organize segments by their type
        parsed_segments = {}
        for segment in segments:
            if not segment.strip():
                continue
                
            segment_fields = segment.split(field_separator)
            segment_type = segment_fields[0]
            
            if segment_type not in parsed_segments:
                parsed_segments[segment_type] = []
                
            parsed_segments[segment_type].append(segment_fields)
        
        # Extract appointment data
        appointment_data = self._extract_appointment_data(
            parsed_segments, 
            component_separator
        )
        
        self.debug_print(f"Appointment data before validation: {appointment_data}")
        
        # Validation
        self._validate_appointment_data(appointment_data)
        
        # Schema validation if available
        if self.schema and JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=appointment_data, schema=self.schema)
            except jsonschema.exceptions.ValidationError as e:
                raise SchemaValidationError(f"JSON schema validation failed: {str(e)}")
        
        return appointment_data
    
    def _extract_appointment_data(self, segments: Dict[str, List[List[str]]], 
                                component_separator: str) -> dict:
        """Extract appointment data from the parsed segments."""
        appointment_data = {
            "appointment_id": "",
            "appointment_datetime": "",
            "patient": {
                "id": "",
                "first_name": "",
                "last_name": "",
                "dob": "",
                "gender": ""
            },
            "provider": {
                "id": "",
                "name": ""
            },
            "location": "",
            "reason": ""
        }
        
        # Extract from SCH segment (Schedule Activity Information)
        if "SCH" in segments and segments["SCH"]:
            sch_segment = segments["SCH"][0]
            self.debug_print(f"SCH segment: {sch_segment}")
            self.debug_print(f"SCH segment length: {len(sch_segment)}")
            
            # Get appointment ID from SCH-1 (first component)
            if len(sch_segment) > 1 and sch_segment[1]:
                self.debug_print(f"SCH-1 value: {sch_segment[1]}")
                appointment_id_parts = sch_segment[1].split(component_separator)
                self.debug_print(f"Appointment ID parts: {appointment_id_parts}")
                if appointment_id_parts:
                    appointment_data["appointment_id"] = appointment_id_parts[0]
                    self.debug_print(f"Appointment ID set to: {appointment_id_parts[0]}")
            
            # Try multiple possible locations for appointment_datetime
            datetime_field = None
            # First try SCH-11 (standard for appointment timing)
            if len(sch_segment) > 11 and sch_segment[11]:
                datetime_field = sch_segment[11]
                self.debug_print(f"Found datetime in SCH-11: {datetime_field}")
            # If not found or empty, try SCH-3 (as in your first sample)
            elif len(sch_segment) > 3 and sch_segment[3]:
                datetime_field = sch_segment[3]
                self.debug_print(f"Found datetime in SCH-3: {datetime_field}")
            
            if datetime_field:
                # Handle complex datetime formats like "^^60^20110617084500^20110617093000"
                datetime_parts = datetime_field.split(component_separator)
                self.debug_print(f"Datetime parts: {datetime_parts}")
                
                # Look for a part that looks like a datetime (YYYYMMDDHHMMSS)
                appointment_time = None
                for part in datetime_parts:
                    if part and len(part) >= 8 and part.isdigit():
                        appointment_time = part
                        self.debug_print(f"Using datetime part: {appointment_time}")
                        break
                
                if appointment_time:
                    try:
                        # Parse datetime based on length
                        if len(appointment_time) >= 8:  # At least YYYYMMDD
                            year = int(appointment_time[0:4])
                            month = int(appointment_time[4:6])
                            day = int(appointment_time[6:8])
                            hour = 0
                            minute = 0
                            second = 0
                            
                            if len(appointment_time) >= 10:  # YYYYMMDDHH
                                hour = int(appointment_time[8:10])
                            if len(appointment_time) >= 12:  # YYYYMMDDHHMM
                                minute = int(appointment_time[10:12])
                            if len(appointment_time) >= 14:  # YYYYMMDDHHMMSS
                                second = int(appointment_time[12:14])
                                
                            dt = datetime.datetime(
                                year=year,
                                month=month,
                                day=day,
                                hour=hour,
                                minute=minute,
                                second=second
                            )
                            appointment_data["appointment_datetime"] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                            self.debug_print(f"Formatted datetime: {appointment_data['appointment_datetime']}")
                        else:
                            appointment_data["appointment_datetime"] = appointment_time
                    except (ValueError, IndexError) as e:
                        self.debug_print(f"Error formatting datetime: {e}")
                        appointment_data["appointment_datetime"] = appointment_time
            
            # Try multiple possible locations for location
            # First try SCH-14 (as in first sample)
            if len(sch_segment) > 14 and sch_segment[14]:
                appointment_data["location"] = sch_segment[14]
                self.debug_print(f"Location from SCH-14: {appointment_data['location']}")
            # Then try SCH-8 (often used for appointment type/location)
            elif len(sch_segment) > 8 and sch_segment[8]:
                appointment_data["location"] = sch_segment[8]
                self.debug_print(f"Location from SCH-8: {appointment_data['location']}")
            # Also check SCH-6 first component which can be a location
            elif len(sch_segment) > 6 and sch_segment[6]:
                loc_parts = sch_segment[6].split(component_separator)
                if loc_parts and len(loc_parts) > 0:
                    appointment_data["location"] = loc_parts[0]
                    self.debug_print(f"Location from SCH-6 first component: {appointment_data['location']}")
            
            # Try multiple possible locations for reason
            # First try SCH-7 (standard reason field)
            if len(sch_segment) > 7 and sch_segment[7]:
                appointment_data["reason"] = sch_segment[7]
                self.debug_print(f"Reason from SCH-7: {appointment_data['reason']}")
            # Then try SCH-6 second component (often used for appointment type/reason)
            elif len(sch_segment) > 6 and sch_segment[6]:
                reason_value = sch_segment[6]
                if component_separator in reason_value:
                    reason_parts = reason_value.split(component_separator)
                    if len(reason_parts) > 1 and reason_parts[1]:
                        appointment_data["reason"] = reason_parts[1]
                    else:
                        appointment_data["reason"] = reason_parts[0]
                else:
                    appointment_data["reason"] = reason_value
                self.debug_print(f"Reason from SCH-6: {appointment_data['reason']}")
        
        # Extract from PID segment (Patient Identification)
        if "PID" in segments and segments["PID"]:
            pid_segment = segments["PID"][0]
            self.debug_print(f"PID segment: {pid_segment}")
            
            # Try different possible locations for patient ID
            # First try PID-3 (standard)
            if len(pid_segment) > 3 and pid_segment[3]:
                patient_id = pid_segment[3]
                # Check if it has components
                if component_separator in patient_id:
                    patient_id_parts = patient_id.split(component_separator)
                    if patient_id_parts and len(patient_id_parts) > 0:
                        appointment_data["patient"]["id"] = patient_id_parts[0]
                else:
                    appointment_data["patient"]["id"] = patient_id
                self.debug_print(f"Patient ID: {appointment_data['patient']['id']}")
            
            # Get patient name from PID-5
            if len(pid_segment) > 5 and pid_segment[5]:
                patient_name = pid_segment[5]
                if component_separator in patient_name:
                    patient_name_parts = patient_name.split(component_separator)
                    if len(patient_name_parts) > 0:
                        appointment_data["patient"]["last_name"] = patient_name_parts[0]
                    if len(patient_name_parts) > 1:
                        appointment_data["patient"]["first_name"] = patient_name_parts[1]
                else:
                    # If no separator, use the whole field as last name
                    appointment_data["patient"]["last_name"] = patient_name
                self.debug_print(f"Patient name: {appointment_data['patient']['last_name']}, {appointment_data['patient']['first_name']}")
            
            # Get DOB from PID-7
            if len(pid_segment) > 7 and pid_segment[7]:
                dob = pid_segment[7]
                try:
                    # Format YYYYMMDD to YYYY-MM-DD
                    if len(dob) >= 8:
                        formatted_dob = f"{dob[0:4]}-{dob[4:6]}-{dob[6:8]}"
                        appointment_data["patient"]["dob"] = formatted_dob
                    else:
                        appointment_data["patient"]["dob"] = dob
                    self.debug_print(f"Patient DOB: {appointment_data['patient']['dob']}")
                except (ValueError, IndexError):
                    appointment_data["patient"]["dob"] = dob
            
            # Get gender from PID-8
            if len(pid_segment) > 8 and pid_segment[8]:
                appointment_data["patient"]["gender"] = pid_segment[8]
                self.debug_print(f"Patient gender: {appointment_data['patient']['gender']}")
        
        # Extract from PV1 segment (Patient Visit)
        if "PV1" in segments and segments["PV1"]:
            pv1_segment = segments["PV1"][0]
            self.debug_print(f"PV1 segment: {pv1_segment}")
            self.debug_print(f"PV1 segment length: {len(pv1_segment)}")
            
            # Try to find provider info in PV1-7 first (standard), then PV1-3 as fallback
            provider_field = None
            
            # Check PV1-7 (standard location for attending doctor)
            if len(pv1_segment) > 7 and pv1_segment[7]:
                provider_field = pv1_segment[7]
                self.debug_print(f"Using PV1-7 for provider: {provider_field}")
            # If not found, check PV1-3 (as in your first sample)
            elif len(pv1_segment) > 3 and pv1_segment[3]:
                provider_field = pv1_segment[3]
                self.debug_print(f"Using PV1-3 for provider: {provider_field}")
            
            if provider_field:
                provider_parts = provider_field.split(component_separator)
                self.debug_print(f"Provider parts: {provider_parts}")
                
                if len(provider_parts) > 0:
                    appointment_data["provider"]["id"] = provider_parts[0]
                    self.debug_print(f"Provider ID set to: {provider_parts[0]}")
                
                # Build provider name from available parts
                provider_name_parts = []
                if len(provider_parts) > 2:  # Standard format with last name, first name
                    if provider_parts[1]:
                        provider_name_parts.append(provider_parts[1])  # Last name
                    if provider_parts[2]:
                        provider_name_parts.append(provider_parts[2])  # First name
                    if len(provider_parts) > 3 and provider_parts[3]:
                        provider_name_parts.append(provider_parts[3])  # Middle initial
                    if len(provider_parts) > 4 and provider_parts[4]:
                        provider_name_parts.append(provider_parts[4])  # Title
                elif len(provider_parts) > 1:  # Minimal format
                    if provider_parts[1]:
                        provider_name_parts.append(provider_parts[1])
                
                appointment_data["provider"]["name"] = " ".join(provider_name_parts).strip()
                self.debug_print(f"Provider name set to: {appointment_data['provider']['name']}")
        
        self.debug_print(f"Final appointment data: {appointment_data}")
        return appointment_data
    
    def _validate_appointment_data(self, data: dict) -> None:
        """Make sure all required fields are present in the data."""
        required_fields = [
            ("appointment_id", "Appointment ID is missing"),
            #("appointment_datetime", "Appointment datetime is missing"),
            ("patient.id", "Patient ID is missing"),
            ("patient.first_name", "Patient first name is missing"),
            ("patient.last_name", "Patient last name is missing"),
            ("provider.id", "Provider ID is missing")
        ]
        
        for field, error_message in required_fields:
            field_parts = field.split('.')
            current = data
            self.debug_print(f"Checking field: {field}")
            
            try:
                for part in field_parts:
                    current = current[part]
                    self.debug_print(f"  Current value: {current}")
                
                if not current:
                    self.debug_print(f"  Field is empty")
                    raise ValidationError(f"{error_message} (empty value)")
            except (KeyError, TypeError):
                self.debug_print(f"  Field is missing")
                raise ValidationError(error_message)


def parse_hl7_file(file_path: str, schema_path: Optional[str] = None, multiple: bool = False, debug: bool = False) -> Union[dict, List[dict]]:
    """Convenience function to parse an HL7 file."""
    parser = HL7Parser(schema_path, debug)
    return parser.parse_file(file_path, multiple)


def main():
    """Command-line interface for the HL7 parser."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse HL7 SIU messages into JSON")
    parser.add_argument("input_file", help="Path to the HL7 input file")
    parser.add_argument("-o", "--output", help="Output JSON file path (default: stdout)")
    parser.add_argument("-s", "--schema", help="Path to JSON schema file for validation")
    parser.add_argument("-m", "--multiple", action="store_true", help="Parse multiple messages from a single file")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()
    
    try:
        result = parse_hl7_file(args.input_file, args.schema, args.multiple, args.debug)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Output written to {args.output}")
        else:
            print(json.dumps(result, indent=2))
            
    except (FileNotFoundError, HL7ParserError, ValidationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
