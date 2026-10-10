"""
CircuitForge AI — Diversity Regression Test Suite
Validates that different natural-language requests produce genuinely distinct,
request-specific hardware specifications, circuit diagrams, and firmware code.

Tests:
- Request A: Temperature alert (ESP32 + DHT22 + LED, >30°C)
- Request B: Distance warning (ESP32 + HC-SR04 + Buzzer, <20 cm)
- Request C: Adjustable environmental monitor (ESP32 + DHT22 + Potentiometer + LED + Buzzer)
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from schemas import ProjectStatus, BoardType
from storage.db import init_db, create_project, get_project, export_project_zip
from catalog.diagram_generator import generate_diagram
from catalog.bom_generator import generate_bom
from validators.project_validator import (
    validate_project_spec, validate_diagram, validate_firmware_pins, validate_zip_contents
)
from ai.ollama_client import plan_project, generate_firmware
from simulator.arduino_compiler import compile_firmware, arduino_cli_available


@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_diversity_pipeline_requests():
    """
    Execute generation for Request A, B, and C and verify they produce
    strictly distinct, request-specific outputs across all pipeline stages.
    """
    req_a = "Build an ESP32 temperature monitoring system using a DHT22 and an LED that turns on when temperature exceeds 30°C."
    req_b = "Build an ultrasonic distance warning system using an HC-SR04 and a buzzer that activates when distance is below 20 cm."
    req_c = "Build an environmental monitoring system with a DHT22, potentiometer, red LED, and buzzer where the potentiometer adjusts the alert threshold."

    # ── 1. Plan specs ─────────────────────────────────────────────────────────
    spec_a, _ = await plan_project(req_a)
    spec_b, _ = await plan_project(req_b)
    spec_c, _ = await plan_project(req_c)

    # Validate structural specs
    assert validate_project_spec(spec_a).valid, "Spec A validation failed"
    assert validate_project_spec(spec_b).valid, "Spec B validation failed"
    assert validate_project_spec(spec_c).valid, "Spec C validation failed"

    catalog_ids_a = {c.catalog_id for c in spec_a.components}
    catalog_ids_b = {c.catalog_id for c in spec_b.components}
    catalog_ids_c = {c.catalog_id for c in spec_c.components}

    # Verify Request A components
    assert "dht22" in catalog_ids_a, "Request A must contain DHT22"
    assert "led_red" in catalog_ids_a, "Request A must contain LED"
    assert "hc_sr04" not in catalog_ids_a, "Request A must not contain HC-SR04"
    assert "buzzer" not in catalog_ids_a, "Request A must not contain buzzer"

    # Verify Request B components
    assert "hc_sr04" in catalog_ids_b, "Request B must contain HC-SR04"
    assert "buzzer" in catalog_ids_b, "Request B must contain buzzer"
    assert "dht22" not in catalog_ids_b, "Request B must not contain DHT22"
    assert "potentiometer_10k" not in catalog_ids_b, "Request B must not contain potentiometer"

    # Verify Request C components
    assert "dht22" in catalog_ids_c, "Request C must contain DHT22"
    assert "potentiometer_10k" in catalog_ids_c, "Request C must contain potentiometer"
    assert "led_red" in catalog_ids_c, "Request C must contain LED"
    assert "buzzer" in catalog_ids_c, "Request C must contain buzzer"

    # Assert distinct component sets
    assert catalog_ids_a != catalog_ids_b, "Request A and B component sets must differ"
    assert catalog_ids_b != catalog_ids_c, "Request B and C component sets must differ"
    assert catalog_ids_a != catalog_ids_c, "Request A and C component sets must differ"

    # ── 2. Diagrams ───────────────────────────────────────────────────────────
    diag_a = generate_diagram(spec_a)
    diag_b = generate_diagram(spec_b)
    diag_c = generate_diagram(spec_c)

    assert validate_diagram(diag_a).valid, "Diagram A validation failed"
    assert validate_diagram(diag_b).valid, "Diagram B validation failed"
    assert validate_diagram(diag_c).valid, "Diagram C validation failed"

    parts_a = {p["type"] for p in diag_a["parts"]}
    parts_b = {p["type"] for p in diag_b["parts"]}
    parts_c = {p["type"] for p in diag_c["parts"]}

    assert "wokwi-dht22" in parts_a and "wokwi-hc-sr04" not in parts_a
    assert "wokwi-hc-sr04" in parts_b and "wokwi-dht22" not in parts_b
    assert "wokwi-potentiometer" in parts_c and "wokwi-buzzer" in parts_c

    assert parts_a != parts_b, "Diagram parts A and B must differ"
    assert parts_b != parts_c, "Diagram parts B and C must differ"
    assert parts_a != parts_c, "Diagram parts A and C must differ"

    # ── 3. Firmware Generation & Pin Validation ──────────────────────────────
    fw_a, _ = await generate_firmware(spec_a)
    fw_b, _ = await generate_firmware(spec_b)
    fw_c, _ = await generate_firmware(spec_c)

    # Firmware A checks
    assert "DHT" in fw_a or "dht" in fw_a, "Firmware A must reference DHT"
    assert "30" in fw_a, "Firmware A must reference threshold 30"
    assert "HCSR04" not in fw_a and "TRIG_PIN" not in fw_a, "Firmware A must not have ultrasonic logic"
    val_pins_a = validate_firmware_pins(fw_a, spec_a)
    assert val_pins_a.valid, f"Firmware A pin check failed: {val_pins_a.errors}"

    # Firmware B checks
    assert ("TRIG" in fw_b or "duration" in fw_b or "pulseIn" in fw_b), "Firmware B must have ultrasonic logic"
    assert "20" in fw_b, "Firmware B must reference threshold 20"
    assert "BUZZER" in fw_b or "buzzer" in fw_b or "tone" in fw_b, "Firmware B must control buzzer"
    assert "DHT" not in fw_b, "Firmware B must not have DHT logic"
    val_pins_b = validate_firmware_pins(fw_b, spec_b)
    assert val_pins_b.valid, f"Firmware B pin check failed: {val_pins_b.errors}"

    # Firmware C checks
    assert ("POT" in fw_c or "analogRead" in fw_c), "Firmware C must read potentiometer"
    assert "DHT" in fw_c, "Firmware C must read DHT"
    assert ("BUZZER" in fw_c or "buzzer" in fw_c), "Firmware C must control buzzer"
    assert ("LED" in fw_c or "led" in fw_c), "Firmware C must control LED"
    val_pins_c = validate_firmware_pins(fw_c, spec_c)
    assert val_pins_c.valid, f"Firmware C pin check failed: {val_pins_c.errors}"

    # Assert distinct firmware content
    assert fw_a != fw_b, "Firmware A and B must differ"
    assert fw_b != fw_c, "Firmware B and C must differ"
    assert fw_a != fw_c, "Firmware A and C must differ"

    # ── 4. Arduino Compilation Verification ───────────────────────────────────
    if arduino_cli_available():
        for name, fw, spec in [("Request A", fw_a, spec_a), ("Request B", fw_b, spec_b), ("Request C", fw_c, spec_c)]:
            with tempfile.TemporaryDirectory() as td:
                p = Path(td)
                (p / "sketch.ino").write_text(fw, encoding="utf-8")
                res = await compile_firmware(p, f"test_{name.replace(' ', '_')}")
                assert res["success"], f"Compilation failed for {name}:\n{res['stderr']}"

    # ── 5. Project Creation and Persistence Isolation ────────────────────────
    proj_a = await create_project(req_a)
    proj_b = await create_project(req_b)
    proj_c = await create_project(req_c)

    assert len({proj_a.id, proj_b.id, proj_c.id}) == 3, "Projects must have unique IDs"
    assert proj_a.user_request != proj_b.user_request != proj_c.user_request, "Requests must be preserved individually"


@pytest.mark.asyncio
async def test_tft_mq135_generation():
    """
    Test the user prompt: 'try tft and mq135 to esp32'.
    Ensures:
    1. Correct components: mq135, tft_ili9341.
    2. Zero hallucinated LED, DHT, buzzer components.
    3. Proper pin assignments for SPI TFT and analog MQ-135.
    4. Compilable Arduino firmware using Adafruit_ILI9341 without LED code.
    5. Clean Wokwi diagram with correct parts and connections.
    """
    req = "try tft and mq135 to esp32"
    spec, _ = await plan_project(req)
    val_spec = validate_project_spec(spec)
    assert val_spec.valid, f"Spec validation failed: {val_spec.errors}"

    comp_ids = {c.catalog_id for c in spec.components}
    assert "mq135" in comp_ids, "Spec must include mq135"
    assert "tft_ili9341" in comp_ids, "Spec must include tft_ili9341"
    assert "led_red" not in comp_ids, "Spec must NOT include led_red"
    assert "dht22" not in comp_ids, "Spec must NOT include dht22"
    assert "buzzer" not in comp_ids, "Spec must NOT include buzzer"

    # Diagram
    diag = generate_diagram(spec)
    val_diag = validate_diagram(diag)
    assert val_diag.valid, f"Diagram validation failed: {val_diag.errors}"
    part_types = {p["type"] for p in diag["parts"]}
    assert "wokwi-gas-sensor" in part_types
    assert "wokwi-ili9341" in part_types

    # Firmware
    fw, _ = await generate_firmware(spec)
    assert "Adafruit_ILI9341" in fw, "Firmware must use Adafruit_ILI9341"
    assert "analogRead" in fw, "Firmware must read analog MQ135"
    assert "LED" not in fw and "led" not in fw, "Firmware must NOT contain any LED code"
    assert "DHT" not in fw, "Firmware must NOT contain DHT code"
    assert "BUZZER" not in fw, "Firmware must NOT contain buzzer code"

    # Compile firmware
    if arduino_cli_available():
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "sketch.ino").write_text(fw, encoding="utf-8")
            res = await compile_firmware(p, "test_tft_mq135")
            assert res["success"], f"Compilation failed for TFT+MQ135:\n{res['stderr']}"

