# VitaBand — System Architecture

This document describes the high-level architecture for VitaBand, a wearable IoT health
system that collects physiological and environmental data, performs local processing and
ML inference on a Raspberry Pi, and publishes user-friendly summaries to a mobile app
over MQTT.

## Table of contents

- [High-level overview](#high-level-overview)
- [Architecture components](#architecture-components)
	- [Sensor layer](#sensor-layer)
	- [Edge computing (Raspberry Pi)](#edge-computing-raspberry-pi)
		- [Data acquisition](#data-acquisition)
		- [Feature extraction](#feature-extraction)
		- [On-device ML inference](#on-device-ml-inference)
		- [Interpretation & recommendations](#interpretation--recommendations)
		- [Local alerts & storage](#local-alerts--storage)
	- [Local MQTT communication](#local-mqtt-communication)
	- [Mobile app layer](#mobile-app-layer)
- [Data flow summary](#data-flow-summary)
- [System strengths](#system-strengths)
- [Next steps / suggestions](#next-steps--suggestions)

## High-level overview

VitaBand is a wearable health device ecosystem that:

- Collects physiological and environmental data from multiple sensors.
- Processes and extracts features locally on a Raspberry Pi.
- Runs a lightweight ML model (e.g., PyTorch Lite or ONNX Runtime) for inference.
- Produces plain-English insights and recommendations via a small rule engine.
- Publishes vitals and explanations to a mobile app using MQTT (works offline on local
	Wi‑Fi).

The main logical layers are:

1. Wearable / Sensor layer (edge sensors)
2. Edge computing & ML inference (Raspberry Pi)
3. Mobile app / dashboard (MQTT subscriber)
4. Cloud storage & analytics (optional)

## Architecture components

### Sensor layer

Sensors connect directly to the Raspberry Pi (I²C) and capture both physiological and
environmental signals.

Key sensors and their purposes:

| Sensor     | Purpose                                      |
|------------|----------------------------------------------|
| MAX30102   | Heart rate, SpO₂, PPG waveform               |
| MCP9808    | Body (skin) temperature                      |
| BME280     | Ambient temperature, humidity, pressure     |
| MPU6050    | Body movement: accelerometer + gyro (steps,
|            | orientation, motion artifact detection)      |

This layer provides raw streams that feed the edge-processing modules.

### Edge computing (Raspberry Pi)

The Raspberry Pi runs several cooperating modules:

#### Data acquisition

- Python scripts read sensor values over I²C.
- Timestamp synchronization across sensors.
- Basic preprocessing: outlier removal and motion-PPG artifact detection.

#### Feature extraction

- Periodic aggregation (example: every 30 seconds) to compute features:
	- HR mean and HR variability (HRV)
	- SpO₂ mean
	- Skin temperature trend
	- Motion intensity (accelerometer energy)
	- Ambient conditions (temp, humidity, pressure)
	- PPG signal quality metrics

#### On-device ML inference

- A compact model (PyTorch Lite or ONNX Runtime) consumes fused features and
	produces predictions such as:
	- Stress
	- Fatigue
	- Early illness
	- Possible fever
	- Low oxygen (hypoxemia)
	- Overtraining
	- Dehydration (inferred from HR trends + temp + humidity + HRV)
	- Activity state: sleep / rest / active / normal

#### Interpretation & recommendations

- A small rule-based engine converts model outputs and features into human-friendly
	explanations and action suggestions.

Examples:

> "Your heart rate is slightly higher than usual for your activity level. This may
> indicate that your body is under stress. It could be helpful to rest for a few
> minutes."

#### Local alerts & storage

- Real-time local alerts (e.g., "High stress detected", "Possible fever symptoms").
- Local storage using SQLite for offline buffering and historical queries.

### Local MQTT communication

The Raspberry Pi acts as an MQTT publisher on the local network. Example topics:

| Topic                      | Description                                   |
|---------------------------:|:----------------------------------------------|
| vitaband/vitals            | HR, SpO₂, Temp, Motion, etc.                  |
| vitaband/explanation       | Plain-English insights and action
|                           | recommendations                                |
| vitaband/device/status     | Battery, uptime, errors                        |

The mobile app subscribes to the relevant topics. This approach supports fully
offline operation when both devices are on the same Wi‑Fi network.

### Mobile app layer

Expected mobile app capabilities:

- Connect to the same Wi‑Fi network as the Raspberry Pi and subscribe to MQTT topics.
- Display real-time vitals and plain-English insights.
- Plot time-series trends (historical data from local storage or periodic sync).
- Present alerts and recommended actions.
- Operate without internet access (local-only mode).

## Data flow summary

Sensors → Raspberry Pi (I²C)

Raw data → cleaning → feature extraction → ML model → interpretation/recommendation

Raspberry Pi (MQTT publish) → Mobile app (MQTT subscribe)

Summaries and synced state: typically every 5–10 minutes for aggregated summaries;
real-time vitals may be streamed at higher frequency depending on bandwidth and
power constraints.

## System strengths

- On-device ML reduces cloud costs and dependency on internet connectivity.
- Fully offline capability preserves privacy (data can stay on the local network).
- Personalized, context-aware insights using fused multimodal signals.
- Fast, reliable messaging using MQTT.
- Modular design — scalable from prototype to commercial deployment.

## Next steps & suggestions

- Define data retention and privacy policies for local storage.
- Add secure MQTT (TLS + authentication) for deployments that cross network
	boundaries.
- Create a lightweight mobile app prototype (MQTT client) for end-to-end testing.
- Add automated tests for feature extraction and model inference (unit + integration).

## License & contact

Include appropriate license and author/contact information here.

---

If you'd like, I can also:

- Convert the MQTT topics into a publish/subscribe sequence diagram.
- Generate a minimal mobile app mock that subscribes to the topics.
- Add example payload formats for each MQTT topic.

Tell me which of those you'd like next.