"""
Generates a simple wiring/block diagram for the Smart Irrigation & Climate
Automation System (ESP32-based). Not a full schematic - a clear connection
diagram suitable for a README, showing which module connects to which pin.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

fig, ax = plt.subplots(figsize=(10, 7))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis("off")

def box(x, y, w, h, text, color="#dce9f9"):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                    linewidth=1.5, edgecolor="#1f4e79", facecolor=color)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10, wrap=True)
    return (x, y, w, h)

def connect(box_a, side_a, box_b, side_b, label=""):
    xa, ya, wa, ha = box_a
    xb, yb, wb, hb = box_b
    points = {
        "right": (xa + wa, ya + ha / 2),
        "left": (xa, ya + ha / 2),
        "top": (xa + wa / 2, ya + ha),
        "bottom": (xa + wa / 2, ya),
    }
    pb = {
        "right": (xb + wb, yb + hb / 2),
        "left": (xb, yb + hb / 2),
        "top": (xb + wb / 2, yb + hb),
        "bottom": (xb + wb / 2, yb),
    }
    p1 = points[side_a]
    p2 = pb[side_b]
    ax.add_line(Line2D([p1[0], p2[0]], [p1[1], p2[1]], color="#333333", linewidth=1.4))
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    if label:
        ax.text(mx, my + 0.15, label, ha="center", fontsize=8, color="#555555")

# ESP32 in the center
esp32 = box(4, 3.2, 2.2, 1.6, "ESP32\nDevKit", color="#ffe9b3")

dht22 = box(0.4, 6.0, 2.2, 1.1, "DHT22\nTemp/Humidity", color="#dce9f9")
soil = box(0.4, 4.0, 2.2, 1.1, "Capacitive Soil\nMoisture Sensor", color="#dce9f9")
ldr = box(0.4, 2.0, 2.2, 1.1, "LDR Light\nSensor (voltage divider)", color="#dce9f9")

pump_relay = box(7.4, 5.2, 2.2, 1.1, "Relay Module\n(Water Pump)", color="#f9dcdc")
fan_relay = box(7.4, 3.2, 2.2, 1.1, "Relay Module\n(Fan / Vent)", color="#f9dcdc")
psu = box(7.4, 1.0, 2.2, 1.1, "5V/12V PSU\n(pump + fan power)", color="#e3f9dc")

wifi = box(4, 0.6, 2.2, 1.0, "WiFi -> Local\nWeb Dashboard", color="#e9dcf9")

connect(dht22, "right", esp32, "left", "GPIO4 (1-wire)")
connect(soil, "right", esp32, "left", "GPIO34 (ADC)")
connect(ldr, "right", esp32, "left", "GPIO35 (ADC)")
connect(esp32, "right", pump_relay, "left", "GPIO26")
connect(esp32, "right", fan_relay, "left", "GPIO27")
connect(psu, "top", fan_relay, "bottom", "12V")
connect(psu, "left", pump_relay, "bottom", "12V")
connect(esp32, "bottom", wifi, "top", "802.11")

ax.set_title("Smart Irrigation & Climate Automation - Wiring Overview", fontsize=13, pad=15)
plt.tight_layout()
plt.savefig("wiring_diagram.png", dpi=150)
print("Saved wiring_diagram.png")
