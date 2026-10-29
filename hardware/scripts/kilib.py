"""Load symbols from the stock KiCad symbol libraries (flattening `extends`)."""
import copy
import os

from sexpr import Sym, find, find_all, parse

KICAD_SHARE = os.environ.get("KICAD_SHARE", r"C:\Program Files\KiCad\10.0\share\kicad")
_cache = {}


def _lib(name):
    if name not in _cache:
        path = os.path.join(KICAD_SHARE, "symbols", name + ".kicad_sym")
        with open(path, encoding="utf-8") as f:
            tree = parse(f.read())
        _cache[name] = {s[1]: s for s in find_all(tree, "symbol")}
    return _cache[name]


def load_symbol(lib_id):
    """Return a flattened symbol definition named `lib_id` (e.g. "Device:R")."""
    lib, name = lib_id.split(":")
    sym = copy.deepcopy(_lib(lib)[name])
    ext = find(sym, "extends")
    if ext:
        parent = load_symbol(f"{lib}:{ext[1]}")
        pname = parent[1].split(":")[1]
        props = {p[1]: p for p in find_all(sym, "property")}
        flat = [Sym("symbol"), name]
        for item in parent[2:]:
            if isinstance(item, list) and item[0] == "property" and item[1] in props:
                flat.append(props.pop(item[1]))
            elif isinstance(item, list) and item[0] == "symbol":
                sub = copy.deepcopy(item)
                sub[1] = sub[1].replace(pname, name, 1)
                flat.append(sub)
            else:
                flat.append(item)
        # child-only properties go before the unit sub-symbols
        idx = next(i for i, x in enumerate(flat) if isinstance(x, list) and x[0] == "symbol")
        for p in props.values():
            flat.insert(idx, p)
            idx += 1
        sym = flat
    sym[1] = lib_id
    return sym


def pins(sym):
    """Map pin number -> dict(name, type, x, y, angle) for unit 1 / body style 1."""
    out = {}
    base = sym[1].split(":")[1]
    for sub in find_all(sym, "symbol"):
        unit, style = sub[1][len(base) + 1:].split("_")
        if unit not in ("0", "1") or style not in ("0", "1"):
            continue
        for p in find_all(sub, "pin"):
            at = find(p, "at")
            out[find(p, "number")[1]] = dict(
                name=find(p, "name")[1], type=str(p[1]),
                x=float(at[1]), y=float(at[2]), angle=float(at[3]),
                hidden=find(p, "hide") is not None and find(p, "hide")[1] == "yes")
    return out
