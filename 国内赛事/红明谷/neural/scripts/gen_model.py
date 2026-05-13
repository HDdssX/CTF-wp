#!/usr/bin/env python3
"""Generate default NCML model file for NeuralChat."""

import struct
import os

MODEL_PATH = "/opt/neuralchat/data/models/active.ncm"

def write_ncml(path):
    metadata_entries = [
        (0x01, b"neuralchat-7b"),          # model_name
        (0x02, b"2.1.0"),                   # version
        (0x03, b"NeuralChat Team"),         # author
        (0x04, b"Conversational AI model"), # description
        (0x05, b"/opt/neuralchat/plugins/validate.sh /opt/neuralchat/data/models/active.ncm"), # pre_load_hook
    ]

    # Build metadata section
    meta_data = struct.pack('<H', len(metadata_entries))
    for key_type, value in metadata_entries:
        meta_data += struct.pack('<B', key_type)
        meta_data += struct.pack('<H', len(value))
        meta_data += value

    # Fake model weights (just random-looking data)
    weights = b'\x00' * 256

    # Build data section
    data_section = struct.pack('<I', len(weights)) + weights

    # Header: magic(4) + version(4) + header_size(4) + meta_offset(4) + data_offset(4) = 20 bytes
    header_size = 20
    meta_offset = header_size
    data_offset = meta_offset + len(meta_data)

    header = b'NCML'
    header += struct.pack('<I', 1)            # version
    header += struct.pack('<I', header_size)
    header += struct.pack('<I', meta_offset)
    header += struct.pack('<I', data_offset)

    with open(path, 'wb') as f:
        f.write(header)
        f.write(meta_data)
        f.write(data_section)

    print(f"[*] Default model written to {path}")

if __name__ == '__main__':
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    write_ncml(MODEL_PATH)
