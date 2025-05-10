# HL7 SIU Parser for Appointments

A Python-based parser that reads HL7 SIU (Schedule Information Unsolicited) message files and converts them into structured JSON objects representing appointments.

## Overview

This project provides a solution for parsing HL7 SIU^S12 messages, which are commonly used for appointment scheduling in healthcare systems. The parser extracts relevant appointment information from the HL7 message and converts it to a standardized JSON format, making it easier to integrate with modern applications and systems.

## Features

- Parses HL7 SIU^S12 messages from files
- Extracts data from SCH, PID, and PV1 segments
- Converts dates to ISO format
- Outputs standardized JSON
- Validates required fields
- Handles edge cases (missing fields, custom separators, etc.)
- Provides comprehensive unit tests
- Supports multiple message parsing in a single file
- Optional validation against JSON schema
- Docker support for containerized deployment

## Project Structure

The project includes the following files:

| File                      | Purpose                                                |
| ------------------------- | ------------------------------------------------------ |
| `hl7_parser.py`           | Main parser implementation with the core parsing logic |
| `test_hl7_parser.py`      | Unit tests to validate parser functionality            |
| `sample.hl7`              | Sample HL7 message file for testing                    |
| `input.hl7`               | Sample HL7 message file for testing                    |
| `multiple_samples.hl7`    | Sample file with multiple HL7 messages                 |
| `appointment_schema.json` | JSON Schema for validating parser output               |
| `requirements.txt`        | List of Python dependencies                            |
| `Dockerfile`              | Docker container definition                            |
| `docker-compose.yml`      | Docker Compose configuration                           |

## Installation

### Prerequisites

- Python 3.8 or higher
- (Optional) Docker for containerized usage

### Standard Installation

No installation is required to use the parser directly. Simply clone or download the repository:

```bash
git clone https://github.com/yourusername/hl7-parser.git
cd hl7-parser
```

### Installing Dependencies

The parser has minimal dependencies. To install them:

```bash
pip install -r requirements.txt
```

This will install `jsonschema` which is used for optional output validation.

## Usage

### Parsing a Single HL7 Message

```bash
python hl7_parser.py sample.hl7
python hl7_parser.py input.hl7
```

The above commands would parse the input.hl7 and sample.hl7 files and print the JSON output to the console.

### Saving Output to a File

```bash
python hl7_parser.py sample.hl7 --output result.json
```

### Parsing Multiple Messages

```bash
python hl7_parser.py multiple_samples.hl7 --multiple
```

### Validating Against a Schema

```bash
python hl7_parser.py sample.hl7 --schema appointment_schema.json
```

### Enabling Debug Output

```bash
python hl7_parser.py sample.hl7 --debug
```

## Docker Usage

### Building the Docker Image

```bash
docker build -t hl7-parser .
```

### Running Tests in Docker

```bash
docker run hl7-parser
```

### Parsing a File with Docker

```bash
docker run -v "$(pwd)":/data hl7-parser python hl7_parser.py /data/sample.hl7
```

### Using Docker Compose

```bash
docker-compose up             # Run tests
docker-compose run --rm hl7-parser-cli       # Parse sample file
docker-compose run --rm hl7-parser-multi     # Parse multiple messages
```

## File Descriptions

### hl7_parser.py

This is the main parser implementation that contains all the logic for parsing HL7 SIU messages. It includes:

- A class-based approach with `HL7Parser` as the main class
- Methods for parsing files and message strings
- Field extraction from SCH, PID, and PV1 segments
- Validation logic for required fields
- Support for multiple message parsing
- Flexible field position detection to handle different HL7 formats
- Date/time formatting to convert HL7 dates to ISO format

### test_hl7_parser.py

Comprehensive unit tests for the parser that verify:

- Parsing of valid messages
- Handling of invalid messages
- Custom field separators
- Processing of minimal messages
- Schema validation
- Multiple message parsing

These tests ensure the parser works correctly in various scenarios and can handle edge cases properly.

### sample.hl7 and multiple_samples.hl7

Sample HL7 message files for testing the parser:

- `sample.hl7` contains a single SIU^S12 message
- `multiple_samples.hl7` contains multiple SIU^S12 messages

These files are used for testing and demonstration of the parser's capabilities.

### appointment_schema.json

A JSON schema definition that specifies the structure and validation rules for the appointment data output by the parser. This allows for validation of the output to ensure it matches the expected format.

## Output Format

The parser produces JSON output in the following format:

```json
{
  "appointment_id": "123456",
  "appointment_datetime": "2025-05-02T13:00:00Z",
  "patient": {
    "id": "P12345",
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1985-02-10",
    "gender": "M"
  },
  "provider": {
    "id": "D67890",
    "name": "Dr. Smith"
  },
  "location": "Clinic A - Room 203",
  "reason": "General Consultation"
}
```

## Field Mapping

The following table shows how fields are mapped from HL7 segments to JSON:

| JSON Field           | HL7 Field            | Segment |
| -------------------- | -------------------- | ------- |
| appointment_id       | SCH-1                | SCH     |
| appointment_datetime | SCH-11 or SCH-3      | SCH     |
| location             | SCH-14 or SCH-8      | SCH     |
| reason               | SCH-7 or SCH-6       | SCH     |
| patient.id           | PID-3                | PID     |
| patient.first_name   | PID-5-2              | PID     |
| patient.last_name    | PID-5-1              | PID     |
| patient.dob          | PID-7                | PID     |
| patient.gender       | PID-8                | PID     |
| provider.id          | PV1-7-1 or PV1-3-1   | PV1     |
| provider.name        | PV1-7-2+ or PV1-3-2+ | PV1     |

The parser is flexible and can handle different field positions across various HL7 implementations.

## Running Tests

To run the unit tests:

```bash
python -m unittest test_hl7_parser.py
```

This will run all the test cases and report any failures.

## Error Handling

The parser provides several types of errors to make debugging easier:

- `HL7ParserError`: Base exception for all parser errors
- `ValidationError`: Raised when required fields are missing
- `SchemaValidationError`: Raised when output fails schema validation

Each error includes a detailed message explaining what went wrong.

## Implementation Details

The parser uses a flexible approach to handle variations in HL7 message formats:

1. **Segment Identification**: Identifies MSH, SCH, PID, and PV1 segments in the message
2. **Field Extraction**: Extracts fields based on their positions in each segment
3. **Component Processing**: Handles nested components within fields
4. **Date Formatting**: Converts HL7 date formats to ISO format
5. **Validation**: Ensures all required fields are present

The parser is designed to be robust against variations in HL7 implementations, checking multiple possible field positions for important data.

## Requirements Addressed

This implementation addresses all requirements specified in the assignment:

- Parses an .hl7 file from the filesystem
- Extracts relevant fields from SCH, PID, and PV1 segments
- Outputs a valid JSON structure
- Includes validation for required fields
- Handles common edge cases
- Includes unit tests for parsing logic
- Includes detailed documentation

Additionally, it implements all bonus features:

- Dockerfile for containerization
- Command-line interface
- Support for parsing multiple messages
- Output validation using a JSON schema

## License

This project is licensed under the MIT License.

## Contact

For any questions or issues, please open an issue in the GitHub repository.
