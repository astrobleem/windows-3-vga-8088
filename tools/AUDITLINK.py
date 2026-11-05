from pathlib import Path
import json,re,sys
def normalized(p): return p.read_bytes().replace(b"\r\n",b"\n").replace(b"\x1a",b"").decode("latin1")
def audit_link(renderer: Path, additional_objects=()):
    """Prove no library executable/data contribution escapes the OBJ audit.

    Parse 16-bit OMF SEGDEF/LNAMES records from every explicit LNK input, apply
    each contribution's actual alignment in input order, and compare the totals
    with the final MAP. The import libraries may supply import records, but any
    extra CODE/DATA bytes (including an unlisted runtime helper) fail this test.
    """
    ega = Path(renderer) / "SRC"
    objects = re.findall(r"\b([a-z0-9_]+\.obj)\b", normalized(ega / "VGA88.LNK"), re.I)
    if not objects or len({name.upper() for name in objects}) != len(objects):
        raise RuntimeError('Link response file must list a nonempty, unique set of objects')
    totals = {}
    details = []
    def omf_index(data, position):
        first = data[position]
        if first & 128:
            return ((first & 127) << 8) | data[position+1], position+2
        return first, position+1
    for name in objects:
        raw = (ega / name.upper()).read_bytes()
        offset, names, contributions = 0, [""], []
        while offset < len(raw):
            if offset + 3 > len(raw):
                raise RuntimeError("Truncated OMF: " + name)
            kind = raw[offset]
            size = int.from_bytes(raw[offset+1:offset+3], "little")
            if size < 1 or offset+3+size > len(raw):
                raise RuntimeError("Invalid OMF record: " + name)
            data = raw[offset+3:offset+2+size]  # exclude record checksum
            offset += 3+size
            if kind == 0x96:  # LNAMES
                position = 0
                while position < len(data):
                    length = data[position]
                    names.append(data[position+1:position+1+length].decode("ascii"))
                    position += 1+length
                if position != len(data):
                    raise RuntimeError("Invalid OMF names: " + name)
            elif kind == 0x99 or kind in (0xC2, 0xC3):
                raise RuntimeError("Unreviewed 32-bit segment/COMDAT: " + name)
            elif kind == 0x98:  # 16-bit SEGDEF
                attribute = data[0]
                alignment_code, combine = attribute >> 5, (attribute >> 2) & 7
                position = 1 + (3 if alignment_code == 0 else 0)
                length = int.from_bytes(data[position:position+2], "little")
                position += 2
                name_index, position = omf_index(data, position)
                class_index, position = omf_index(data, position)
                key = (names[name_index], names[class_index].upper())
                if key[1] not in ("CODE", "DATA"):
                    continue
                if alignment_code not in (1, 2, 3, 4, 5) or combine != 2 or attribute & 3:
                    raise RuntimeError("Unreviewed OMF segment attributes: " + repr((name, key, attribute)))
                alignment = {1: 1, 2: 2, 3: 16, 4: 256, 5: 4}[alignment_code]
                start = totals.get(key, 0)
                start = ((start + alignment-1) // alignment) * alignment
                totals[key] = start + length
                contributions.append({"segment": key[0], "class": key[1],
                                      "start": start, "bytes": length, "alignment": alignment})
        details.append({"object": name.upper(), "contributions": contributions})
    # LINK4 aligns even zero-length contributions and treats CODE class names
    # case-insensitively. Only nonempty final segments appear in this comparison.
    totals = {key: value for key, value in totals.items() if value}
    mapped = {}
    for length, name, kind in re.findall(
            r"^\s+[0-9A-F]{4}:[0-9A-F]{4}\s+([0-9A-F]+)H\s+(\S+)\s+(CODE|DATA)\s*$",
            normalized(ega / "VGA88.MAP"), flags=re.I | re.M):
        if int(length, 16):
            key = (name, kind.upper())
            if key in mapped:
                raise RuntimeError("Duplicate nonempty MAP segment: " + name)
            mapped[key] = int(length, 16)
    if not mapped or totals != mapped:
        raise RuntimeError("Unaccounted linked CODE/DATA bytes: objects=" + repr(totals) + "; map=" + repr(mapped))
    return {"result": "PASS", "explicit_objects": len(objects), "extra_library_code_bytes": 0,
            "segments": [{"name": key[0], "class": key[1], "bytes": value}
                         for key, value in sorted(totals.items())], "objects": details}

if __name__=="__main__": print(json.dumps(audit_link(Path(sys.argv[1])),indent=2))
