"""Generate esp32s3-usbc.kicad_sch from design.py.

Every connection is made with a net label or power symbol placed directly on
the pin tip, so no wire geometry is needed. Unused pins get no-connect flags.
"""
import copy
import os
import sys

import kilib
from design import PARTS, POWER_NETS, PROJECT, PWR_FLAGS, ROOT_UUID, uid
from sexpr import Sym, dump, find, find_all

OUT = os.path.join(os.path.dirname(__file__), "..", PROJECT, PROJECT + ".kicad_sch")
S = Sym


def snap(v):
    return round(v / 1.27) * 1.27


def font(justify=None, hide=False):
    eff = [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]
    if justify:
        eff.append([S("justify"), *[S(j) for j in justify.split()]])
    out = [eff]
    if hide:
        out.insert(0, [S("hide"), S("yes")])
    return out


# outward direction of a pin in schematic coordinates (y down)
def outward(angle):
    return {0: "left", 180: "right", 90: "down", 270: "up"}[int(angle) % 360]


GND_ROT = {"down": 0, "right": 90, "up": 180, "left": 270}
UP_ROT = {"up": 0, "left": 90, "down": 180, "right": 270}
LABEL = {"right": (0, "left"), "left": (180, "right"), "up": (90, "left"), "down": (270, "right")}


class Sheet:
    def __init__(self):
        self.lib = {}
        self.items = []
        self.pwr_n = 0

    def use(self, lib_id):
        if lib_id not in self.lib:
            self.lib[lib_id] = kilib.load_symbol(lib_id)
        return self.lib[lib_id]

    def place(self, lib_id, ref, value, x, y, rot=0, footprint=None, key=None):
        sym = self.use(lib_id)
        key = key or ref
        node = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, rot], [S("unit"), 1],
                [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
                [S("on_board"), S("yes")], [S("dnp"), S("no")], [S("uuid"), uid("sym", key)]]
        for p in find_all(sym, "property"):
            p = copy.deepcopy(p)
            if p[1] == "Reference":
                p[2] = ref
            elif p[1] == "Value":
                p[2] = value
            elif p[1] == "Footprint" and footprint is not None:
                p[2] = footprint
            at = find(p, "at")
            px, py = float(at[1]), float(at[2])
            if rot == 0:
                at[1], at[2] = x + px, y - py
            else:  # power symbols only: keep text next to the symbol
                at[1], at[2], at[3] = x, y, 0
            node.append(p)
        for num in kilib.pins(sym):
            node.append([S("pin"), num, [S("uuid"), uid("pin", key, num)]])
        node.append([S("instances"), [S("project"), PROJECT,
                     [S("path"), "/" + ROOT_UUID, [S("reference"), ref], [S("unit"), 1]]]])
        self.items.append(node)
        return sym

    def power(self, net, x, y, direction):
        self.pwr_n += 1
        lib_id = POWER_NETS[net]
        rot = GND_ROT[direction] if net == "GND" else UP_ROT[direction]
        self.place(lib_id, f"#PWR{self.pwr_n:02d}", net, x, y, rot, key=f"pwr{self.pwr_n}")

    def label(self, net, x, y, direction):
        rot, just = LABEL[direction]
        self.items.append([S("label"), net, [S("at"), x, y, rot], *font(just),
                           [S("uuid"), uid("label", net, f"{x:.2f}", f"{y:.2f}")]])

    def no_connect(self, x, y):
        self.items.append([S("no_connect"), [S("at"), x, y],
                           [S("uuid"), uid("nc", f"{x:.2f}", f"{y:.2f}")]])

    def text(self, s, x, y, size=2.54):
        self.items.append([S("text"), s, [S("exclude_from_sim"), S("no")], [S("at"), x, y, 0],
                           [S("effects"), [S("font"), [S("size"), size, size]],
                            [S("justify"), S("left")]],
                           [S("uuid"), uid("text", s)]])

    def write(self, path):
        root = [S("kicad_sch"), [S("version"), S("20250610")], [S("generator"), "gen_schematic.py"],
                [S("generator_version"), "10.0"], [S("uuid"), ROOT_UUID], [S("paper"), "A3"],
                [S("title_block"), [S("title"), "ESP32-S3 USB-C Demo"], [S("date"), "2026-10-28"],
                 [S("rev"), "A"], [S("company"), "Claude-ESP32-PCB-Demo"]],
                [S("lib_symbols"), *self.lib.values()],
                *self.items,
                [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
                [S("embedded_fonts"), S("no")]]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dump(root) + "\n")


def main():
    sh = Sheet()
    for ref, (lib_id, value, fp, (x, y), _pcb, nets) in PARTS.items():
        sym = sh.place(lib_id, ref, value, x, y, footprint=fp)
        done = set()
        for num, pin in kilib.pins(sym).items():
            px, py = round(x + pin["x"], 2), round(y - pin["y"], 2)
            if (px, py) in done:
                continue  # stacked pins share one connection point
            done.add((px, py))
            net = nets.get(num)
            d = outward(pin["angle"])
            if net is None:
                sh.no_connect(px, py)
            elif net in POWER_NETS:
                sh.power(net, px, py, d)
            else:
                sh.label(net, px, py, d)
        unknown = set(nets) - set(kilib.pins(sym))
        if unknown:
            sys.exit(f"{ref}: unknown pins {unknown}")
    for i, (net, (x, y)) in enumerate(PWR_FLAGS.items(), 1):
        sh.place("power:PWR_FLAG", f"#FLG{i:02d}", "PWR_FLAG", x, y, key=f"flg{i}")
        sh.power(net, x, y, "down" if net == "GND" else "up")
    sh.text("USB-C input, CC sink resistors, ESD", 30.48, 132.08)
    sh.text("5V -> 3.3V LDO, power LED", 30.48, 30.48)
    sh.text("ESP32-S3-WROOM-1 (native USB on GPIO19/20)", 142.24, 50.8)
    sh.text("Headers", 243.84, 88.9)
    sh.write(os.path.abspath(OUT))
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
