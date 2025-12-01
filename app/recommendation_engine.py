#!/usr/bin/env python3
"""
RecommendationEngine
- Structured, humanized explanations
- Intensity scaling (mild/moderate/high)
- Priority-based multi-label logic
- Short and detailed output modes
- Clean, maintainable layout
"""

from typing import List, Dict, Optional
import random

# -------------------------
# Humanized text resources
# -------------------------

# Activity descriptions (humanized)
ACTIVITY_DESCRIPTIONS = {
    "Resting": "Your body is calm and you're not doing any physical activity.",
    "Light activity": "You're moving lightly, maybe walking around or doing something small.",
    "Moderate activity": "You're fairly active, like walking fast or doing light exercise.",
    "High activity": "Your body is working hard, similar to jogging or physical work.",
    "Sleeping": "You're currently in a relaxed sleep state.",
    "Walking": "You're moving at a steady walking pace.",
    "Running": "You're engaged in a high-effort activity like running.",
    "Sedentary": "You've been sitting or staying in one position for a while."
}

# Health status descriptions
HEALTH_STATUS_DESCRIPTIONS = {
    "Normal": "Everything looks okay with your readings.",
    "Healthy": "Your readings fall within a good and stable range.",
    "Slight abnormality": "Something looks a bit off, but not serious.",
    "Warning": "Some readings are outside the normal range and need attention.",
    "Critical": "Your readings suggest a serious condition that needs immediate care."
}

# Environment descriptions
ENVIRONMENTAL_DESCRIPTIONS = {
    "Hot environment": "The temperature around you is higher than normal.",
    "Cold environment": "The surrounding temperature is quite low.",
    "Humid environment": "The humidity level is high where you are.",
    "Low-pressure environment": "The air pressure around you is lower than normal."
}

# Health condition base descriptions
HEALTH_CONDITION_DESCRIPTIONS = {
    "Stressed": "Your body is showing signs of stress.",
    "Fatigued": "You're showing signs of tiredness.",
    "Dehydrated": "Your hydration level may be low.",
    "Possible fever": "Your temperature is higher than normal.",
    "Low oxygen state": "Your oxygen level is lower than it should be.",
    "Overexertion": "Your body is working harder than normal.",
    "Early illness indication": "Some patterns suggest you might be coming down with something."
}

# Intensity-based phrasing for conditions
CONDITION_INTENSITY_MESSAGES = {
    "Stressed": {
        "mild": "Your stress level is slightly raised.",
        "moderate": "You're showing noticeable signs of stress.",
        "high": "Your stress level is high and it's worth taking immediate steps to relax."
    },
    "Fatigued": {
        "mild": "You seem a bit tired.",
        "moderate": "You're getting noticeably fatigued; consider resting soon.",
        "high": "You're very fatigued and need proper rest."
    },
    "Dehydrated": {
        "mild": "You might need to drink a little more water.",
        "moderate": "You're getting dehydrated and should drink water soon.",
        "high": "You're likely very dehydrated — rehydrate as soon as possible."
    },
    "Possible fever": {
        "mild": "Your temperature is slightly above normal.",
        "moderate": "Your temperature is fairly high.",
        "high": "Your temperature is very high and may need urgent attention."
    },
    "Low oxygen state": {
        "mild": "Your oxygen level is a bit below normal.",
        "moderate": "Your oxygen level is low and needs attention.",
        "high": "Your oxygen level is dangerously low — seek help immediately."
    },
    "Overexertion": {
        "mild": "You're pushing yourself a little.",
        "moderate": "You're working your body harder than usual.",
        "high": "You're overexerting and should stop to rest right away."
    },
    "Early illness indication": {
        "mild": "There are a few small signs that something may be starting.",
        "moderate": "There are several signs that could mean you're getting unwell.",
        "high": "Strong signs suggest you may be getting ill — monitor closely or consult a clinician."
    }
}

# Action suggestions (humanized, consistent)
RECOMMENDATION_ACTIONS = {
    "Critical": "Please get medical help immediately. It's not safe to ignore this.",
    "Low oxygen state": "Move to a place with better airflow. If it does not improve, seek medical support.",
    "Possible fever": "Try to rest and drink water. Check your temperature again later. If it stays high, consult a doctor.",
    "Dehydrated": "Drink water and rest in a cool spot for a while.",
    "Overexertion": "Stop and rest. Allow your body to recover before continuing.",
    "Stressed": "Pause for a moment, take slow breaths, and try to relax.",
    "Fatigued": "Consider resting or taking a short nap if possible.",
    "Hot environment": "Move somewhere cooler and hydrate if you can.",
    "Cold environment": "Try to warm up or move to a warmer place.",
    "Humid environment": "Ensure good ventilation and drink water.",
    "Low-pressure environment": "If you feel dizzy, sit down and allow your body to adjust.",
    "Running": "Slow down if needed and make sure you drink enough water.",
    "Walking": "Keep a steady pace and stay hydrated if outdoors.",
    "Sedentary": "Stand up, stretch, or go for a short walk.",
    "Resting": "No action needed right now.",
    "Light activity": "You can continue what you're doing.",
    "Moderate activity": "You're doing okay; slow down if you feel tired.",
    "High activity": "Be careful and hydrate; slow down if you feel strained."
}

# Priority map (higher means more important)
LABEL_PRIORITY = {
    "Critical": 100,
    "Low oxygen state": 90,
    "Possible fever": 85,
    "Overexertion": 80,
    "Dehydrated": 75,
    "Fatigued": 70,
    "Stressed": 65,

    # Activity
    "Running": 40,
    "High activity": 38,
    "Moderate activity": 35,
    "Walking": 30,
    "Light activity": 25,
    "Resting": 20,
    "Sedentary": 15,
    "Sleeping": 10,

    # Environment (lower priority)
    "Hot environment": 12,
    "Cold environment": 11,
    "Humid environment": 10,
    "Low-pressure environment": 9,
}

# Small set of soft intro phrases to vary language a bit
INTRO_PHRASES = [
    "From your readings,",
    "Based on the sensors,",
    "From what the data shows,"
]

# -------------------------
# Engine implementation
# -------------------------

class RecommendationEngine:
    """
    RecommendationEngineV2:
      - Accepts predicted labels, optional intensity map, optional sensor data
      - Produces user-friendly explanations in 'short' or 'detailed' mode
    """

    def __init__(self):
        # Public resources (for easy tweaking)
        self.activity_desc = ACTIVITY_DESCRIPTIONS
        self.status_desc = HEALTH_STATUS_DESCRIPTIONS
        self.env_desc = ENVIRONMENTAL_DESCRIPTIONS
        self.cond_desc = HEALTH_CONDITION_DESCRIPTIONS
        self.intensity_msgs = CONDITION_INTENSITY_MESSAGES
        self.actions = RECOMMENDATION_ACTIONS
        self.priority = LABEL_PRIORITY

    # -------------------------
    # Utility helpers
    # -------------------------
    def _safe_format(self, value, decimals=1):
        """Format numeric sensor values safely."""
        try:
            return f"{float(value):.{decimals}f}"
        except Exception:
            return "N/A"

    def _format_list(self, items: List[str], connector: str = "and"):
        """Natural-language list formatting."""
        items = list(dict.fromkeys(items))  # dedupe while preserving order
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} {connector} {items[1]}"
        return f"{', '.join(items[:-1])}, {connector} {items[-1]}"

    def _select_top_label(self, labels: List[str]) -> Optional[str]:
        """Return label with highest priority. If empty, None."""
        if not labels:
            return None
        return max(labels, key=lambda l: self.priority.get(l, 0))

    def _classify_labels(self, labels: List[str]):
        """Split labels into activity / condition / environment / status lists."""
        activity = []
        conditions = []
        environment = []
        status = []
        for l in labels:
            if l in self.activity_desc:
                activity.append(l)
            elif l in self.cond_desc:
                conditions.append(l)
            elif l in self.env_desc:
                environment.append(l)
            elif l in self.status_desc:
                status.append(l)
            else:
                # Unknown labels treated as conditions (fallback)
                conditions.append(l)
        return activity, conditions, environment, status

    def _cond_message(self, label: str, intensity: Optional[str] = None) -> str:
        """Return an intensity-aware message for a condition."""
        if not label:
            return ""
        if label in self.intensity_msgs:
            if intensity in ("mild", "moderate", "high"):
                return self.intensity_msgs[label].get(intensity) or self.cond_desc.get(label, "")
            # choose a default phrasing if intensity not given
            return self.intensity_msgs[label].get("moderate", self.cond_desc.get(label, ""))
        # fallback to general description
        return self.cond_desc.get(label, "")

    # -------------------------
    # Core interpretation
    # -------------------------
    def interpret(self,
                  predicted_labels: List[str],
                  sensor_data: Optional[Dict] = None,
                  intensity_map: Optional[Dict[str, str]] = None,
                  mode: str = "detailed") -> Dict[str, str]:
        """
        Build a user-facing interpretation.

        Args:
            predicted_labels: list of labels from the model
            intensity_map: optional dict mapping specific labels to 'mild'|'moderate'|'high'
            sensor_data: optional sensor readings used for context in the output
            mode: 'short' or 'detailed'

        Returns:
            dict with keys: 'summary', 'recommendation', 'priority', 'full_message'
        """
        intensity_map = intensity_map or {}
        sensor_data = sensor_data or {}

        # classify labels
        activity, conditions, environment, status = self._classify_labels(predicted_labels)

        # choose main issue by priority
        main_label = self._select_top_label(predicted_labels)

        # Determine priority level string
        if main_label == "Critical" or "Critical" in predicted_labels:
            priority_level = "critical"
        elif any(l in ("Low oxygen state", "Possible fever", "Warning") for l in predicted_labels):
            priority_level = "warning"
        elif any(l in self.cond_desc for l in predicted_labels):
            priority_level = "caution"
        else:
            priority_level = "normal"

        # Build opening summary
        intro = random.choice(INTRO_PHRASES)
        parts = []

        # If there's a main_label and it's a condition, add its intensity phrase first
        if main_label and main_label in self.cond_desc:
            intensity = intensity_map.get(main_label)
            parts.append(self._cond_message(main_label, intensity))

        # If there are other conditions, describe them briefly
        other_conditions = [c for c in conditions if c != main_label]
        if other_conditions:
            brief = self._format_list([self._cond_message(c, intensity_map.get(c)) for c in other_conditions], connector="and")
            if brief:
                parts.append(brief)

        # Add activity context
        if activity:
            activity_text = self._format_list(activity, connector="and")
            parts.append(self.activity_desc.get(activity[0], f"You appear to be {activity_text.lower()}"))

        # Add environment context
        if environment:
            env_text = self._format_list([self.env_desc.get(e, e) for e in environment], connector="and")
            if env_text:
                parts.append(env_text)

        # Add health status if present and not normal
        if status:
            non_normal = [s for s in status if s not in ("Normal", "Healthy")]
            if non_normal:
                parts.append(self._format_list(non_normal, connector="and").lower() + " health indicators present")

        # Build the summary sentence(s)
        if parts:
            # Capitalize first part for neatness
            summary_text = " ".join([p[0].upper() + p[1:] if p else "" for p in parts])
            summary = f"{intro} {summary_text}"
        else:
            summary = f"{intro} everything looks normal."

        # Build the recommendation (action) list, respecting priority
        rec_actions = []
        # Main label action first (highest priority)
        if main_label and main_label in self.actions:
            rec_actions.append(self.actions[main_label])
        # Add actions for other important conditions
        for cond in other_conditions + activity + environment:
            action = self.actions.get(cond)
            if action and action not in rec_actions:
                rec_actions.append(action)

        # If no specific actions, provide a general friendly suggestion
        if not rec_actions:
            rec_actions.append("Keep monitoring your readings and stay hydrated. Take rest if you feel unwell.")

        # Compose recommendation text
        if mode == "short":
            recommendation = rec_actions[0]
            full_message = f"{summary} {recommendation}"
        else:
            # detailed: organize into paragraphs
            rec_para = " ".join(rec_actions)
            # sensor context if available
            sensor_lines = []
            if sensor_data:
                bt = self._safe_format(sensor_data.get("body_temp"))
                hr = self._safe_format(sensor_data.get("heart_rate_bpm"), 0)
                sp = self._safe_format(sensor_data.get("spo2_pct"))
                at = self._safe_format(sensor_data.get("ambient_temp"))
                hu = self._safe_format(sensor_data.get("humidity_pct"))
                sensor_lines = [
                    f"Body temp: {bt}°C" if bt != "N/A" else None,
                    f"Heart rate: {hr} BPM" if hr != "N/A" else None,
                    f"SpO₂: {sp}%" if sp != "N/A" else None,
                    f"Ambient: {at}°C, {hu}%" if at != "N/A" and hu != "N/A" else None
                ]
                sensor_lines = [s for s in sensor_lines if s]
            # assemble detailed full message
            sensor_block = ("\n".join(sensor_lines) + "\n\n") if sensor_lines else ""
            full_message = f"{summary}\n\nWhat this means:\n{rec_para}\n\n{sensor_block}Suggested next step: {rec_actions[0]}"

            recommendation = rec_para

        # Return structured result
        return {
            "summary": summary,
            "recommendation": recommendation,
            "priority": priority_level,
            "full_message": full_message
        }

# -------------------------
# Example usage (scenarios)
# -------------------------

def _demo():
    engine = RecommendationEngine()

    scenarios = [
        {
            "name": "Scenario A — Low oxygen + Hot + Walking",
            "labels": ["Low oxygen state", "Hot environment", "Walking"],
            "intensity_map": {"Low oxygen state": "moderate"},
            "sensors": {
                "body_temp": 37.9,
                "heart_rate_bpm": 110,
                "spo2_pct": 91.0,
                "ambient_temp": 33.0,
                "humidity_pct": 70.0
            }
        },
        {
            "name": "Scenario B — Running + Dehydrated (high)",
            "labels": ["Running", "Dehydrated", "High activity"],
            "intensity_map": {"Dehydrated": "high"},
            "sensors": {
                "body_temp": 38.2,
                "heart_rate_bpm": 150,
                "spo2_pct": 95.0,
                "ambient_temp": 30.0,
                "humidity_pct": 60.0
            }
        },
        {
            "name": "Scenario C — Normal Resting",
            "labels": ["Resting", "Normal"],
            "intensity_map": {},
            "sensors": {
                "body_temp": 36.8,
                "heart_rate_bpm": 68,
                "spo2_pct": 98.0,
                "ambient_temp": 24.0,
                "humidity_pct": 45.0
            }
        },
        {
            "name": "Scenario D — Critical + Possible fever + Overexertion",
            "labels": ["Critical", "Possible fever", "Overexertion"],
            "intensity_map": {"Possible fever": "high", "Overexertion": "moderate"},
            "sensors": {
                "body_temp": 39.5,
                "heart_rate_bpm": 165,
                "spo2_pct": 89.0,
                "ambient_temp": 25.0,
                "humidity_pct": 55.0
            }
        }
    ]

    for s in scenarios:
        print("\n" + "="*70)
        print(s["name"])
        print("-"*70)
        short = engine.interpret(s["labels"], s["intensity_map"], s["sensors"], mode="short")
        detailed = engine.interpret(s["labels"], s["intensity_map"], s["sensors"], mode="detailed")
        print("\nSHORT MODE:")
        print(short["full_message"])
        print("\nDETAILED MODE:")
        print(detailed["full_message"])
        print("="*70 + "\n")

if __name__ == "__main__":
    _demo()
