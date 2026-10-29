"""Generate esp32s3-usbc.kicad_pcb from design.py (run with KiCad's bundled Python).

Places footprints from the stock libraries, assigns nets, routes tracks from
the hand-planned ROUTES list, and pours GND on both layers.
"""
import os

import kilib
import pcbnew
from design import BOARD_H, BOARD_W, PARTS, POWER_NETS, PROJECT, uid
from sexpr import find_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", PROJECT, PROJECT + ".kicad_pcb")
FP_DIR = os.path.join(os.environ.get("KICAD_SHARE", r"C:\Program Files\KiCad\10.0\share\kicad"),
                      "footprints")
mm = pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu

SIG, PWR = 0.2, 0.5

# Route = (net, layer, width, points). Points are "REF.PAD" (optionally "#k" for
# the k-th pad of that number, sorted by x then y), absolute (x, y), or
# ("x", v) / ("y", v) for a horizontal / vertical move from the previous point.
ROUTES = [
    # --- USB-C receptacle -> ESD -> module (top) ---
    ("USB_D+", F, SIG, ["J1.A6", ("y", 37.7), ("x", 18.75), ("y", 36.4), (18.95, 36.0), "D1.3"]),
    ("USB_D+", F, SIG, ["J1.B6", (18.75, 37.7)]),
    ("USB_D+", F, SIG, ["D1.3", "D1.4"]),
    ("USB_D+", F, SIG, ["D1.4", ("y", 28.0), ("x", 9.25), "U1.14"]),
    ("USB_D-", F, SIG, ["J1.B7", ("y", 36.4), (17.05, 36.0), "D1.1"]),
    ("USB_D-", F, SIG, ["D1.1", "D1.6"]),
    ("USB_D-", F, SIG, ["D1.6", ("y", 28.8), ("x", 8.0), ("y", 22.73), "U1.13"]),
    # second D- contact joined underneath the receptacle
    ("USB_D-", F, SIG, ["J1.B7", (17.25, 40.2)]),
    ("USB_D-", F, SIG, ["J1.A7", (18.25, 40.2)]),
    ("USB_D-", B, SIG, [(17.25, 40.2), (18.25, 40.2)]),
    ("CC1", F, SIG, ["J1.A5", ("y", 36.5), "R1.1"]),
    ("CC2", F, SIG, ["J1.B5", ("y", 36.5), "R2.1"]),
    # --- VBUS (bottom) -> fuse -> LDO ---
    ("VBUS", F, PWR, ["J1.A4", (15.6, 37.9)]),
    ("VBUS", F, PWR, ["J1.A9", (20.4, 37.9)]),
    ("VBUS", B, PWR, [(15.6, 37.9), (20.4, 37.9), (20.4, 33.9), (20.4, 30.6), (18, 30.6)]),
    ("VBUS", F, SIG, ["D1.5", (18, 30.6)]),
    ("VBUS", F, PWR, [(20.4, 33.9), "F1.1"]),
    ("+5V", F, PWR, ["F1.2", "U2.3"]),
    ("+5V", F, PWR, ["C1.1", "U2.3"]),
    # --- 3V3 distribution ---
    ("+3V3", F, PWR, ["U2.2#0", "U2.2#1"]),
    ("+3V3", F, PWR, ["C2.1", ("x", 33.15), "U2.2#1"]),
    ("+3V3", F, PWR, ["U2.2#0", (25.0, 31.6)]),
    ("+3V3", B, PWR, [(25.0, 31.6), ("y", 27.0), ("x", 6.75), ("y", 8.76)]),
    ("+3V3", F, PWR, ["U1.2", "C4.1", (6.75, 8.76), "C3.1", "J2.1"]),
    ("+3V3", B, PWR, [(6.75, 27.0), ("y", 31.5)]),
    ("+3V3", F, SIG, [(6.75, 31.5), "R4.1"]),
    ("+3V3", F, SIG, [(6.75, 31.5), "R3.1"]),
    ("LED_A", F, SIG, ["R4.2", "D2.2"]),
    # --- EN / reset ---
    ("EN", F, SIG, ["U1.3", (5.4, 10.03)]),
    ("EN", B, SIG, [(5.4, 10.03), ("y", 36.0)]),
    ("EN", F, SIG, ["R3.2", (5.4, 36.0), ("x", 5.975), "C5.1"]),
    ("EN", F, SIG, ["C5.1", ("x", 7.3), ("y", 39.75)]),
    ("EN", F, SIG, ["SW2.1#0", (7.3, 39.75), "SW2.1#1"]),
    # --- BOOT ---
    ("IO0", F, SIG, ["U1.27", ("x", 35.2), ("y", 40.25), "SW1.1#1", "SW1.1#0"]),
    # --- headers ---
    ("IO1", F, SIG, ["U1.39", "J3.1"]),
    ("IO2", F, SIG, ["U1.38", ("x", 31.4), ("y", 11.30), "J3.2"]),
    ("TXD0", F, SIG, ["U1.37", ("x", 30.85), ("y", 13.84), "J3.3"]),
    ("RXD0", F, SIG, ["U1.36", ("x", 30.3), ("y", 16.38), "J3.4"]),
    ("IO4", F, SIG, ["U1.4", ("x", 4.5), ("y", 13.84), "J2.3"]),
    ("IO5", F, SIG, ["U1.5", ("x", 5.05), ("y", 16.38), "J2.4"]),
    ("IO6", F, SIG, ["U1.6", ("x", 5.6), ("y", 18.92), "J2.5"]),
    ("IO7", F, SIG, ["U1.7", ("x", 6.15), ("y", 21.46), "J2.6"]),
    ("IO15", F, SIG, ["U1.8", ("x", 6.7), ("y", 24.0), "J2.7"]),
    ("IO16", F, SIG, ["U1.9", ("x", 7.25), ("y", 26.54), "J2.8"]),
    # --- local GND ties (rest is handled by the pours) ---
    ("GND", F, PWR, ["C3.2", "C4.2", "U1.1"]),
    ("GND", F, SIG, ["C3.2", (4.5, 6.9)]),
    ("GND", F, PWR, ["C2.2", ("x", 26.85), "U2.1"]),
    ("GND", F, SIG, ["J1.A1", "J1.SH#0"]),
    ("GND", F, SIG, ["J1.B1", "J1.SH#2"]),
    ("GND", F, SIG, ["D1.2", (18, 35.3)]),
    ("GND", F, SIG, ["R1.2", (11.9, 36.5)]),
    ("GND", F, SIG, ["R2.2", (24.1, 36.5)]),
    ("GND", F, SIG, ["C1.2", (26, 38.9)]),
    ("GND", F, SIG, ["C5.2", (3.4, 37.4)]),
    ("GND", F, SIG, ["D2.1", (1.2, 33.0)]),
    ("GND", F, SIG, ["U1.40", (28.3, 7.49)]),
]

VIAS = [
    ("USB_D-", 17.25, 40.2), ("USB_D-", 18.25, 40.2),
    ("VBUS", 15.6, 37.9), ("VBUS", 20.4, 37.9), ("VBUS", 20.4, 33.9), ("VBUS", 18, 30.6),
    ("+3V3", 25.0, 31.6), ("+3V3", 6.75, 8.76), ("+3V3", 6.75, 31.5),
    ("EN", 5.4, 10.03), ("EN", 5.4, 36.0),
    ("GND", 4.5, 6.9), ("GND", 28.5, 26.9), ("GND", 18, 35.3), ("GND", 11.9, 36.5),
    ("GND", 24.1, 36.5), ("GND", 26, 38.9), ("GND", 3.4, 37.4), ("GND", 1.2, 33.0),
    ("GND", 28.3, 7.49),
    # stitching
    ("GND", 1.2, 28.5), ("GND", 12.0, 31.0), ("GND", 24.0, 30.0), ("GND", 34.8, 21.5),
    ("GND", 11.5, 44.5), ("GND", 24.5, 44.5), ("GND", 30.0, 37.0), ("GND", 14.0, 33.5),
]


# Reference-designator silkscreen overrides: (x, y, angle) or None to hide.
REF_SILK = {
    "C3": (5.3, 5.0, 0), "C4": (7.5, 5.0, 0), "C5": (1.5, 37.4, 90), "C2": (34.4, 26.9, 90),
    "U2": (30.5, 36.3, 0), "R1": (13.5, 35.0, 0), "R2": (21.0, 35.6, 0),
    "SW1": None, "SW2": None,
}


def net_name(net):
    if net in POWER_NETS or net.startswith("unconnected-"):
        return net
    return "/" + net


def main():
    board = pcbnew.NewBoard(os.path.abspath(OUT))
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.2)  # module footprint has 0.2 mm thermal vias
    ds.m_HoleClearance = mm(0.15)  # USB4105 GND pads sit 0.19 mm from its NPTH pegs
    ds.m_MinClearance = mm(0.15)
    ds.m_CopperEdgeClearance = mm(0.3)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.15))
    nc.SetTrackWidth(mm(SIG))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))

    nets = {}

    def get_net(name):
        name = net_name(name)
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    # outline
    pts = [(0, -0.5), (BOARD_W, -0.5), (BOARD_W, BOARD_H), (0, BOARD_H)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        seg.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        seg.SetWidth(mm(0.1))
        board.Add(seg)

    fps = {}
    for ref, (lib_id, value, fp_id, _sch, (x, y, rot), pin_nets) in PARTS.items():
        lib, name = fp_id.split(":")
        fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)
        fp.SetPath(pcbnew.KIID_PATH("/" + uid("sym", ref)))
        fp.SetSheetname("/")
        fp.SetSheetfile(PROJECT + ".kicad_sch")
        board.Add(fp)
        sym = kilib.load_symbol(lib_id)
        for prop in find_all(sym, "property"):
            if prop[1] == "ki_fp_filters":
                fp.SetFilters(prop[2])
            elif prop[1] not in ("Reference", "Value", "Footprint"):
                fp.SetField(prop[1], prop[2])
                fp.GetField(prop[1]).SetVisible(False)
        sym_pins = kilib.pins(sym)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in pin_nets:
                pad.SetNet(get_net(pin_nets[num]))
                if ref == "J1" and pin_nets[num] == "GND":
                    # fine-pitch GND contacts can't fit two spokes; they're tied to SH anyway
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            elif num in sym_pins:  # same name eeschema gives an unconnected pin
                pad.SetNet(get_net(f"unconnected-({ref}-{sym_pins[num]['name']}-Pad{num})"))
        fps[ref] = fp
        if ref in REF_SILK:
            silk = REF_SILK[ref]
            if silk is None:
                fp.Reference().SetVisible(False)
            else:
                fp.Reference().SetPosition(pcbnew.VECTOR2I(mm(silk[0]), mm(silk[1])))
                fp.Reference().SetTextAngleDegrees(silk[2])

    def pad_pos(token):
        ref, num = token.split(".")
        idx = 0
        if "#" in num:
            num, idx = num.split("#")
            idx = int(idx)
        pads = sorted((p for p in fps[ref].Pads() if p.GetNumber() == num),
                      key=lambda p: (p.GetPosition().x, p.GetPosition().y))
        pos = pads[idx].GetPosition()
        return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)

    for net, layer, width, points in ROUTES:
        coords = []
        for p in points:
            if isinstance(p, str):
                coords.append(pad_pos(p))
            elif p[0] == "x":
                coords.append((p[1], coords[-1][1]))
            elif p[0] == "y":
                coords.append((coords[-1][0], p[1]))
            else:
                coords.append(p)
        for a, b in zip(coords, coords[1:]):
            if a == b:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            t.SetWidth(mm(width))
            t.SetLayer(layer)
            t.SetNet(get_net(net))
            board.Add(t)

    for net, x, y in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(get_net(net))
        board.Add(v)

    # GND pours, both layers
    for layer in (F, B):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(get_net("GND"))
        z.SetLocalClearance(mm(0.25))
        z.SetMinThickness(mm(0.2))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(mm(x), mm(y))
        board.Add(z)

    # silkscreen
    for text, x, y, layer, size in [
        ("ESP32-S3 USB-C Demo", BOARD_W / 2, 30.0, pcbnew.B_SilkS, 1.2),
        ("Claude-ESP32-PCB-Demo rev A", BOARD_W / 2, 32.0, pcbnew.B_SilkS, 0.8),
        ("BOOT", 24.6, 42.5, pcbnew.F_SilkS, 0.8),
        ("RST", 11.9, 42.0, pcbnew.F_SilkS, 0.8),
    ]:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(size * 0.15))
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        elif x not in (BOARD_W / 2,):
            t.SetTextAngleDegrees(90)
        board.Add(t)

    pcbnew.SaveBoard(os.path.abspath(OUT), board)
    # fill on a freshly loaded copy so the filler sees the saved design rules
    board = pcbnew.LoadBoard(os.path.abspath(OUT))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(os.path.abspath(OUT), board)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
