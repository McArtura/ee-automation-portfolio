# EE Portfolio — Automation & Control Systems

Electrical Engineering student project portfolio focused on automation: sensing, decision logic, and actuation across three layers — embedded firmware, control theory, and signal processing.

## Projects

### 1. [Smart Irrigation & Climate Automation](./smart-automation-esp32) — ESP32 firmware
Sensor-driven automation of a water pump and fan using hysteresis control and a runtime safety cutoff, with a live WiFi dashboard. The embedded/hardware layer of the "sense -> decide -> act" loop.

### 2. [PID Motor Speed Controller](./pid-motor-control) — Python / control theory
Closed-loop DC motor speed control built from the motor's physical equations, comparing P, PI, and PID tuning under a load disturbance. The control-theory layer.

### 3. [Predictive Maintenance via FFT](./predictive-maintenance-fft) — Python / DSP
Automated bearing-fault detection from simulated vibration data using FFT and a statistically-derived threshold — turning raw sensor data into an automatic health verdict. The signal-processing / decision layer.

## Why these three together

Automation shows up differently at each layer of a real system: firmware that reads sensors and drives relays in real time, control theory that keeps a physical quantity (like speed) locked to a setpoint, and signal processing that turns raw waveforms into decisions. These three projects are deliberately built to show the same underlying pattern at each layer, using the actual equations/math involved rather than pre-built libraries doing the work invisibly.

## Skills demonstrated

Embedded C/C++ (ESP32/Arduino), sensor interfacing (analog + digital), relay/actuator control, control systems (PID design, hysteresis, anti-windup), digital signal processing (FFT, spectral analysis, statistical thresholding), Python (NumPy, Matplotlib), and technical documentation.

## Setup

Each project folder has its own README with run instructions. The two Python projects only need:

```bash
pip install numpy matplotlib scipy
```

The ESP32 project needs the Arduino IDE (or PlatformIO) with the ESP32 board package and the Adafruit DHT library — details in its README.
