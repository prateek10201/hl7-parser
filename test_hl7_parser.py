#!/usr/bin/env python3
"""
Unit tests for the HL7 parser.
"""

import unittest
import os
import tempfile
import json
from hl7_parser import HL7Parser, ValidationError, HL7ParserError, SchemaValidationError

class TestHL7Parser(unittest.TestCase):
    """Test cases for the HL7Parser class."""
    
    def setUp(self):
        """Set up the parser and test data."""
        self.parser = HL7Parser()
        self.schema_parser = None
        
        # Create a simple schema for testing
        schema_data = {
            "type": "object",
            "required": ["appointment_id", "patient"],
            "properties": {
                "appointment_id": {"type": "string"},
                "patient": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "string"}
                    }
                }
            }
        }
        
        # Create temporary schema file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(schema_data, f)
            self.schema_file = f.name
            
        try:
            self.schema_parser = HL7Parser(self.schema_file)
        except ImportError:
            print("Warning: jsonschema not installed, skipping schema validation tests")
            
        # Sample data for testing
        self.valid_hl7 = (
            "MSH|^~\\&|EMR|HOSPITAL|RCM|RCMSYSTEM|202505021200||SIU^S12|12345|P|2.3\r"
            "SCH|123456^A|...|202505021300|...|...|General Consultation|General Consultation|...|...|...|202505021300|...|...|Clinic A - Room 203\r"
            "PID|1||P12345^^^HOSP^MR||Doe^John||19850210|M\r"
            "PV1|1|...|D67890^Smith^Dr"
        )
        
        self.invalid_hl7 = (
            "MSH|^~\\&|EMR|HOSPITAL|RCM|RCMSYSTEM|202505021200||SIU^S12|12345|P|2.3\r"
            "SCH||...|202505021300|...|...|General Consultation|...|...|...|...|Clinic A - Room 203\r"
            "PID|1|||||19850210|M\r"
            "PV1|1|...|"
        )
        
        self.minimal_hl7 = (
            "MSH|^~\\&|EMR|HOSPITAL|RCM|RCMSYSTEM|202505021200||SIU^S12|12345|P|2.3\r"
            "SCH|123456|...|202505021300\r"
            "PID|1||P12345||Doe^John\r"
            "PV1|1|...|D67890"
        )
        
        self.custom_separator_hl7 = (
            "MSH$^~\\&$EMR$HOSPITAL$RCM$RCMSYSTEM$202505021200$$SIU^S12$12345$P$2.3\r"
            "SCH$123456^A$...$202505021300$...$...$General Consultation$...$...$...$...$Clinic A - Room 203\r"
            "PID$1$$P12345^^^HOSP^MR$$Doe^John$$19850210$M\r"
            "PV1$1$...$D67890^Smith^Dr"
        )
        
        self.complex_hl7 = (
            "MSH|^~\\&|SENDING_APPLICATION|SENDING_FACILITY|RECEIVING_APPLICATION|RECEIVING_FACILITY|20110613061611||SIU^S12|24916560|P|2.3|||||\r"
            "SCH|10345^10345|2196178^2196178|||10345|OFFICE^Office visit|reason for the appointment|OFFICE|60|m|^^60^20110617084500^20110617093000|||||9^DENT^ARTHUR^||||9^DENT^ARTHUR^|||||Scheduled\r"
            "PID|1||42||BEEBLEBROX^ZAPHOD||19781012|M|||1 Heart of Gold ave^^Fort Wayne^IN^46804||(260)555-1234|||S||999999999|||||||||||||||||||||\r"
            "PV1|1|O|||||1^Adams^Douglas^A^MD^^^^|2^Colfer^Eoin^D^MD^^^^||||||||||||||||||||||||||||||||||||||||||99158||"
        )
        
        self.multiple_hl7 = (
            "MSH|^~\\&|EMR|HOSPITAL|RCM|RCMSYSTEM|202505021200||SIU^S12|12345|P|2.3\r"
            "SCH|123456^A|...|202505021300|...|...|General Consultation|General Consultation|...|...|...|202505021300|...|...|Clinic A - Room 203\r"
            "PID|1||P12345^^^HOSP^MR||Doe^John||19850210|M\r"
            "PV1|1|...|D67890^Smith^Dr\r"
            "MSH|^~\\&|EMR|HOSPITAL|RCM|RCMSYSTEM|202505031000||SIU^S12|12346|P|2.3\r"
            "SCH|789012^B|...|202505031430|...|...|Follow-up Visit|Follow-up Visit|...|...|...|202505031430|...|...|Clinic B - Room 105\r"
            "PID|1||P67890^^^HOSP^MR||Smith^Jane||19900315|F\r"
            "PV1|1|...|D12345^Johnson^Dr"
        )
    
    def tearDown(self):
        """Clean up temporary files."""
        try:
            os.unlink(self.schema_file)
        except:
            pass
    
    def test_parse_valid_message(self):
        """Test parsing a valid HL7 message."""
        result = self.parser.parse_message(self.valid_hl7)
        
        # Check various fields
        self.assertEqual(result["appointment_id"], "123456")
        self.assertEqual(result["appointment_datetime"], "2025-05-02T13:00:00Z")
        self.assertEqual(result["location"], "Clinic A - Room 203")
        self.assertEqual(result["reason"], "General Consultation")
        
        self.assertEqual(result["patient"]["id"], "P12345")
        self.assertEqual(result["patient"]["first_name"], "John")
        self.assertEqual(result["patient"]["last_name"], "Doe")
        self.assertEqual(result["patient"]["dob"], "1985-02-10")
        self.assertEqual(result["patient"]["gender"], "M")
        
        self.assertEqual(result["provider"]["id"], "D67890")
        self.assertEqual(result["provider"]["name"], "Smith Dr")
    
    def test_parse_invalid_message(self):
        """Test parsing an invalid HL7 message."""
        with self.assertRaises(ValidationError):
            self.parser.parse_message(self.invalid_hl7)
    
    def test_parse_minimal_message(self):
        """Test parsing a message with minimal required fields."""
        result = self.parser.parse_message(self.minimal_hl7)
        
        self.assertEqual(result["appointment_id"], "123456")
        self.assertEqual(result["patient"]["id"], "P12345")
        self.assertEqual(result["patient"]["last_name"], "Doe")
        self.assertEqual(result["patient"]["first_name"], "John")
        self.assertEqual(result["provider"]["id"], "D67890")
    
    def test_custom_field_separator(self):
        """Test parsing a message with custom field separators."""
        result = self.parser.parse_message(self.custom_separator_hl7)
        
        self.assertEqual(result["appointment_id"], "123456")
        self.assertEqual(result["patient"]["id"], "P12345")
        self.assertEqual(result["patient"]["first_name"], "John")
        self.assertEqual(result["patient"]["last_name"], "Doe")
    
    def test_complex_message(self):
        """Test parsing a more complex HL7 message format."""
        result = self.parser.parse_message(self.complex_hl7)
        
        self.assertEqual(result["appointment_id"], "10345")
        self.assertEqual(result["appointment_datetime"], "2011-06-17T08:45:00Z")
        self.assertEqual(result["location"], "OFFICE")
        self.assertEqual(result["reason"], "reason for the appointment")
        
        self.assertEqual(result["patient"]["id"], "42")
        self.assertEqual(result["patient"]["first_name"], "ZAPHOD")
        self.assertEqual(result["patient"]["last_name"], "BEEBLEBROX")
        
        self.assertEqual(result["provider"]["id"], "1")
        self.assertTrue("Adams" in result["provider"]["name"])
    
    def test_file_not_found(self):
        """Test handling of nonexistent files."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file("nonexistent_file.hl7")
    
    def test_parse_file(self):
        """Test parsing a file from the filesystem."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(self.valid_hl7)
            temp_file_path = temp_file.name
        
        try:
            result = self.parser.parse_file(temp_file_path)
            self.assertEqual(result["appointment_id"], "123456")
            self.assertEqual(result["patient"]["id"], "P12345")
        finally:
            os.unlink(temp_file_path)
    
    def test_malformed_message(self):
        """Test handling of malformed messages."""
        malformed_hl7 = "This is not an HL7 message"
        with self.assertRaises(HL7ParserError):
            self.parser.parse_message(malformed_hl7)
    
    def test_empty_message(self):
        """Test handling of empty messages."""
        with self.assertRaises(HL7ParserError):
            self.parser.parse_message("")
    
    def test_missing_segments(self):
        """Test handling of messages with missing segments."""
        no_pid_hl7 = (
            "MSH|^~\\&|EMR|HOSPITAL|RCM|RCMSYSTEM|202505021200||SIU^S12|12345|P|2.3\r"
            "SCH|123456^A|...|202505021300|...|...|General Consultation|...|...|...|...|Clinic A - Room 203\r"
            "PV1|1|...|D67890^Smith^Dr"
        )
        
        with self.assertRaises(ValidationError):
            self.parser.parse_message(no_pid_hl7)
    
    def test_parse_multiple_messages(self):
        """Test parsing multiple messages."""
        results = self.parser.parse_multiple_messages(self.multiple_hl7)
        
        self.assertEqual(len(results), 2)
        
        self.assertEqual(results[0]["appointment_id"], "123456")
        self.assertEqual(results[0]["patient"]["id"], "P12345")
        
        self.assertEqual(results[1]["appointment_id"], "789012")
        self.assertEqual(results[1]["patient"]["id"], "P67890")
        self.assertEqual(results[1]["patient"]["first_name"], "Jane")
    
    def test_parse_file_multiple(self):
        """Test parsing multiple messages from a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(self.multiple_hl7)
            temp_file_path = temp_file.name
        
        try:
            results = self.parser.parse_file(temp_file_path, multiple=True)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["appointment_id"], "123456")
            self.assertEqual(results[1]["appointment_id"], "789012")
        finally:
            os.unlink(temp_file_path)
    
    def test_schema_validation(self):
        """Test validation against a JSON schema."""
        if not self.schema_parser:
            self.skipTest("jsonschema not available")
            
        # Valid message should pass
        result = self.schema_parser.parse_message(self.valid_hl7)
        self.assertEqual(result["appointment_id"], "123456")
        
        # Create a schema that will fail validation
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            invalid_schema = {
                "type": "object",
                "required": ["appointment_id"],
                "properties": {
                    "appointment_id": {"type": "number"}  # This will fail since ID is a string
                }
            }
            json.dump(invalid_schema, f)
            invalid_schema_file = f.name
        
        try:
            # Test with the invalid schema
            invalid_schema_parser = HL7Parser(invalid_schema_file)
            
            # Only run this test if jsonschema is available
            if hasattr(invalid_schema_parser, 'schema') and invalid_schema_parser.schema:
                with self.assertRaises(SchemaValidationError):
                    invalid_schema_parser.parse_message(self.minimal_hl7)
        finally:
            try:
                os.unlink(invalid_schema_file)
            except:
                pass


if __name__ == "__main__":
    unittest.main()
