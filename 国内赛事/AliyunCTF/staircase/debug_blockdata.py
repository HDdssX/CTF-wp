#!/usr/bin/env python3
"""
调试 blockdata chain 构建
"""
import struct

def build_blockdata_chain_debug(raw_payload):
    """Debug version"""
    print(f"Raw payload ({len(raw_payload)} bytes): {raw_payload.hex()}")
    
    chunks = []
    
    # 第一块: stream header + 77 0E + padding
    first_chunk = b'\xac\xed\x00\x05\x77\x0e\x00\x00'
    chunks.append(first_chunk)
    print(f"Chunk 0: {first_chunk.hex()} (stream header + TC_BLOCKDATA 14 + padding)")
    
    # remaining = payload without stream header
    remaining = raw_payload[4:]
    print(f"Remaining ({len(remaining)} bytes): {remaining.hex()}")
    
    i = 0
    chunk_idx = 1
    while i < len(remaining):
        chunk_data = remaining[i:i+6]
        print(f"  Slice [{i}:{i+6}]: {chunk_data.hex()} ({len(chunk_data)} bytes)")
        
        if len(chunk_data) < 6:
            chunk_data = chunk_data + b'\x00' * (6 - len(chunk_data))
            print(f"  Padded to: {chunk_data.hex()}")
        
        if i + 6 < len(remaining):
            # More data follows
            chunk = chunk_data + b'\x77\x0e'
            print(f"Chunk {chunk_idx}: {chunk.hex()} (data + TC_BLOCKDATA 14)")
        else:
            # Last chunk - no more blockdata needed
            chunk = chunk_data + b'\x00\x00'
            print(f"Chunk {chunk_idx}: {chunk.hex()} (data + padding, LAST)")
        
        chunks.append(chunk)
        i += 6
        chunk_idx += 1
    
    return chunks


def create_simple_string_payload():
    """TC_STRING "test" """
    payload = b'\xac\xed\x00\x05'
    payload += b'\x74'  # TC_STRING
    payload += struct.pack('>H', 4)
    payload += b'test'
    return payload


def main():
    raw = create_simple_string_payload()
    chunks = build_blockdata_chain_debug(raw)
    
    print("\n--- Verification ---")
    # 模拟反序列化读取流
    print("\nSimulating deserialization:")
    
    # 构建写入后的文件内容（从 DATA 部分开始，不包括 <start>/<end>）
    file_content = bytearray()
    
    for i, chunk in enumerate(chunks):
        if i == 0:
            # chunk 0 的 DATA 直接开始流
            file_content.extend(chunk)
            file_content.extend(b'<end><start>')  # 模拟 tags
        else:
            file_content.extend(chunk)
            file_content.extend(b'<end><start>')
    
    # 去掉最后的 <start>
    file_content = bytes(file_content)[:-len(b'<start>')]
    
    print(f"Simulated file content: {file_content.hex()}")
    
    # 解析
    pos = 0
    print(f"\nParsing stream:")
    
    # Stream header
    magic = file_content[pos:pos+2]
    version = file_content[pos+2:pos+4]
    print(f"  Stream magic: {magic.hex()} (expect aced)")
    print(f"  Stream version: {version.hex()} (expect 0005)")
    pos += 4
    
    # TC_BLOCKDATA
    while pos < len(file_content):
        if file_content[pos] == 0x77:  # TC_BLOCKDATA
            length = file_content[pos+1]
            print(f"  TC_BLOCKDATA at {pos}: skip {length} bytes")
            pos += 2 + length  # skip opcode + length byte + data
        elif file_content[pos] == 0x74:  # TC_STRING
            str_len = struct.unpack('>H', file_content[pos+1:pos+3])[0]
            str_data = file_content[pos+3:pos+3+str_len]
            print(f"  TC_STRING at {pos}: len={str_len}, data='{str_data.decode()}'")
            pos += 3 + str_len
        elif file_content[pos] == 0x00:
            print(f"  Null byte at {pos}, stopping")
            break
        else:
            print(f"  Unknown byte at {pos}: 0x{file_content[pos]:02x}")
            break
    
if __name__ == "__main__":
    main()
