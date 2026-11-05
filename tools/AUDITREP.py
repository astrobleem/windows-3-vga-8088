import json,re,sys,importlib.machinery
from pathlib import Path
COMPILED_COUNTS={"CBLT.LST":8,"BITBLT.LST":1,"BMC_ITE.LST":1}
PREFIXES={0x26,0x2e,0x36,0x3e,0xf0,0xf2,0xf3}
def instruction_rows(path):
    # AUDIT88 independently rejects every unclassified emitted instruction.
    isa = importlib.machinery.SourceFileLoader("repcopy_isa", str(Path(__file__).with_name("AUDIT88.py"))).load_module()
    data_words = {"db", "dw", "dd", "dq", "dt", "bitmap", "bitmapinfoheader", "rgbquad", "rgbtriple", "bitmapcoreheader", "cursorinfo", "cursorshape"}
    last = None
    for lineno, raw in enumerate(Path(path).read_text(errors="replace").splitlines(), 1):
        line = raw.expandtabs(8)
        if not re.match(r"^ [0-9A-F]{4}  [0-9A-F]{2}", line):
            continue
        source = line[32:].strip().split(";", 1)[0].strip()
        words = source.split()
        if words and words[0].endswith(":"):
            words = words[1:]
        if not words:
            continue
        mnemonic = words[0].lower()
        if mnemonic in data_words or (len(words)>1 and words[1].lower() in data_words) or mnemonic == "even":
            continue
        if mnemonic not in isa.MNEMONICS and mnemonic != "out16":
            raise AssertionError("Unclassified emitted listing row: " + line)
        tokens = re.findall(r"[0-9A-F]{2,8}", line[7:28])
        if not tokens:
            raise AssertionError("No machine bytes: " + line)
        address = int(line[1:5], 16)
        # MASM displays words in value order; prefix/opcode bytes are individual
        # tokens. Only leading bytes are decoded, never immediates/relocations.
        leading = []
        for token in tokens:
            leading.append(int(token[:2], 16))
            if len(token) != 2 or leading[-1] not in PREFIXES:
                break
        key = (address, tuple(tokens))
        if key == last:
            continue  # Macro invocation header may duplicate expansion bytes.
        last = key
        yield {"file": Path(path).name, "line": lineno, "address": address,
               "tokens": tokens, "leading": leading, "source": source}


def audit_listings(paths, require_replacements=True):
    bad, replacements, prefix_rows, single_rep, instructions = [], [], 0, 0, 0
    for path in paths:
        rows = list(instruction_rows(path))
        pending, pending_end = [], None
        for index, row in enumerate(rows):
            instructions += 1
            leading = row["leading"]
            if pending and row["address"] != pending_end:
                raise AssertionError("Noncontiguous standalone instruction prefixes: " + str(row))
            combined = pending + leading
            prefixes = []
            for value in combined:
                if value not in PREFIXES:
                    break
                prefixes.append(value)
            if any(value in (0xf2, 0xf3) for value in prefixes):
                if len(prefixes) > 1:
                    bad.append({**row, "prefixes": [f"{value:02X}" for value in prefixes]})
                elif len(combined) > len(prefixes):
                    single_rep += 1
            if len(combined) == len(prefixes):
                pending = combined
                pending_end = row["address"] + len(leading)
                prefix_rows += 1
                continue
            pending, pending_end = [], None
            if re.search(r"\bjcxz\s+rc88_\w+_done$", row["source"], re.I):
                triplet = rows[index:index+3]
                tokens = [value for item in triplet for value in item["tokens"]]
                if (len(triplet) != 3 or tokens[:2] != ["E3", "04"] or
                    tokens[2:4] not in (["26", "A4"], ["2E", "A4"], ["2E", "A5"]) or
                    tokens[4:] != ["E2", "FC"] or
                    [item["address"] for item in triplet] != [row["address"]+n for n in (0,2,4)]):
                    raise AssertionError("Unexpected REPCOPY88 machine code: " + str(triplet))
                replacements.append({"file": row["file"], "line": row["line"],
                    "address": f"{row['address']:04X}", "bytes": " ".join(tokens), "source": row["source"]})
        if pending:
            raise AssertionError("Unterminated standalone instruction prefix in " + str(path))
    counts = {name: sum(row["file"] == name for row in replacements) for name in COMPILED_COUNTS}
    report = {"instruction_rows_checked": instructions, "multi_prefix_rep": bad,
              "standalone_prefix_rows_checked": prefix_rows, "single_prefix_rep_retained": single_rep,
              "replacement_counts": counts, "replacement_sites": replacements,
              "scope": "Decoded emitted instruction prefixes across all linked listings, including adjacent standalone prefix rows; pinned dynamic emitter reviewed separately"}
    if bad or (require_replacements and counts != COMPILED_COUNTS):
        raise AssertionError(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(audit_listings([Path(path) for path in sys.argv[1:]]), indent=2))
