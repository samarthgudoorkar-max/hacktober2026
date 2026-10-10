"""
CircuitForge AI - Component Catalog
Verified catalog of supported components with pricing, wiring rules, and Wokwi IDs.
All prices in INR are indicative catalog estimates as of 2025-01.
"""
from __future__ import annotations
from typing import Optional
from schemas import CatalogComponent, ComponentPin, WiringRule

# ── ESP32 Development Board ────────────────────────────────────────────────────

ESP32_DEVKIT = CatalogComponent(
    id="esp32_devkitv1",
    name="ESP32 DevKit V1",
    category="microcontroller",
    wokwi_id="wokwi-esp32-devkit-v1",
    supported_boards=["esp32"],
    pins=[
        ComponentPin(name="3V3",   description="3.3V power output",  pin_type="power",   required=True),
        ComponentPin(name="GND",   description="Ground",              pin_type="ground",  required=True),
        ComponentPin(name="VIN",   description="5V input",            pin_type="power",   required=False),
        ComponentPin(name="GPIO2", description="GPIO 2 / LED_BUILTIN",pin_type="digital", required=False),
        ComponentPin(name="GPIO4", description="GPIO 4",              pin_type="digital", required=False),
        ComponentPin(name="GPIO5", description="GPIO 5",              pin_type="digital", required=False),
        ComponentPin(name="GPIO12",description="GPIO 12",             pin_type="digital", required=False),
        ComponentPin(name="GPIO13",description="GPIO 13",             pin_type="digital", required=False),
        ComponentPin(name="GPIO14",description="GPIO 14",             pin_type="digital", required=False),
        ComponentPin(name="GPIO15",description="GPIO 15",             pin_type="digital", required=False),
        ComponentPin(name="GPIO18",description="GPIO 18 / SPI CLK",  pin_type="digital", required=False),
        ComponentPin(name="GPIO19",description="GPIO 19 / SPI MISO", pin_type="digital", required=False),
        ComponentPin(name="GPIO21",description="GPIO 21 / I2C SDA",  pin_type="i2c",     required=False),
        ComponentPin(name="GPIO22",description="GPIO 22 / I2C SCL",  pin_type="i2c",     required=False),
        ComponentPin(name="GPIO23",description="GPIO 23 / SPI MOSI", pin_type="digital", required=False),
        ComponentPin(name="GPIO25",description="GPIO 25 / DAC1",     pin_type="analog",  required=False),
        ComponentPin(name="GPIO26",description="GPIO 26 / DAC2",     pin_type="analog",  required=False),
        ComponentPin(name="GPIO27",description="GPIO 27",             pin_type="digital", required=False),
        ComponentPin(name="GPIO32",description="GPIO 32 / ADC1_CH4", pin_type="analog",  required=False),
        ComponentPin(name="GPIO33",description="GPIO 33 / ADC1_CH5", pin_type="analog",  required=False),
        ComponentPin(name="GPIO34",description="GPIO 34 / input only",pin_type="digital",required=False),
        ComponentPin(name="GPIO35",description="GPIO 35 / input only",pin_type="digital",required=False),
    ],
    unit_price_inr=350.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="ESP32 dual-core 240MHz WiFi+BT development board with 38 pins",
    electrical_constraints=[
        "GPIO6-11 are connected to flash memory — do not use",
        "GPIO34-39 are input-only — cannot be used as output",
        "Max 40mA per GPIO pin, 1200mA total",
        "3.3V logic only — do not apply 5V to GPIO pins",
    ],
)

# ── DHT22 Temperature & Humidity Sensor ────────────────────────────────────────

DHT22 = CatalogComponent(
    id="dht22",
    name="DHT22 Temperature & Humidity Sensor",
    category="sensor",
    wokwi_id="wokwi-dht22",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC",  description="Power supply 3.3V-5V", pin_type="power",   required=True),
        ComponentPin(name="SDA",  description="Data signal",           pin_type="signal",  required=True),
        ComponentPin(name="NC",   description="Not connected",         pin_type="signal",  required=False),
        ComponentPin(name="GND",  description="Ground",                pin_type="ground",  required=True),
    ],
    wiring_rules=[
        WiringRule(from_pin="VCC", to_component="esp32", to_pin="3V3",   description="Connect to 3.3V power"),
        WiringRule(from_pin="GND", to_component="esp32", to_pin="GND",   description="Connect to ground"),
        WiringRule(from_pin="SDA", to_component="esp32", to_pin="GPIO4", description="Data line (default GPIO4)"),
    ],
    libraries=["DHT sensor library", "Adafruit Unified Sensor"],
    unit_price_inr=200.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="AM2302 digital temperature and humidity sensor, 0-100%RH, -40 to 80°C",
    electrical_constraints=[
        "Requires 10kΩ pull-up resistor on data line (built-in on module versions)",
        "Minimum 2 seconds between readings",
        "Operating voltage: 3.3V to 5V",
    ],
    example_firmware="""
#include <DHT.h>
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);
void setup() {
  Serial.begin(115200);
  dht.begin();
}
void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t)) { Serial.println("DHT read failed"); return; }
  Serial.printf("Temp: %.1f°C  Humidity: %.1f%%\\n", t, h);
  delay(2000);
}
""",
)

# ── LED ────────────────────────────────────────────────────────────────────────

LED_RED = CatalogComponent(
    id="led_red",
    name="Red LED",
    category="output",
    wokwi_id="wokwi-led",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="A",  description="Anode (positive)",  pin_type="digital", required=True),
        ComponentPin(name="K",  description="Cathode (negative)", pin_type="ground",  required=True),
    ],
    unit_price_inr=5.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="5mm red LED, Vf≈2.0V, If≈20mA",
    electrical_constraints=[
        "Always use current-limiting resistor (220Ω for 3.3V supply)",
        "Forward voltage: 2.0V typical",
        "Max forward current: 20mA",
    ],
)

# ── Resistor ───────────────────────────────────────────────────────────────────

RESISTOR_220 = CatalogComponent(
    id="resistor_220",
    name="220Ω Resistor",
    category="passive",
    wokwi_id="wokwi-resistor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1", description="Terminal 1", pin_type="signal", required=True),
        ComponentPin(name="2", description="Terminal 2", pin_type="signal", required=True),
    ],
    unit_price_inr=1.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="220Ω 1/4W through-hole resistor for LED current limiting",
    electrical_constraints=["Power rating: 0.25W"],
)

RESISTOR_10K = CatalogComponent(
    id="resistor_10k",
    name="10kΩ Resistor",
    category="passive",
    wokwi_id="wokwi-resistor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1", description="Terminal 1", pin_type="signal", required=True),
        ComponentPin(name="2", description="Terminal 2", pin_type="signal", required=True),
    ],
    unit_price_inr=1.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="10kΩ 1/4W through-hole resistor for pull-up/down",
    electrical_constraints=["Power rating: 0.25W"],
)

# ── HC-SR04 Ultrasonic Sensor ──────────────────────────────────────────────────

HC_SR04 = CatalogComponent(
    id="hc_sr04",
    name="HC-SR04 Ultrasonic Distance Sensor",
    category="sensor",
    wokwi_id="wokwi-hc-sr04",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC",   description="5V power supply",  pin_type="power",  required=True),
        ComponentPin(name="TRIG",  description="Trigger input",     pin_type="signal", required=True),
        ComponentPin(name="ECHO",  description="Echo output",       pin_type="signal", required=True),
        ComponentPin(name="GND",   description="Ground",            pin_type="ground", required=True),
    ],
    libraries=["NewPing"],
    unit_price_inr=60.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Ultrasonic distance sensor, range 2cm-400cm",
    electrical_constraints=[
        "VCC requires 5V — use voltage divider on ECHO pin when using 3.3V MCU",
        "ECHO pin output is 5V — use level shifter or voltage divider for ESP32",
        "Minimum 60ms between measurements to avoid echo interference",
    ],
)

# ── Buzzer ─────────────────────────────────────────────────────────────────────

BUZZER = CatalogComponent(
    id="buzzer",
    name="Active Buzzer",
    category="output",
    wokwi_id="wokwi-buzzer",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="+", description="Positive (signal)",  pin_type="signal", required=True),
        ComponentPin(name="-", description="Negative (ground)",  pin_type="ground", required=True),
    ],
    unit_price_inr=20.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="5V active buzzer, beeps when positive voltage is applied",
    electrical_constraints=[
        "Operating voltage: 3.3V to 5V",
        "Current consumption: ~30mA — may need transistor driver for ESP32 GPIO",
    ],
)

# ── Push Button ────────────────────────────────────────────────────────────────

PUSH_BUTTON = CatalogComponent(
    id="push_button",
    name="Tactile Push Button",
    category="input",
    wokwi_id="wokwi-pushbutton",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1.l", description="Left terminal 1",  pin_type="signal", required=True),
        ComponentPin(name="1.r", description="Right terminal 1", pin_type="signal", required=True),
        ComponentPin(name="2.l", description="Left terminal 2",  pin_type="signal", required=False),
        ComponentPin(name="2.r", description="Right terminal 2", pin_type="signal", required=False),
    ],
    unit_price_inr=5.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="6×6mm tactile momentary push button, rated 50mA 12V",
    electrical_constraints=["Use internal pull-up or external pull-up resistor"],
)

# ── Potentiometer ──────────────────────────────────────────────────────────────

POTENTIOMETER = CatalogComponent(
    id="potentiometer_10k",
    name="10kΩ Potentiometer",
    category="input",
    wokwi_id="wokwi-potentiometer",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="GND", description="Ground terminal", pin_type="ground",  required=True),
        ComponentPin(name="SIG", description="Wiper / signal",  pin_type="analog",  required=True),
        ComponentPin(name="VCC", description="Power terminal",  pin_type="power",   required=True),
    ],
    unit_price_inr=15.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="10kΩ rotary potentiometer for analog input 0-3.3V",
    electrical_constraints=["Max 1W power dissipation", "Use ADC-capable GPIO pin for signal"],
)


# ── MQ-135 Gas & Air Quality Sensor ───────────────────────────────────────────

MQ135 = CatalogComponent(
    id="mq135",
    name="MQ-135 Air Quality & Gas Sensor",
    category="sensor",
    wokwi_id="wokwi-gas-sensor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC",  description="Power terminal 5V/3.3V", pin_type="power",   required=True),
        ComponentPin(name="GND",  description="Ground terminal",       pin_type="ground",  required=True),
        ComponentPin(name="AOUT", description="Analog output (PPM)",   pin_type="analog",  required=True),
        ComponentPin(name="DOUT", description="Digital threshold out", pin_type="digital", required=False),
    ],
    wiring_rules=[
        WiringRule(from_pin="VCC", to_component="esp32", to_pin="3V3", description="Connect to 3.3V power"),
        WiringRule(from_pin="GND", to_component="esp32", to_pin="GND", description="Connect to ground"),
        WiringRule(from_pin="AOUT", to_component="esp32", to_pin="GPIO34", description="Analog signal to ADC1"),
    ],
    libraries=[],
    unit_price_inr=160.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Air quality sensor for detecting ammonia, nitrogen oxides, alcohol, benzene, smoke, and CO2",
    electrical_constraints=["Requires preheating for accurate readings", "Connect AOUT to ADC1 pin (e.g. GPIO34)"],
)

# ── 2.8" SPI TFT Display (ILI9341) ─────────────────────────────────────────────

TFT_ILI9341 = CatalogComponent(
    id="tft_ili9341",
    name="2.8\" SPI TFT LCD Display (ILI9341)",
    category="display",
    wokwi_id="wokwi-ili9341",
    supported_boards=["esp32"],
    pins=[
        ComponentPin(name="VCC",   description="Power supply 3.3V",   pin_type="power",   required=True),
        ComponentPin(name="GND",   description="Ground",              pin_type="ground",  required=True),
        ComponentPin(name="CS",    description="Chip Select (SPI)",   pin_type="digital", required=True),
        ComponentPin(name="RST",   description="Reset line",          pin_type="digital", required=True),
        ComponentPin(name="D/C",   description="Data/Command select", pin_type="digital", required=True),
        ComponentPin(name="MOSI",  description="SPI Data input",      pin_type="digital", required=True),
        ComponentPin(name="SCK",   description="SPI Clock",           pin_type="digital", required=True),
        ComponentPin(name="LED",   description="Backlight 3.3V",      pin_type="power",   required=False),
        ComponentPin(name="MISO",  description="SPI Data output",     pin_type="digital", required=False),
    ],
    wiring_rules=[
        WiringRule(from_pin="VCC", to_component="esp32", to_pin="3V3", description="3.3V power"),
        WiringRule(from_pin="GND", to_component="esp32", to_pin="GND.1", description="Ground"),
        WiringRule(from_pin="CS", to_component="esp32", to_pin="D15", description="SPI Chip Select"),
        WiringRule(from_pin="D/C", to_component="esp32", to_pin="D2", description="SPI Data/Command"),
        WiringRule(from_pin="RST", to_component="esp32", to_pin="D4", description="Display Reset"),
        WiringRule(from_pin="MOSI", to_component="esp32", to_pin="D23", description="SPI MOSI"),
        WiringRule(from_pin="SCK", to_component="esp32", to_pin="D18", description="SPI Clock"),
    ],
    libraries=["Adafruit GFX Library", "Adafruit ILI9341"],
    unit_price_inr=650.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="240x320 RGB color TFT LCD display module with SPI bus",
    electrical_constraints=["3.3V logic level only", "Hardware SPI on GPIO 18/23 recommended"],
)


# ── Photoresistor / Light Sensor (LDR) ─────────────────────────────────────────

PHOTORESISTOR = CatalogComponent(
    id="photoresistor",
    name="Photoresistor (LDR Light Sensor)",
    category="sensor",
    wokwi_id="wokwi-photoresistor-sensor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC", description="3.3V Power", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
        ComponentPin(name="AO",  description="Analog Light Reading (ADC)", pin_type="analog", required=True),
        ComponentPin(name="DO",  description="Digital Threshold Output", pin_type="digital", required=False),
    ],
    unit_price_inr=15.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Light Dependent Resistor module for detecting ambient light levels and illuminance",
    electrical_constraints=["Connect AO to ADC1 pin (e.g. GPIO35)", "Resistance decreases with increased light"],
)

# ── PIR Motion Sensor ─────────────────────────────────────────────────────────

PIR_MOTION = CatalogComponent(
    id="pir_motion",
    name="PIR Motion Sensor (HC-SR501)",
    category="sensor",
    wokwi_id="wokwi-pir-motion-sensor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC", description="Power supply 3.3V-5V", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
        ComponentPin(name="OUT", description="Digital Motion Signal (HIGH on motion)", pin_type="digital", required=True),
    ],
    unit_price_inr=95.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Pyroelectric infrared motion detector for human and intruder presence detection",
    electrical_constraints=["3.3V digital output is directly compatible with ESP32 GPIO"],
)

# ── SG90 Micro Servo Motor ───────────────────────────────────────────────────

SERVO = CatalogComponent(
    id="servo",
    name="SG90 Micro Servo Motor",
    category="actuator",
    wokwi_id="wokwi-servo",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="PWM", description="PWM Control Signal", pin_type="digital", required=True),
        ComponentPin(name="VCC", description="5V Power (VIN)", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
    ],
    libraries=["ESP32Servo"],
    unit_price_inr=120.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="9g micro servo motor with 0 to 180 degree rotation control",
    electrical_constraints=["Requires 5V (VIN) power for adequate torque; ESP32 GPIO13 for PWM signal"],
)

# ── SPDT Slide Switch ─────────────────────────────────────────────────────────

SLIDE_SWITCH = CatalogComponent(
    id="slide_switch",
    name="SPDT Slide Switch",
    category="input",
    wokwi_id="wokwi-slide-switch",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1", description="Terminal 1 (GND)", pin_type="ground", required=False),
        ComponentPin(name="2", description="Common terminal (Signal)", pin_type="digital", required=True),
        ComponentPin(name="3", description="Terminal 2 (VCC / Open)", pin_type="power", required=False),
    ],
    unit_price_inr=8.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Sub-miniature SPDT slide toggle switch for on/off circuit control",
    electrical_constraints=["Use internal pull-up on common pin"],
)

# ── Light Button (Illuminated Push Button) ─────────────────────────────────────

LIGHT_BUTTON = CatalogComponent(
    id="light_button",
    name="Light Button (Illuminated Push Button)",
    category="input",
    wokwi_id="wokwi-pushbutton",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1.l",  description="Button Signal Input", pin_type="digital", required=True),
        ComponentPin(name="1.r",  description="Button Signal Right", pin_type="digital", required=False),
        ComponentPin(name="2.l",  description="Button Ground", pin_type="ground", required=True),
        ComponentPin(name="2.r",  description="Button Ground Right", pin_type="ground", required=False),
        ComponentPin(name="led+", description="Button LED Anode Indicator", pin_type="digital", required=True),
        ComponentPin(name="led-", description="Button LED Cathode", pin_type="ground", required=True),
    ],
    unit_price_inr=25.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Tactile push button with integrated LED light indicator for interactive illumination control",
    electrical_constraints=["Button signal requires INPUT_PULLUP; LED requires current limiting or GPIO driver"],
)

# ── 5V Relay Module ───────────────────────────────────────────────────────────

RELAY = CatalogComponent(
    id="relay",
    name="5V Relay Module",
    category="actuator",
    wokwi_id="wokwi-relay-module",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC", description="5V/3.3V Power", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
        ComponentPin(name="IN",  description="Control Signal", pin_type="digital", required=True),
        ComponentPin(name="NO",  description="Normally Open", pin_type="signal", required=False),
        ComponentPin(name="COM", description="Common Terminal", pin_type="signal", required=False),
        ComponentPin(name="NC",  description="Normally Closed", pin_type="signal", required=False),
    ],
    unit_price_inr=65.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Electromechanical relay module for switching AC mains or high-power DC appliances",
    electrical_constraints=["Active LOW or HIGH trigger; optical isolation built-in"],
)

# ── RGB LED (Common Cathode) ──────────────────────────────────────────────────

RGB_LED = CatalogComponent(
    id="rgb_led",
    name="RGB LED (Common Cathode)",
    category="output",
    wokwi_id="wokwi-rgb-led",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="R",   description="Red Anode", pin_type="digital", required=True),
        ComponentPin(name="G",   description="Green Anode", pin_type="digital", required=True),
        ComponentPin(name="B",   description="Blue Anode", pin_type="digital", required=True),
        ComponentPin(name="COM", description="Common Cathode (GND)", pin_type="ground", required=True),
    ],
    unit_price_inr=15.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="5mm diffused RGB LED for full-spectrum multi-color lighting and status indication",
    electrical_constraints=["Current limit resistors 220Ω recommended on R, G, B channels"],
)

# ── Additional LEDs ───────────────────────────────────────────────────────────

LED_GREEN = CatalogComponent(
    id="led_green",
    name="5mm Green LED",
    category="output",
    wokwi_id="wokwi-led",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="A", description="Anode (+)", pin_type="signal", required=True),
        ComponentPin(name="C", description="Cathode (-)", pin_type="ground", required=True),
    ],
    unit_price_inr=3.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Standard 5mm green indicator LED",
    electrical_constraints=["Forward voltage ~2.2V; 220Ω resistor required"],
)

LED_BLUE = CatalogComponent(
    id="led_blue",
    name="5mm Blue LED",
    category="output",
    wokwi_id="wokwi-led",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="A", description="Anode (+)", pin_type="signal", required=True),
        ComponentPin(name="C", description="Cathode (-)", pin_type="ground", required=True),
    ],
    unit_price_inr=3.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Standard 5mm blue indicator LED",
    electrical_constraints=["Forward voltage ~3.0V; 220Ω resistor required"],
)

RESISTOR_1K = CatalogComponent(
    id="resistor_1k",
    name="1kΩ Resistor",
    category="passive",
    wokwi_id="wokwi-resistor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1", description="Lead 1", pin_type="signal", required=True),
        ComponentPin(name="2", description="Lead 2", pin_type="signal", required=True),
    ],
    unit_price_inr=2.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="1kΩ 1/4W through-hole carbon film resistor",
    electrical_constraints=["Max 250mW power dissipation"],
)

# ── 16x2 Character LCD with I2C ───────────────────────────────────────────────

LCD1602_I2C = CatalogComponent(
    id="lcd1602_i2c",
    name="16x2 I2C Character LCD Display",
    category="display",
    wokwi_id="wokwi-lcd1602",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
        ComponentPin(name="VCC", description="Power 5V/3.3V", pin_type="power", required=True),
        ComponentPin(name="SDA", description="I2C Data", pin_type="digital", required=True),
        ComponentPin(name="SCL", description="I2C Clock", pin_type="digital", required=True),
    ],
    libraries=["LiquidCrystal I2C"],
    unit_price_inr=190.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="16x2 alphanumeric LCD with PCF8574 I2C backpack adapter (Address 0x27)",
    electrical_constraints=["Connect SDA to GPIO21, SCL to GPIO22 on ESP32"],
)

# ── 0.96\" I2C OLED Display (SSD1306) ──────────────────────────────────────────

SSD1306_I2C = CatalogComponent(
    id="ssd1306_i2c",
    name="0.96\" I2C OLED Display (SSD1306)",
    category="display",
    wokwi_id="wokwi-ssd1306",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
        ComponentPin(name="VCC", description="Power 3.3V", pin_type="power", required=True),
        ComponentPin(name="SCL", description="I2C Clock", pin_type="digital", required=True),
        ComponentPin(name="SDA", description="I2C Data", pin_type="digital", required=True),
    ],
    libraries=["Adafruit SSD1306", "Adafruit GFX Library"],
    unit_price_inr=220.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="128x64 monochrome OLED graphic display module with I2C interface (Address 0x3C)",
    electrical_constraints=["3.3V operation; connect SDA to GPIO21, SCL to GPIO22"],
)

# ── MPU6050 6-Axis Accelerometer / Gyroscope ──────────────────────────────────

MPU6050 = CatalogComponent(
    id="mpu6050",
    name="MPU6050 6-Axis Accelerometer / Gyroscope",
    category="sensor",
    wokwi_id="wokwi-mpu6050",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VCC", description="Power 3.3V", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
        ComponentPin(name="SCL", description="I2C Clock", pin_type="digital", required=True),
        ComponentPin(name="SDA", description="I2C Data", pin_type="digital", required=True),
        ComponentPin(name="INT", description="Interrupt Signal", pin_type="digital", required=False),
    ],
    libraries=["Adafruit MPU6050", "Adafruit Sensor"],
    unit_price_inr=180.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Triple-axis accelerometer and gyro sensor for orientation, motion, and tilt detection",
    electrical_constraints=["I2C address 0x68; connect to ESP32 standard I2C pins"],
)

# ── 4x4 Membrane Matrix Keypad ────────────────────────────────────────────────

MEMBRANE_KEYPAD = CatalogComponent(
    id="membrane_keypad",
    name="4x4 Membrane Matrix Keypad",
    category="input",
    wokwi_id="wokwi-membrane-keypad",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="R1", description="Row 1", pin_type="digital", required=True),
        ComponentPin(name="R2", description="Row 2", pin_type="digital", required=True),
        ComponentPin(name="R3", description="Row 3", pin_type="digital", required=True),
        ComponentPin(name="R4", description="Row 4", pin_type="digital", required=True),
        ComponentPin(name="C1", description="Column 1", pin_type="digital", required=True),
        ComponentPin(name="C2", description="Column 2", pin_type="digital", required=True),
        ComponentPin(name="C3", description="Column 3", pin_type="digital", required=True),
        ComponentPin(name="C4", description="Column 4", pin_type="digital", required=True),
    ],
    unit_price_inr=75.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="16-key matrix numeric keypad for PIN code entry and user input",
    electrical_constraints=["8 digital GPIO lines required for row/column scanning"],
)

# ── NTC Temperature Sensor ───────────────────────────────────────────────────

NTC_TEMPERATURE = CatalogComponent(
    id="ntc_temperature",
    name="NTC Temperature Sensor (Thermistor)",
    category="sensor",
    wokwi_id="wokwi-ntc-temperature-sensor",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="OUT", description="Analog Output", pin_type="analog", required=True),
        ComponentPin(name="VCC", description="3.3V Power", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
    ],
    unit_price_inr=30.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Negative Temperature Coefficient thermistor module for temperature measurement",
    electrical_constraints=["Connect to ADC pin (GPIO32-39 on ESP32)", "3.3V supply"],
)

# ── KY-040 Rotary Encoder ─────────────────────────────────────────────────────

ROTARY_ENCODER = CatalogComponent(
    id="rotary_encoder",
    name="KY-040 Rotary Encoder",
    category="input",
    wokwi_id="wokwi-ky-040",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="CLK", description="Clock output A", pin_type="digital", required=True),
        ComponentPin(name="DT", description="Data output B", pin_type="digital", required=True),
        ComponentPin(name="SW", description="Pushbutton switch", pin_type="digital", required=False),
        ComponentPin(name="VCC", description="Power 3.3V", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
    ],
    unit_price_inr=90.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Incremental 360-degree rotary encoder with integrated push button",
    electrical_constraints=["Requires interrupt-capable GPIO pins for CLK and DT", "Internal pull-ups recommended"],
)

# ── Analog Joystick Module ────────────────────────────────────────────────────

ANALOG_JOYSTICK = CatalogComponent(
    id="analog_joystick",
    name="Dual-Axis Analog Joystick",
    category="input",
    wokwi_id="wokwi-analog-joystick",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="VERT", description="Y-axis analog output", pin_type="analog", required=True),
        ComponentPin(name="HORZ", description="X-axis analog output", pin_type="analog", required=True),
        ComponentPin(name="SEL", description="Switch / push button", pin_type="digital", required=False),
        ComponentPin(name="VCC", description="Power 3.3V", pin_type="power", required=True),
        ComponentPin(name="GND", description="Ground", pin_type="ground", required=True),
    ],
    unit_price_inr=110.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Dual potentiometer thumb joystick with center push button",
    electrical_constraints=["Requires 2 ADC analog inputs and 1 digital input"],
)

# ── 10-Segment LED Bar Graph ──────────────────────────────────────────────────

LED_BAR_GRAPH = CatalogComponent(
    id="led_bar_graph",
    name="10-Segment LED Bar Graph",
    category="display",
    wokwi_id="wokwi-led-bar-graph",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="A1", description="Anode segment 1", pin_type="digital", required=True),
        ComponentPin(name="A2", description="Anode segment 2", pin_type="digital", required=True),
        ComponentPin(name="A3", description="Anode segment 3", pin_type="digital", required=True),
        ComponentPin(name="A4", description="Anode segment 4", pin_type="digital", required=True),
        ComponentPin(name="A5", description="Anode segment 5", pin_type="digital", required=True),
        ComponentPin(name="C1", description="Cathode segment 1", pin_type="ground", required=True),
    ],
    unit_price_inr=45.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="10-level LED indicator bar graph for volume or level meters",
    electrical_constraints=["Current-limiting resistors required per active segment"],
)

# ── 7-Segment Display ─────────────────────────────────────────────────────────

SEVEN_SEGMENT = CatalogComponent(
    id="seven_segment",
    name="7-Segment LED Display",
    category="display",
    wokwi_id="wokwi-7segment",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="A", description="Segment A", pin_type="digital", required=True),
        ComponentPin(name="B", description="Segment B", pin_type="digital", required=True),
        ComponentPin(name="C", description="Segment C", pin_type="digital", required=True),
        ComponentPin(name="D", description="Segment D", pin_type="digital", required=True),
        ComponentPin(name="E", description="Segment E", pin_type="digital", required=True),
        ComponentPin(name="F", description="Segment F", pin_type="digital", required=True),
        ComponentPin(name="G", description="Segment G", pin_type="digital", required=True),
        ComponentPin(name="COM", description="Common pin", pin_type="ground", required=True),
    ],
    unit_price_inr=25.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="Classic 1-digit 7-segment numerical LED display",
    electrical_constraints=["Current limiting resistors required"],
)

# ── 8-Position DIP Switch ─────────────────────────────────────────────────────

DIP_SWITCH_8 = CatalogComponent(
    id="dip_switch_8",
    name="8-Position DIP Switch",
    category="input",
    wokwi_id="wokwi-dip-switch-8",
    supported_boards=["esp32", "arduino_uno", "arduino_nano"],
    pins=[
        ComponentPin(name="1", description="Switch 1", pin_type="digital", required=True),
        ComponentPin(name="2", description="Switch 2", pin_type="digital", required=True),
        ComponentPin(name="3", description="Switch 3", pin_type="digital", required=True),
        ComponentPin(name="4", description="Switch 4", pin_type="digital", required=True),
    ],
    unit_price_inr=35.0,
    price_source="catalog_estimate",
    price_verified_date="2025-01-01",
    description="8-way slide DIP configuration switch array",
    electrical_constraints=["Use internal pull-ups on inputs"],
)


# ── Catalog Registry ──────────────────────────────────────────────────────────

CATALOG: dict[str, CatalogComponent] = {
    c.id: c for c in [
        ESP32_DEVKIT,
        DHT22,
        LED_RED,
        LED_GREEN,
        LED_BLUE,
        RGB_LED,
        RESISTOR_220,
        RESISTOR_1K,
        RESISTOR_10K,
        HC_SR04,
        BUZZER,
        PUSH_BUTTON,
        LIGHT_BUTTON,
        SLIDE_SWITCH,
        POTENTIOMETER,
        PHOTORESISTOR,
        PIR_MOTION,
        MQ135,
        SERVO,
        RELAY,
        LCD1602_I2C,
        SSD1306_I2C,
        TFT_ILI9341,
        MPU6050,
        MEMBRANE_KEYPAD,
        NTC_TEMPERATURE,
        ROTARY_ENCODER,
        ANALOG_JOYSTICK,
        LED_BAR_GRAPH,
        SEVEN_SEGMENT,
        DIP_SWITCH_8,
    ]
}

# Valid GPIO numbers for ESP32 (excluding reserved flash pins 6-11)
ESP32_VALID_GPIO: set[int] = {0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19,
                               21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39}
ESP32_OUTPUT_GPIO: set[int] = {0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19,
                                21, 22, 23, 25, 26, 27, 32, 33}
ESP32_ANALOG_GPIO: set[int] = {32, 33, 34, 35, 36, 39, 25, 26}


def get_component(component_id: str) -> Optional[CatalogComponent]:
    return CATALOG.get(component_id)


def list_components() -> list[CatalogComponent]:
    return list(CATALOG.values())


def search_components(query: str) -> list[CatalogComponent]:
    q = query.lower()
    return [c for c in CATALOG.values()
            if q in c.name.lower() or q in c.description.lower() or q in c.category.lower()]
