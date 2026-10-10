"""
CircuitForge AI - Diagram Generator
Generates Wokwi-compatible diagram.json from a validated ProjectSpec.
Uses deterministic templates — does NOT rely on unconstrained AI output.
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import ProjectSpec, ComponentInstance, Connection, PinAssignment
from catalog.components import CATALOG


# ── Wokwi attribute helpers ────────────────────────────────────────────────────

def _resistor_attrs(value: str = "220") -> dict:
    return {"resistance": value}


def _led_attrs(color: str = "red") -> dict:
    return {"color": color}


def _dht22_attrs() -> dict:
    return {"temperature": "25", "humidity": "50"}


def _hcsr04_attrs() -> dict:
    return {"distance": "100"}


def _buzzer_attrs() -> dict:
    return {"volume": "0.5"}


def _potentiometer_attrs(value: str = "0.5") -> dict:
    return {"value": value}


COMPONENT_ATTRS: dict[str, callable] = {
    "resistor_220": lambda inst: _resistor_attrs("220"),
    "resistor_1k": lambda inst: _resistor_attrs("1000"),
    "resistor_10k": lambda inst: _resistor_attrs("10000"),
    "led_red": lambda inst: _led_attrs("red"),
    "led_green": lambda inst: _led_attrs("green"),
    "led_blue": lambda inst: _led_attrs("blue"),
    "rgb_led": lambda inst: {},
    "dht22": lambda inst: _dht22_attrs(),
    "hc_sr04": lambda inst: _hcsr04_attrs(),
    "buzzer": lambda inst: _buzzer_attrs(),
    "push_button": lambda inst: {},
    "light_button": lambda inst: {"color": "green"},
    "slide_switch": lambda inst: {},
    "potentiometer_10k": lambda inst: _potentiometer_attrs(),
    "photoresistor": lambda inst: {"lux": "500"},
    "pir_motion": lambda inst: {},
    "mq135": lambda inst: {},
    "servo": lambda inst: {},
    "relay": lambda inst: {},
    "lcd1602_i2c": lambda inst: {"pins": "i2c"},
    "ssd1306_i2c": lambda inst: {},
    "tft_ili9341": lambda inst: {},
    "mpu6050": lambda inst: {},
    "membrane_keypad": lambda inst: {},
    "ntc_temperature": lambda inst: {},
    "rotary_encoder": lambda inst: {},
    "analog_joystick": lambda inst: {},
    "led_bar_graph": lambda inst: {},
    "seven_segment": lambda inst: {},
    "dip_switch_8": lambda inst: {},
}

# Layout positions for parts — space them horizontally
X_STEP = 150
Y_BOARD = 100
Y_COMPONENTS = 350


def generate_diagram(spec: ProjectSpec) -> dict:
    """
    Generate a Wokwi-compatible diagram.json from a ProjectSpec.
    Returns a dict that can be serialized to JSON.
    """
    parts: list[dict] = []
    connections: list[list[str]] = []

    # ── Board ─────────────────────────────────────────────────────────────────
    board_wokwi_id = "wokwi-esp32-devkit-v1"
    parts.append({
        "id": "board",
        "type": board_wokwi_id,
        "top": Y_BOARD,
        "left": 200,
        "attrs": {}
    })

    # ── Components ────────────────────────────────────────────────────────────
    x = 50
    for inst in spec.components:
        cat = CATALOG.get(inst.catalog_id)
        if cat is None:
            continue  # skip unknown (already validated)

        attr_fn = COMPONENT_ATTRS.get(inst.catalog_id, lambda i: {})
        attrs = attr_fn(inst)
        if inst.catalog_id == "resistor_220" and inst.value:
            attrs = {"resistance": inst.value}
        elif inst.catalog_id == "resistor_10k" and inst.value:
            attrs = {"resistance": inst.value}

        parts.append({
            "id": inst.instance_id,
            "type": cat.wokwi_id,
            "top": Y_COMPONENTS,
            "left": x,
            "attrs": attrs,
        })
        x += X_STEP

    part_type_map: dict[str, str] = {p["id"]: p["type"] for p in parts}

    def _normalize_ref(ref: str) -> str:
        if ":" not in ref:
            return ref
        comp_id, pin = ref.split(":", 1)
        part_type = part_type_map.get(comp_id, "")
        if comp_id == "board":
            if pin.startswith("GPIO"):
                pin = f"D{pin[4:]}"
            elif pin.upper() == "GND":
                pin = "GND.1"
            return f"{comp_id}:{pin}"

        if part_type == "wokwi-ili9341":
            if pin.upper() in ("DC", "D_C"):
                pin = "D/C"
            elif pin.upper() in ("RESET", "RST_N"):
                pin = "RST"
        elif part_type == "wokwi-pushbutton":
            if pin.upper() in ("1.L", "SIG", "OUT", "BTN"):
                pin = "1.l"
            elif pin.upper() in ("2.L", "GND", "K"):
                pin = "2.l"
            elif pin.upper() in ("1.R", "LED+", "VCC"):
                pin = "1.r"
            elif pin.upper() in ("2.R", "LED-"):
                pin = "2.r"
        elif part_type == "wokwi-servo":
            if pin.upper() in ("VCC", "VIN", "5V", "V", "POWER", "V+"):
                pin = "V+"
            elif pin.upper() in ("GND", "GROUND", "-"):
                pin = "GND"
            elif pin.upper() in ("PWM", "SIG", "SIGNAL", "IN"):
                pin = "PWM"
        return f"{comp_id}:{pin}"

    # ── Connections ───────────────────────────────────────────────────────────
    # Build from spec.connections
    raw_connections: list[list] = []
    for conn in spec.connections:
        from_ref = f"{conn.from_component}:{conn.from_pin}"
        to_ref = f"{conn.to_component}:{conn.to_pin}"
        raw_connections.append([from_ref, to_ref, conn.wire_color, []])

    # If no explicit connections defined, generate from pin assignments
    if not raw_connections and spec.pin_assignments:
        raw_connections = _generate_connections_from_pin_assignments(spec)

    # Normalize all connection pins to Wokwi standards
    normalized_connections: list[list] = []
    for conn in raw_connections:
        from_norm = _normalize_ref(conn[0])
        to_norm = _normalize_ref(conn[1])
        color = conn[2] if len(conn) > 2 else "green"
        normalized_connections.append([from_norm, to_norm, color, []])

    diagram = {
        "version": 1,
        "author": "CircuitForge AI",
        "editor": "wokwi",
        "parts": parts,
        "connections": normalized_connections,
    }
    return diagram


def _generate_connections_from_pin_assignments(spec: ProjectSpec) -> list[list]:
    """
    Generate Wokwi connections from pin assignment metadata.
    Uses standard Wokwi ESP32 pin names (D2, D15, GND.1, 3V3).
    """
    connections: list[list] = []
    instance_map: dict[str, str] = {inst.instance_id: inst.catalog_id for inst in spec.components}

    for pa in spec.pin_assignments:
        board_pin = f"D{pa.gpio_pin}"
        inst_id = pa.component_instance
        comp_pin = pa.component_pin
        catalog_id = instance_map.get(inst_id, "")

        # Normalize pushbutton pins if needed
        if catalog_id in ("push_button", "light_button"):
            if comp_pin.upper() in ("1.L", "SIG", "OUT", "BTN"):
                comp_pin = "1.l"
            elif comp_pin.upper() in ("2.L", "GND", "LED-", "K"):
                comp_pin = "2.l"
            elif comp_pin.upper() in ("LED+", "VCC"):
                comp_pin = "1.r"

        color = "green"
        if "gnd" in comp_pin.lower() or comp_pin.lower() in ("k", "-", "gnd", "2.l"):
            color = "black"
        elif "vcc" in comp_pin.lower() or comp_pin.lower() in ("vcc", "+", "3v3", "1.r"):
            color = "red"

        # Board GPIO to component pin
        connections.append([
            f"board:{board_pin}", f"{inst_id}:{comp_pin}", color, []
        ])

    # Add power/ground connections for all components
    for inst in spec.components:
        cat = CATALOG.get(inst.catalog_id)
        if cat is None:
            continue
        for pin in cat.pins:
            if pin.pin_type == "power" and (pin.name.upper() in ("VCC", "3V3", "VIN", "LED") or pin.name in ("V+", "VCC")):
                connections.append([
                    "board:3V3", f"{inst.instance_id}:{pin.name}", "red", []
                ])
            elif pin.pin_type == "ground" and pin.name.upper() == "GND":
                connections.append([
                    "board:GND.1", f"{inst.instance_id}:{pin.name}", "black", []
                ])

    return connections
