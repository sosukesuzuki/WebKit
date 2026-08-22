import sys, struct
TRAILER=b"\n---- Bun! ----\n"
REC=52
def parse(path):
    data=open(path,'rb').read()
    idx=data.rfind(TRAILER)
    byte_count, m_off, m_len, entry, argv_off, argv_len, flags = struct.unpack_from('<QIIIIII', data, idx-32)
    for base in [idx-32-byte_count, idx-byte_count, idx+len(TRAILER)-byte_count]:
        mods=data[base+m_off: base+m_off+m_len]
        if len(mods)%REC: continue
        files=[]; ok=True
        for i in range(len(mods)//REC):
            f=struct.unpack_from('<12I4B', mods, i*REC)
            name=data[base+f[0]:base+f[0]+f[1]]
            if not name or b'\x00' in name: ok=False; break
            files.append((name.decode('latin1'), f))
        if ok: return data, base, files, flags
    raise SystemExit("could not locate graph")
if __name__=='__main__':
    data, base, files, flags = parse(sys.argv[1])
    print("base", base, "files", len(files), "flags", hex(flags))
    for name, f in files:
        print(f"{name}: contents={f[3]} sourcemap={f[5]} bytecode_off={f[6]} bytecode_len={f[7]} module_info={f[9]} origin={data[base+f[10]:base+f[10]+f[11]].decode('latin1')} enc/loader/fmt/side={f[12:]}")
