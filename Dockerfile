FROM python:3.8-slim

WORKDIR /app

COPY hl7_parser.py /app/
COPY test_hl7_parser.py /app/
COPY requirements.txt /app/

# Install jsonschema for schema validation
RUN pip install --no-cache-dir -r requirements.txt

# Run tests by default
CMD ["python", "-m", "unittest", "test_hl7_parser.py"]

# Alternative usage:
# To parse a file, mount a volume with your HL7 files and run:
# docker run -v /path/to/your/files:/data hl7-parser python hl7_parser.py /data/your_file.hl7