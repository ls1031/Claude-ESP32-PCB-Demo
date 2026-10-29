"""Single source of truth for the ESP32-S3 USB-C demo board.

Both gen_schematic.py and gen_pcb.py read this, so schematic and layout
always agree on parts, footprints and nets.
"""
import uuid

PROJECT = "esp32s3-usbc"
_NS = uuid.UUID("6f1c2b8e-3d4a-4e8f-9b1a-c1a0de5e3201")


def uid(*key):
    return str(uuid.uuid5(_NS, "/".join(key)))


ROOT_UUID = uid("root")

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
TACT = "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92"

# ref: (lib_id, value, footprint, sch (x, y), pcb (x, y, rot), {pin: net})
# Pins not listed get a no-connect flag in the schematic.
PARTS = {
    "U1": ("RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1", "RF_Module:ESP32-S3-WROOM-1",
           (190.5, 114.3), (18, 12.75, 0),
           {"1": "GND", "40": "GND", "41": "GND", "2": "+3V3", "3": "EN", "27": "IO0",
            "13": "USB_D-", "14": "USB_D+", "37": "TXD0", "36": "RXD0",
            "39": "IO1", "38": "IO2", "4": "IO4", "5": "IO5", "6": "IO6", "7": "IO7",
            "8": "IO15", "9": "IO16"}),
    "J1": ("Connector:USB_C_Receptacle_USB2.0_16P", "USB_C",
           "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
           (50.8, 165.1), (18, 42.5, 0),
           {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
            "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
            "A5": "CC1", "B5": "CC2", "A6": "USB_D+", "B6": "USB_D+",
            "A7": "USB_D-", "B7": "USB_D-"}),
    "R1": ("Device:R", "5.1k", R0603, (81.28, 182.88), (13.5, 36.5, 180),
           {"1": "CC1", "2": "GND"}),
    "R2": ("Device:R", "5.1k", R0603, (91.44, 182.88), (22.5, 36.5, 0),
           {"1": "CC2", "2": "GND"}),
    "D1": ("Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
           (119.38, 165.1), (18, 33, 90),
           {"1": "USB_D-", "6": "USB_D-", "3": "USB_D+", "4": "USB_D+",
            "5": "VBUS", "2": "GND"}),
    "F1": ("Device:Polyfuse", "500mA", "Fuse:Fuse_1206_3216Metric",
           (40.64, 55.88), (22.9, 33.9, 0), {"1": "VBUS", "2": "+5V"}),
    "C1": ("Device:C", "10uF", C0805, (55.88, 63.5), (26, 37.0, 270),
           {"1": "+5V", "2": "GND"}),
    "U2": ("Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
           (76.2, 55.88), (30, 31.6, 0), {"1": "GND", "2": "+3V3", "3": "+5V"}),
    "C2": ("Device:C", "10uF", C0805, (96.52, 63.5), (31, 26.9, 180),
           {"1": "+3V3", "2": "GND"}),
    "C3": ("Device:C", "22uF", C0805, (149.86, 66.04), (5.87, 7.81, 90),
           {"1": "+3V3", "2": "GND"}),
    "C4": ("Device:C", "100nF", "Capacitor_SMD:C_0402_1005Metric", (162.56, 66.04), (7.78, 8.28, 90),
           {"1": "+3V3", "2": "GND"}),
    "R3": ("Device:R", "10k", R0603, (137.16, 104.14), (6.0, 34.5, 180),
           {"1": "+3V3", "2": "EN"}),
    "C5": ("Device:C", "1uF", C0603, (137.16, 129.54), (5.2, 37.4, 180),
           {"1": "EN", "2": "GND"}),
    "SW2": ("Switch:SW_Push", "RESET", TACT, (124.46, 121.92), (6, 42, 0),
            {"1": "EN", "2": "GND"}),
    "SW1": ("Switch:SW_Push", "BOOT", TACT, (124.46, 93.98), (30, 42.5, 0),
            {"1": "IO0", "2": "GND"}),
    "R4": ("Device:R", "1k", R0603, (116.84, 55.88), (5.0, 31.5, 180),
           {"1": "+3V3", "2": "LED_A"}),
    "D2": ("Device:LED", "PWR", "LED_SMD:LED_0603_1608Metric", (116.84, 71.12),
           (2.0, 31.5, 0), {"2": "LED_A", "1": "GND"}),
    "J2": ("Connector_Generic:Conn_01x08", "GPIO_L",
           "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
           (254.0, 101.6), (3, 8.76, 0),
           {"1": "+3V3", "2": "GND", "3": "IO4", "4": "IO5", "5": "IO6", "6": "IO7",
            "7": "IO15", "8": "IO16"}),
    "J3": ("Connector_Generic:Conn_01x05", "UART",
           "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
           (254.0, 137.16), (33, 8.76, 0),
           {"1": "IO1", "2": "IO2", "3": "TXD0", "4": "RXD0", "5": "GND"}),
}

POWER_NETS = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V", "VBUS": "power:VBUS"}
# Nets with no power_out driver get a PWR_FLAG (placed in the schematic only).
PWR_FLAGS = {"VBUS": (25.4, 38.1), "+5V": (55.88, 38.1), "GND": (66.04, 38.1)}

# Board outline (mm)
BOARD_W, BOARD_H = 36.0, 46.0
