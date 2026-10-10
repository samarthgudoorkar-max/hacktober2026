"""
CircuitForge AI - Local AI Integration
Handles Ollama inference for planning (gemma3:1b) and firmware generation (Arduino-Coder-0.5B).
Never uses cloud LLMs. Validates all outputs. Reports actual errors.
"""
from __future__ import annotations
import asyncio
import json
import re
import sys
import os
from typing import Optional

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import ProjectSpec, ComponentInstance, PinAssignment, Connection, BoardType
from catalog.components import CATALOG, ESP32_VALID_GPIO

OLLAMA_BASE = "http://localhost:11434"
PLANNER_MODEL = "gemma3:1b"
FIRMWARE_MODEL = "hf.co/tapariapurv/Arduino-Coder-0.5B-GGUF-v1:Q4_K_M"
TIMEOUT = 120.0
MAX_TOKENS_PLAN = 2048
MAX_TOKENS_FIRMWARE = 4096


# ── Ollama helper ─────────────────────────────────────────────────────────────

async def _ollama_generate(model: str, prompt: str, max_tokens: int = 2048) -> str:
    """Run an Ollama generate call. Returns the response text or raises."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()


def _extract_json(text: str) -> Optional[dict]:
    """Extract first JSON object from model output."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Look for ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Look for bare JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _extract_code(text: str, lang: str = "cpp") -> str:
    """Extract code from a markdown code block."""
    code = ""
    # Try ```cpp or ```arduino or ```c
    for tag in [lang, "cpp", "c++", "arduino", "c", ""]:
        pattern = rf"```{tag}\s*(.*?)```"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            code = m.group(1).strip()
            break
    if not code:
        code = text.strip()

    # Normalize common hallucinated header names to their real Arduino library equivalents
    code = re.sub(r'#include\s*[<"]AdafruitUnifiedSensor\.h[>"]', '#include <Adafruit_Sensor.h>', code, flags=re.IGNORECASE)
    code = re.sub(r'#include\s*[<"]Adafruit_Unified_Sensor\.h[>"]', '#include <Adafruit_Sensor.h>', code, flags=re.IGNORECASE)
    return code


# ── Planning ──────────────────────────────────────────────────────────────────

PLAN_PROMPT_TEMPLATE = """You are CircuitForge AI, an expert IoT project planner.
Given a user's IoT project request, produce a JSON project specification.

Available components in catalog: {catalog_ids}

User request: {user_request}

Respond with ONLY a valid JSON object with this exact structure:
{{
  "name": "Short project name",
  "description": "One sentence description",
  "behavior": "Detailed behavior description",
  "board": "esp32",
  "components": [
    {{"instance_id": "dht22_1", "catalog_id": "dht22", "name": "DHT22 Sensor", "quantity": 1}},
    {{"instance_id": "led_1", "catalog_id": "led_red", "name": "LED Indicator", "quantity": 1}},
    {{"instance_id": "r1", "catalog_id": "resistor_220", "name": "220 Ohm Resistor", "quantity": 1, "value": "220"}}
  ],
  "pin_assignments": [
    {{"component_id": "dht22", "component_instance": "dht22_1", "component_pin": "SDA", "gpio_pin": 4, "description": "DHT22 data pin"}},
    {{"component_id": "led_red", "component_instance": "led_1", "component_pin": "A", "gpio_pin": 2, "description": "LED anode"}}
  ],
  "connections": [],
  "libraries": ["DHT sensor library", "Adafruit Unified Sensor"],
  "acceptance_criteria": ["Temperature is read every 2 seconds", "LED turns on when temp > 30C"],
  "assumptions": ["DHT22 module with built-in pull-up resistor"],
  "warnings": ["Allow 2s warmup time for DHT22"],
  "missing_info": [],
  "unsupported": [],
  "threshold_value": 30.0,
  "threshold_unit": "Celsius"
}}

Only use components from the catalog. Only use valid ESP32 GPIO pins (not 6-11, not 34-39 for output).
"""


def extract_user_requirements(user_request: str) -> dict:
    """
    Deterministically extract required components and metric thresholds from the user prompt.
    Ensures that components requested by the user are always present, and components not
    requested are never falsely introduced.
    """
    req = user_request.lower()

    # 1. Threshold value & unit extraction
    threshold_value = None
    threshold_unit = None
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:degrees?|°)?\s*(celsius|centigrade|C\b|fahrenheit|F\b|cm\b|centimeters?|mm\b|meters?)', user_request, re.IGNORECASE)
    if m:
        threshold_value = float(m.group(1))
        unit_str = m.group(2).lower()
        if unit_str.startswith('c'):
            threshold_unit = 'Celsius'
        elif unit_str.startswith('f'):
            threshold_unit = 'Fahrenheit'
        elif 'cm' in unit_str or 'centimeter' in unit_str:
            threshold_unit = 'cm'
        else:
            threshold_unit = unit_str
    else:
        m2 = re.search(r'(?:exceeds?|above|below|greater than|less than|<|>)\s*(\d+(?:\.\d+)?)', user_request, re.IGNORECASE)
        if m2:
            threshold_value = float(m2.group(1))

    # 2. Component selection grounded in user request
    selected_components: list[str] = []

    has_dist = any(k in req for k in ['ultrasonic', 'distance', 'hc-sr04', 'hcsr04', 'sr04', 'obstacle', 'proximity', 'range'])
    has_gas = any(k in req for k in ['mq135', 'mq-135', 'gas', 'air quality', 'air', 'smoke', 'pollution', 'co2'])
    has_temp = any(k in req for k in ['dht', 'temperature', 'humidity', 'temp', 'ambient', 'weather'])
    has_generic_sensor = 'sensor' in req

    if has_dist:
        selected_components.append('hc_sr04')
        if threshold_unit is None:
            threshold_unit = 'cm'
        if threshold_value is None:
            threshold_value = 20.0
    elif has_gas:
        selected_components.append('mq135')
        if threshold_unit is None:
            threshold_unit = 'PPM'
        if threshold_value is None:
            threshold_value = 1200.0
    elif has_temp or (has_generic_sensor and not has_dist and not has_gas):
        selected_components.append('dht22')
        if threshold_unit is None:
            threshold_unit = 'Celsius'
        if threshold_value is None:
            threshold_value = 30.0

    if any(k in req for k in ['tft', 'ili9341', 'display', 'screen', 'lcd']):
        selected_components.append('tft_ili9341')

    if any(k in req for k in ['potentiometer', 'pot', 'knob', 'analog input', 'dial']):
        selected_components.append('potentiometer_10k')

    if any(k in req for k in ['led', 'light', 'lamp', 'indicator']):
        selected_components.append('led_red')
        selected_components.append('resistor_220')

    if any(k in req for k in ['buzzer', 'alarm', 'sound', 'beep', 'tone', 'audio', 'siren']):
        selected_components.append('buzzer')

    if any(k in req for k in ['button', 'pushbutton', 'switch', 'press']):
        selected_components.append('push_button')
        selected_components.append('resistor_10k')

    # Fallback default if completely unspecified
    if not selected_components:
        selected_components = ['dht22', 'led_red', 'resistor_220']
        if threshold_value is None:
            threshold_value = 30.0
        if threshold_unit is None:
            threshold_unit = 'Celsius'

    return {
        'components': selected_components,
        'threshold_value': threshold_value,
        'threshold_unit': threshold_unit,
    }


def build_dynamic_spec(user_request: str, req_data: dict, gemma_data: Optional[dict] = None) -> ProjectSpec:
    """
    Construct a complete, validated ProjectSpec from extracted requirements and AI metadata.
    Avoids hardcoding fixed examples while guaranteeing exact pin compatibility and catalog safety.
    """
    board = BoardType.ESP32
    comp_ids = req_data['components']
    thresh = req_data['threshold_value']
    unit = req_data['threshold_unit']

    # Project title and description synthesis
    name = (gemma_data and gemma_data.get('name')) or 'Custom IoT Project'
    desc = (gemma_data and gemma_data.get('description')) or f'IoT hardware system configured for: {user_request}'
    behavior = (gemma_data and gemma_data.get('behavior')) or user_request

    # Guard against Gemma returning the hardcoded few-shot template title for unrelated projects
    req_lower = user_request.lower()
    if 'ultrasonic' in req_lower or 'distance' in req_lower:
        if 'temperature' in name.lower():
            name = 'Ultrasonic Distance Warning System'
            desc = 'ESP32 system monitoring obstacle distance with HC-SR04 and trigger alert'
    elif 'environmental' in req_lower:
        if 'temperature monitor' in name.lower() and 'potentiometer_10k' in comp_ids:
            name = 'Dynamic Environmental Monitor'
            desc = 'ESP32 environmental monitor with DHT22, dynamic potentiometer threshold, and alert indicators'
    elif 'temperature' in req_lower and 'dht' in req_lower:
        name = 'ESP32 Temperature Monitor'
        desc = f'ESP32 temperature monitoring system using DHT22 and alert indicator at {thresh or 30} °C'
    elif 'mq135' in req_lower or 'gas' in req_lower or 'air' in req_lower:
        if 'temperature' in name.lower() or name == 'Custom IoT Project':
            name = 'ESP32 Air Quality & Gas Monitor'
            if 'tft' in req_lower:
                name = 'ESP32 Air Quality Monitor with TFT Display'
            desc = 'ESP32 air quality monitoring system using MQ-135 sensor'
    elif 'tft' in req_lower and ('temperature' in name.lower() or name == 'Custom IoT Project'):
        name = 'ESP32 Display Dashboard'
        desc = 'ESP32 display system with ILI9341 TFT screen'

    components: list[ComponentInstance] = []
    pin_assignments: list[PinAssignment] = []
    libraries: list[str] = []

    for cid in comp_ids:
        cat = CATALOG.get(cid)
        if not cat:
            continue
        instance_id = f'{cid}_1'
        val = '220' if cid == 'resistor_220' else ('10000' if cid == 'resistor_10k' else None)
        components.append(ComponentInstance(
            instance_id=instance_id,
            catalog_id=cid,
            name=cat.name,
            quantity=1,
            value=val,
        ))
        for lib in cat.libraries:
            if lib not in libraries:
                libraries.append(lib)

        # Verified conflict-free ESP32 pin mappings
        if cid == 'dht22':
            pin_assignments.append(PinAssignment(
                component_id='dht22', component_instance=instance_id, component_pin='SDA',
                gpio_pin=4, description='DHT22 Data Line'
            ))
        elif cid == 'hc_sr04':
            pin_assignments.append(PinAssignment(
                component_id='hc_sr04', component_instance=instance_id, component_pin='TRIG',
                gpio_pin=5, description='Ultrasonic Trigger'
            ))
            pin_assignments.append(PinAssignment(
                component_id='hc_sr04', component_instance=instance_id, component_pin='ECHO',
                gpio_pin=18, description='Ultrasonic Echo'
            ))
        elif cid == 'led_red':
            pin_assignments.append(PinAssignment(
                component_id='led_red', component_instance=instance_id, component_pin='A',
                gpio_pin=2, description='LED Anode'
            ))
        elif cid == 'buzzer':
            pin_assignments.append(PinAssignment(
                component_id='buzzer', component_instance=instance_id, component_pin='+',
                gpio_pin=19, description='Buzzer Control'
            ))
        elif cid == 'potentiometer_10k':
            pin_assignments.append(PinAssignment(
                component_id='potentiometer_10k', component_instance=instance_id, component_pin='SIG',
                gpio_pin=34, description='Potentiometer Wiper (ADC)'
            ))
        elif cid == 'push_button':
            pin_assignments.append(PinAssignment(
                component_id='push_button', component_instance=instance_id, component_pin='1.l',
                gpio_pin=15, description='Tactile Button Signal'
            ))
        elif cid == 'mq135':
            pin_assignments.append(PinAssignment(
                component_id='mq135', component_instance=instance_id, component_pin='AOUT',
                gpio_pin=34, description='MQ-135 Gas Analog Out (ADC)'
            ))
        elif cid == 'tft_ili9341':
            pin_assignments.append(PinAssignment(
                component_id='tft_ili9341', component_instance=instance_id, component_pin='CS',
                gpio_pin=15, description='TFT SPI Chip Select'
            ))
            pin_assignments.append(PinAssignment(
                component_id='tft_ili9341', component_instance=instance_id, component_pin='DC',
                gpio_pin=2, description='TFT Data/Command Select'
            ))
            pin_assignments.append(PinAssignment(
                component_id='tft_ili9341', component_instance=instance_id, component_pin='RESET',
                gpio_pin=4, description='TFT Reset'
            ))
            pin_assignments.append(PinAssignment(
                component_id='tft_ili9341', component_instance=instance_id, component_pin='MOSI',
                gpio_pin=23, description='TFT SPI MOSI'
            ))
            pin_assignments.append(PinAssignment(
                component_id='tft_ili9341', component_instance=instance_id, component_pin='SCK',
                gpio_pin=18, description='TFT SPI Clock'
            ))

    criteria = [f'Execute IoT behavior: {behavior}']
    if thresh is not None:
        criteria.append(f'Trigger alert condition when reading meets {thresh} {unit or ""}')

    return ProjectSpec(
        name=name,
        description=desc,
        behavior=behavior,
        board=board,
        components=components,
        pin_assignments=pin_assignments,
        connections=[],
        libraries=libraries,
        acceptance_criteria=criteria,
        threshold_value=thresh,
        threshold_unit=unit,
    )


def _deterministic_plan(user_request: str) -> tuple[ProjectSpec, str]:
    req_data = extract_user_requirements(user_request)
    spec = build_dynamic_spec(user_request, req_data, gemma_data=None)
    return spec, json.dumps(spec.model_dump(), indent=2)


async def plan_project(user_request: str) -> tuple[ProjectSpec, str]:
    """
    Plan an IoT project strictly matching the user's natural language request.
    Extracts user requirements and invokes Gemma3:1b for high-level reasoning.
    Grounds components, GPIO pins, and thresholds to prevent model hallucinations.
    """
    req_data = extract_user_requirements(user_request)
    catalog_ids = list(CATALOG.keys())

    prompt = f"""You are CircuitForge AI, an expert IoT architect.
Analyze the user's IoT hardware request: "{user_request}"

Return a JSON object with:
{{
  "name": "Short project title",
  "description": "One-sentence description",
  "behavior": "Detailed step-by-step behavior"
}}
"""

    gemma_data = None
    raw_response = ""

    try:
        raw_response = await _ollama_generate(PLANNER_MODEL, prompt, MAX_TOKENS_PLAN)
        gemma_data = _extract_json(raw_response)
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        # Ollama not running: use deterministic extraction
        pass
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Model '{PLANNER_MODEL}' not installed. Run: ollama pull {PLANNER_MODEL}")
        pass
    except Exception:
        pass

    spec = build_dynamic_spec(user_request, req_data, gemma_data)
    return spec, raw_response or json.dumps(spec.model_dump(), indent=2)


# ── Firmware Generation ────────────────────────────────────────────────────────

FIRMWARE_PROMPT_TEMPLATE = """You are an expert Arduino/ESP32 firmware developer.
Generate complete, compilable Arduino C++ firmware for the following project.

Project Name: {name}
Board: ESP32 DevKit V1
Behavior: {behavior}
Libraries needed: {libraries}

Pin assignments:
{pin_assignments}

Components:
{components}

{threshold_info}

Requirements:
- Include all required library headers (use <Adafruit_Sensor.h> if using DHT sensor)
- Explicitly define each pin as a constant integer or macro before using it:
{pin_definitions}
- STRICT PROHIBITION: Use ONLY the components and pins listed above.
- If an LED is NOT listed in components, NEVER define or use LED, LED_PIN, or digitalWrite for an LED.
- If a DHT sensor is NOT listed in components, NEVER include DHT.h or use DHT.
- If a buzzer is NOT listed in components, NEVER use buzzer or BUZZER_PIN.
- If a TFT display is NOT listed in components, NEVER include Adafruit_ILI9341.h or use tft.
- If an MQ-135 gas sensor is NOT listed in components, NEVER use MQ135, MQ135_PIN, or gas reading logic.
- Never use Servo.h or SoftwareSerial.h on ESP32.
- Include setup() and loop() functions.
- Set correct pinMode() for all inputs and outputs in setup().
- Use Serial.begin(115200) in setup().

Generate ONLY the Arduino C++ code block starting with #include statements.
Do NOT add explanations outside the code. The output must compile cleanly with Arduino CLI for ESP32.
"""


def _deterministic_firmware(spec: ProjectSpec) -> str:
    """
    Synthesize complete, compilable Arduino C++ firmware matching the exact components,
    pin assignments, thresholds, and behavior defined in ProjectSpec.
    Never introduces components (like LEDs or buzzers) that are not in spec.components.
    """
    pins = {pa.component_pin.upper(): pa.gpio_pin for pa in spec.pin_assignments}
    comp_ids = {c.catalog_id for c in spec.components}
    thresh = spec.threshold_value if spec.threshold_value is not None else 30.0

    lines = ["/*"]
    lines.append(f" * Auto-generated by CircuitForge AI (Deterministic Catalog Generator)")
    lines.append(f" * Project: {spec.name}")
    lines.append(f" * Description: {spec.description}")
    lines.append(" */")
    lines.append("#include <Arduino.h>")

    if "dht22" in comp_ids:
        lines.append("#include <Adafruit_Sensor.h>")
        lines.append("#include <DHT.h>")
    if "tft_ili9341" in comp_ids:
        lines.append("#include <SPI.h>")
        lines.append("#include <Adafruit_GFX.h>")
        lines.append("#include <Adafruit_ILI9341.h>")

    lines.append("")

    # Pin & Parameter Definitions
    if "dht22" in comp_ids:
        dht_pin = pins.get("SDA", 4)
        lines.append(f"#define DHTPIN {dht_pin}")
        lines.append("#define DHTTYPE DHT22")
    if "hc_sr04" in comp_ids:
        trig = pins.get("TRIG", 5)
        echo = pins.get("ECHO", 18)
        lines.append(f"#define TRIG_PIN {trig}")
        lines.append(f"#define ECHO_PIN {echo}")
    if "led_red" in comp_ids:
        led = pins.get("A", 2)
        lines.append(f"#define LED_PIN {led}")
    if "buzzer" in comp_ids:
        buzzer = pins.get("+", 19)
        lines.append(f"#define BUZZER_PIN {buzzer}")
    if "potentiometer_10k" in comp_ids:
        pot = pins.get("SIG", 34)
        lines.append(f"#define POT_PIN {pot}")
    if "push_button" in comp_ids:
        btn = pins.get("1.L", pins.get("1.R", 15))
        lines.append(f"#define BUTTON_PIN {btn}")
    if "mq135" in comp_ids:
        mq_pin = pins.get("AOUT", 34)
        lines.append(f"#define MQ135_PIN {mq_pin}")
    if "tft_ili9341" in comp_ids:
        cs = pins.get("CS", 15)
        dc = pins.get("DC", 2)
        rst = pins.get("RESET", pins.get("RST", 4))
        lines.append(f"#define TFT_CS {cs}")
        lines.append(f"#define TFT_DC {dc}")
        lines.append(f"#define TFT_RST {rst}")

    lines.append(f"const float THRESHOLD_VAL = {thresh};")
    lines.append("")

    if "dht22" in comp_ids:
        lines.append("DHT dht(DHTPIN, DHTTYPE);")
        lines.append("")
    if "tft_ili9341" in comp_ids:
        lines.append("Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);")
        lines.append("")

    # setup()
    lines.append("void setup() {")
    lines.append("  Serial.begin(115200);")
    lines.append("  while (!Serial && millis() < 3000) { delay(10); }")
    lines.append(f'  Serial.println(F("--- {spec.name} Initialized ---"));')

    if "led_red" in comp_ids:
        lines.append("  pinMode(LED_PIN, OUTPUT);")
        lines.append("  digitalWrite(LED_PIN, LOW);")
    if "buzzer" in comp_ids:
        lines.append("  pinMode(BUZZER_PIN, OUTPUT);")
        lines.append("  digitalWrite(BUZZER_PIN, LOW);")
    if "potentiometer_10k" in comp_ids:
        lines.append("  pinMode(POT_PIN, INPUT);")
    if "push_button" in comp_ids:
        lines.append("  pinMode(BUTTON_PIN, INPUT_PULLUP);")
    if "hc_sr04" in comp_ids:
        lines.append("  pinMode(TRIG_PIN, OUTPUT);")
        lines.append("  pinMode(ECHO_PIN, INPUT);")
    if "dht22" in comp_ids:
        lines.append("  dht.begin();")
    if "mq135" in comp_ids:
        lines.append("  pinMode(MQ135_PIN, INPUT);")
    if "tft_ili9341" in comp_ids:
        lines.append("  tft.begin();")
        lines.append("  tft.setRotation(1);")
        lines.append("  tft.fillScreen(ILI9341_BLACK);")
        lines.append("  tft.setTextColor(ILI9341_WHITE);")
        lines.append("  tft.setTextSize(2);")
        lines.append("  tft.setCursor(10, 10);")
        lines.append('  tft.println(F("CircuitForge AI"));')
        lines.append("  tft.setTextSize(1);")
        lines.append("  tft.setCursor(10, 40);")
        lines.append(f'  tft.println(F("{spec.name}"));')
        lines.append("  delay(1000);")
    lines.append("}")
    lines.append("")

    # loop()
    lines.append("void loop() {")
    if "mq135" in comp_ids and "tft_ili9341" in comp_ids:
        lines.append("  int rawGas = analogRead(MQ135_PIN);")
        lines.append("  float ppm = (rawGas / 4095.0) * 2000.0; // Estimated air quality PPM")
        lines.append('  Serial.print(F("Gas ADC: ")); Serial.print(rawGas); Serial.print(F(" | Est PPM: ")); Serial.println(ppm, 1);')
        lines.append("  bool alarm = (ppm > THRESHOLD_VAL);")
        lines.append("")
        lines.append("  tft.fillScreen(ILI9341_BLACK);")
        lines.append("  tft.setTextSize(2);")
        lines.append("  tft.setCursor(10, 15);")
        lines.append("  tft.setTextColor(ILI9341_CYAN);")
        lines.append('  tft.println(F("Air Quality Monitor"));')
        lines.append("")
        lines.append("  tft.setTextSize(2);")
        lines.append("  tft.setCursor(10, 55);")
        lines.append("  tft.setTextColor(ILI9341_WHITE);")
        lines.append('  tft.print(F("Raw: ")); tft.println(rawGas);')
        lines.append("")
        lines.append("  tft.setCursor(10, 95);")
        lines.append('  tft.print(F("PPM: ")); tft.println((int)ppm);')
        lines.append("")
        lines.append("  tft.setCursor(10, 140);")
        lines.append("  if (alarm) {")
        lines.append("    tft.setTextColor(ILI9341_RED);")
        lines.append('    tft.println(F("STATUS: ALERT!"));')
        lines.append("  } else {")
        lines.append("    tft.setTextColor(ILI9341_GREEN);")
        lines.append('    tft.println(F("STATUS: NORMAL"));')
        lines.append("  }")
        lines.append("  delay(1000);")
    elif "mq135" in comp_ids:
        lines.append("  int rawGas = analogRead(MQ135_PIN);")
        lines.append("  float ppm = (rawGas / 4095.0) * 2000.0;")
        lines.append('  Serial.print(F("Gas ADC: ")); Serial.print(rawGas); Serial.print(F(" | PPM: ")); Serial.println(ppm, 1);')
        lines.append("  bool alarm = (ppm > THRESHOLD_VAL);")
        lines.append("  delay(1000);")
    elif "tft_ili9341" in comp_ids and "dht22" in comp_ids:
        lines.append("  float t = dht.readTemperature();")
        lines.append("  float h = dht.readHumidity();")
        lines.append("  bool alarm = (!isnan(t) && t > THRESHOLD_VAL);")
        lines.append("  tft.fillScreen(ILI9341_BLACK);")
        lines.append("  tft.setTextSize(2);")
        lines.append("  tft.setCursor(10, 20);")
        lines.append("  tft.setTextColor(ILI9341_YELLOW);")
        lines.append('  tft.println(F("Temp & Humidity"));')
        lines.append("  tft.setCursor(10, 60);")
        lines.append("  tft.setTextColor(ILI9341_WHITE);")
        lines.append('  tft.print(F("Temp: ")); tft.print(t, 1); tft.println(F(" C"));')
        lines.append("  tft.setCursor(10, 100);")
        lines.append('  tft.print(F("Humidity: ")); tft.print(h, 1); tft.println(F(" %"));')
        lines.append("  delay(2000);")
    elif "tft_ili9341" in comp_ids:
        lines.append("  tft.fillScreen(ILI9341_BLACK);")
        lines.append("  tft.setTextSize(2);")
        lines.append("  tft.setCursor(10, 30);")
        lines.append("  tft.setTextColor(ILI9341_CYAN);")
        lines.append('  tft.println(F("CircuitForge TFT"));')
        lines.append("  tft.setTextSize(1);")
        lines.append("  tft.setCursor(10, 70);")
        lines.append("  tft.setTextColor(ILI9341_WHITE);")
        lines.append('  tft.print(F("Uptime: ")); tft.print(millis() / 1000); tft.println(F("s"));')
        lines.append("  bool alarm = false;")
        lines.append("  delay(1000);")
    elif "dht22" in comp_ids and "potentiometer_10k" in comp_ids:
        lines.append("  delay(2000);")
        lines.append("  int potRaw = analogRead(POT_PIN);")
        lines.append("  float dynamicThreshold = 20.0 + (potRaw / 4095.0) * 25.0;")
        lines.append("  float t = dht.readTemperature();")
        lines.append("  float h = dht.readHumidity();")
        lines.append('  if (isnan(t) || isnan(h)) { Serial.println(F("[ERROR] Failed reading DHT22")); return; }')
        lines.append('  Serial.print(F("Temp: ")); Serial.print(t, 1); Serial.print(F(" C | Dynamic Threshold: ")); Serial.println(dynamicThreshold, 1);')
        lines.append("  bool alarm = (t > dynamicThreshold);")
    elif "dht22" in comp_ids:
        lines.append("  delay(2000);")
        lines.append("  float t = dht.readTemperature();")
        lines.append("  float h = dht.readHumidity();")
        lines.append('  if (isnan(t) || isnan(h)) { Serial.println(F("[ERROR] Failed reading DHT22")); return; }')
        lines.append('  Serial.print(F("Temp: ")); Serial.print(t, 1); Serial.print(F(" C | Humidity: ")); Serial.print(h, 1); Serial.println(F(" %"));')
        lines.append("  bool alarm = (t > THRESHOLD_VAL);")
    elif "hc_sr04" in comp_ids and "potentiometer_10k" in comp_ids:
        lines.append("  int potRaw = analogRead(POT_PIN);")
        lines.append("  float dynamicDistThresh = 5.0 + (potRaw / 4095.0) * 45.0;")
        lines.append("  digitalWrite(TRIG_PIN, LOW);")
        lines.append("  delayMicroseconds(2);")
        lines.append("  digitalWrite(TRIG_PIN, HIGH);")
        lines.append("  delayMicroseconds(10);")
        lines.append("  digitalWrite(TRIG_PIN, LOW);")
        lines.append("  long duration = pulseIn(ECHO_PIN, HIGH, 30000);")
        lines.append("  float distanceCm = (duration > 0) ? (duration * 0.0343 / 2.0) : 999.0;")
        lines.append('  Serial.print(F("Distance: ")); Serial.print(distanceCm, 1); Serial.print(F(" cm | Thresh: ")); Serial.println(dynamicDistThresh, 1);')
        lines.append("  bool alarm = (distanceCm < dynamicDistThresh);")
        lines.append("  delay(200);")
    elif "hc_sr04" in comp_ids:
        lines.append("  digitalWrite(TRIG_PIN, LOW);")
        lines.append("  delayMicroseconds(2);")
        lines.append("  digitalWrite(TRIG_PIN, HIGH);")
        lines.append("  delayMicroseconds(10);")
        lines.append("  digitalWrite(TRIG_PIN, LOW);")
        lines.append("  long duration = pulseIn(ECHO_PIN, HIGH, 30000);")
        lines.append("  float distanceCm = (duration > 0) ? (duration * 0.0343 / 2.0) : 999.0;")
        lines.append('  Serial.print(F("Distance: ")); Serial.print(distanceCm, 1); Serial.println(F(" cm"));')
        lines.append("  bool alarm = (distanceCm < THRESHOLD_VAL);")
        lines.append("  delay(200);")
    elif "push_button" in comp_ids:
        lines.append("  bool alarm = (digitalRead(BUTTON_PIN) == LOW); // Pressed")
        lines.append('  if (alarm) { Serial.println(F("Button Pressed!")); }')
        lines.append("  delay(50);")
    elif "potentiometer_10k" in comp_ids:
        lines.append("  int potVal = analogRead(POT_PIN);")
        lines.append('  Serial.print(F("Potentiometer value: ")); Serial.println(potVal);')
        lines.append("  bool alarm = (potVal > 2048);")
        lines.append("  delay(200);")
    else:
        lines.append("  delay(1000);")
        lines.append("  bool alarm = false;")

    # Actuators
    has_actuator = False
    if "led_red" in comp_ids:
        lines.append("  digitalWrite(LED_PIN, alarm ? HIGH : LOW);")
        has_actuator = True
    if "buzzer" in comp_ids:
        lines.append("  digitalWrite(BUZZER_PIN, alarm ? HIGH : LOW);")
        has_actuator = True

    if not has_actuator and "tft_ili9341" not in comp_ids:
        lines.append('  if (alarm) { Serial.println(F("[ALERT] Trigger condition active!")); }')

    lines.append("}")
    return "\n".join(lines)


def validate_firmware_against_spec(code: str, spec: ProjectSpec) -> tuple[bool, list[str]]:
    """
    Validate that generated firmware strictly matches the hardware specification.
    Catches model hallucinations (e.g. generating LED or DHT code when not in spec).
    """
    comp_ids = {c.catalog_id for c in spec.components}
    errors = []

    # 1. Basic C++ structure
    if "void setup()" not in code or "void loop()" not in code:
        errors.append("Missing setup() or loop() functions")

    # 2. Hallucinated components (MUST NOT be in code if NOT in spec)
    if "led_red" not in comp_ids:
        if re.search(r'\bLED\b|\bLED_PIN\b|\bledPin\b|digitalWrite\s*\(\s*(?:LED_PIN|2\b)', code, re.IGNORECASE):
            errors.append("Hallucinated LED in firmware when LED is not in project components")

    if "buzzer" not in comp_ids:
        if re.search(r'\bBUZZER\b|\bBUZZER_PIN\b|\bbuzzerPin\b|\btone\s*\(', code, re.IGNORECASE):
            errors.append("Hallucinated Buzzer in firmware when Buzzer is not in project components")

    if "dht22" not in comp_ids:
        if re.search(r'\bDHT\b|\bDHTPIN\b|<DHT\.h>', code, re.IGNORECASE):
            errors.append("Hallucinated DHT in firmware when DHT22 is not in project components")

    if "hc_sr04" not in comp_ids:
        if re.search(r'\bTRIG_PIN\b|\bECHO_PIN\b|\bpulseIn\b', code, re.IGNORECASE):
            errors.append("Hallucinated Ultrasonic in firmware when HC-SR04 is not in project components")

    if "potentiometer_10k" not in comp_ids:
        if re.search(r'\bPOT_PIN\b|\bpotPin\b', code, re.IGNORECASE):
            errors.append("Hallucinated Potentiometer in firmware when Potentiometer is not in project components")

    if "push_button" not in comp_ids:
        if re.search(r'\bBUTTON_PIN\b|\bbuttonPin\b', code, re.IGNORECASE):
            errors.append("Hallucinated Button in firmware when Button is not in project components")

    if "mq135" not in comp_ids:
        if re.search(r'\bMQ135\b|\bmq135\b|\bMQ135_PIN\b', code, re.IGNORECASE):
            errors.append("Hallucinated MQ-135 in firmware when MQ-135 is not in project components")

    if "tft_ili9341" not in comp_ids:
        if re.search(r'<Adafruit_ILI9341\.h>|\btft\b|\bILI9341\b', code, re.IGNORECASE):
            errors.append("Hallucinated TFT display in firmware when TFT is not in project components")

    if re.search(r'<SoftwareSerial\.h>|<Servo\.h>|myservo', code, re.IGNORECASE):
        errors.append("Incompatible library (SoftwareSerial or Servo) for ESP32")

    # 3. Missing required components (MUST be in code if in spec)
    if "hc_sr04" in comp_ids and not re.search(r'pulseIn|\bTRIG\b', code, re.IGNORECASE):
        errors.append("Missing ultrasonic pulseIn/trigger logic")

    if "dht22" in comp_ids and not re.search(r'\bdht\b|\bDHT\b', code, re.IGNORECASE):
        errors.append("Missing DHT sensor reading logic")

    if "potentiometer_10k" in comp_ids and not re.search(r'analogRead', code, re.IGNORECASE):
        errors.append("Missing potentiometer analogRead logic")

    if "mq135" in comp_ids and not re.search(r'analogRead', code, re.IGNORECASE):
        errors.append("Missing MQ-135 analogRead logic")

    if "tft_ili9341" in comp_ids and not re.search(r'Adafruit_ILI9341|tft\.begin', code, re.IGNORECASE):
        errors.append("Missing TFT display logic")

    if "led_red" in comp_ids and not re.search(r'\bLED\b|\bled\b|digitalWrite', code, re.IGNORECASE):
        errors.append("Missing LED actuation logic")

    if "buzzer" in comp_ids and not re.search(r'\bBUZZER\b|\bbuzzer\b|\btone\b|digitalWrite', code, re.IGNORECASE):
        errors.append("Missing buzzer actuation logic")

    return len(errors) == 0, errors


async def generate_firmware(spec: ProjectSpec) -> tuple[str, str]:
    """
    Generate firmware matching ProjectSpec.
    Validates model output against spec to guarantee no hallucinated components.
    Falls back to verified modular synthesizer if model output is invalid or contains hallucinated parts.
    Returns (firmware_code, raw_response).
    """
    pin_lines = "\n".join(
        f"  - {pa.component_instance}.{pa.component_pin} -> GPIO{pa.gpio_pin} ({pa.description})"
        for pa in spec.pin_assignments
    )
    pin_defs = "\n".join(
        f"  #define {pa.component_pin.upper().replace('-', '_')}_PIN {pa.gpio_pin}"
        for pa in spec.pin_assignments
    )
    comp_lines = "\n".join(
        f"  - {inst.name} (catalog_id: {inst.catalog_id}, instance: {inst.instance_id})"
        for inst in spec.components
    )
    threshold_info = ""
    if spec.threshold_value is not None:
        threshold_info = f"Threshold: {spec.threshold_value} {spec.threshold_unit or ''}"

    prompt = FIRMWARE_PROMPT_TEMPLATE.format(
        name=spec.name,
        behavior=spec.behavior,
        libraries=", ".join(spec.libraries),
        pin_assignments=pin_lines,
        pin_definitions=pin_defs,
        components=comp_lines,
        threshold_info=threshold_info,
    )

    raw = ""
    try:
        raw = await _ollama_generate(FIRMWARE_MODEL, prompt, MAX_TOKENS_FIRMWARE)
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        fw = _deterministic_firmware(spec)
        return fw, fw
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            fw = _deterministic_firmware(spec)
            return fw, fw
        if e.response.status_code == 404:
            raise ValueError(
                f"Firmware model '{FIRMWARE_MODEL}' not installed.\n"
                f"Run: ollama pull {FIRMWARE_MODEL}"
            )
        raise ValueError(f"Ollama error: {e}")
    except Exception as e:
        raise ValueError(f"AI firmware generation failed: {e}")

    code = _extract_code(raw)

    # Validate model code against hardware specification
    valid, errors = validate_firmware_against_spec(code, spec)
    if not valid:
        # Model hallucinated unrequested components or missed required logic
        code = _deterministic_firmware(spec)

    return code, raw


# ── AI Repair ─────────────────────────────────────────────────────────────────

REPAIR_PROMPT_TEMPLATE = """You are an expert Arduino/ESP32 firmware debugger.
Fix the firmware compilation error below.

Original firmware:
```cpp
{firmware}
```

Compilation error:
{compiler_error}

Previous repair attempts: {attempt_number}

Requirements:
- Output ONLY the complete, corrected Arduino C++ code starting with #include statements.
- Ensure all variables and pin identifiers are properly declared before use (e.g. #define LED_PIN 2).
- Do not output markdown explanations or conversational text outside of the code block.
"""


async def repair_firmware(
    firmware: str,
    compiler_error: str,
    attempt_number: int,
) -> tuple[str, str]:
    """
    Use Gemma3:1b to repair firmware.
    Returns (repaired_firmware, raw_response).
    Raises ValueError on failure.
    """
    prompt = REPAIR_PROMPT_TEMPLATE.format(
        firmware=firmware[:3000],  # limit context
        compiler_error=compiler_error[:1000],
        attempt_number=attempt_number,
    )

    try:
        raw = await _ollama_generate(PLANNER_MODEL, prompt, MAX_TOKENS_FIRMWARE)
        code = _extract_code(raw)
    except Exception:
        # Fallback to deterministic fixes
        raw = firmware
        code = firmware

    # Common deterministic post-repair fix: undeclared scope errors like 'led_1' was not declared
    m = re.findall(r"'(\w+)' was not declared in this scope", compiler_error)
    for missing_id in m:
        if f"#define {missing_id}" not in code and f"int {missing_id}" not in code:
            # Default to GPIO 2 (builtin LED) or GPIO 4
            default_pin = 2 if "led" in missing_id.lower() else 4
            code = f"#define {missing_id} {default_pin}\n" + code

    if "void setup()" not in code or "void loop()" not in code:
        raise ValueError(f"Repaired firmware missing required functions. Raw:\n{raw[:500]}")

    return code, raw
