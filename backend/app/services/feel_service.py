"""Minimal functional FeelVsYesterdayService.

Implements lightweight comparative logic required by integration tests using
legacy ``MedicationLog`` and ``SymptomLog`` models. This is NOT the final
production analytics algorithm; it provides deterministic, explainable status
derivation to satisfy current tests until the unified logging & analysis
design lands.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List

import structlog
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.schemas.logs import FeelVsYesterdayResponse
from app.models.logs import MedicationLog, SymptomLog, SeverityLevel

logger = structlog.get_logger(__name__)


class FeelVsYesterdayService:
    def __init__(self, db: Session):
        self.db = db

    # ---- Public API ----
    def analyze_feel_vs_yesterday(self, user_id: str, target_date: Optional[datetime] = None) -> FeelVsYesterdayResponse:
        if target_date is None:
            target_date = datetime.now(timezone.utc)

        today_start, today_end, y_start, y_end = self._date_windows(target_date)
        meds_today, meds_yesterday = self._fetch_medications(user_id, today_start, today_end, y_start, y_end)
        symptoms_today, symptoms_yesterday = self._fetch_symptoms(user_id, today_start, today_end, y_start, y_end)

        if not meds_today and not meds_yesterday and not symptoms_today and not symptoms_yesterday:
            return FeelVsYesterdayResponse(
                status="unknown",
                confidence=0.0,
                summary="Not enough data to compare today with yesterday.",
                details={},
                date_compared=y_start.date().isoformat(),
            )

        details = self._build_details(meds_today, meds_yesterday, symptoms_today, symptoms_yesterday)
        status, confidence, rationale = self._derive_status(details)

        return FeelVsYesterdayResponse(
            status=status,
            confidence=confidence,
            summary=rationale,
            details=details,
            date_compared=y_start.date().isoformat(),
        )

    # ---- Internal helpers ----
    def _date_windows(self, ref: datetime) -> Tuple[datetime, datetime, datetime, datetime]:
        ref = ref.astimezone(timezone.utc)
        today_start = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1) - timedelta(microseconds=1)
        y_start = today_start - timedelta(days=1)
        y_end = today_start - timedelta(microseconds=1)
        return today_start, today_end, y_start, y_end

    def _fetch_medications(self, user_id: str, t_start: datetime, t_end: datetime, y_start: datetime, y_end: datetime) -> Tuple[List[MedicationLog], List[MedicationLog]]:
        all_meds = [m for m in self.db.query(MedicationLog).all() if m.user_id == user_id]
        def normalize(dt: datetime) -> datetime:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        meds_today = [m for m in all_meds if m.taken_at and t_start <= normalize(m.taken_at) <= t_end]
        meds_yesterday = [m for m in all_meds if m.taken_at and y_start <= normalize(m.taken_at) <= y_end]
        return meds_today, meds_yesterday

    def _fetch_symptoms(self, user_id: str, t_start: datetime, t_end: datetime, y_start: datetime, y_end: datetime) -> Tuple[List[SymptomLog], List[SymptomLog]]:
        all_symptoms = [s for s in self.db.query(SymptomLog).all() if s.user_id == user_id]
        def normalize(dt: datetime) -> datetime:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        symptoms_today = [s for s in all_symptoms if s.started_at and t_start <= normalize(s.started_at) <= t_end]
        symptoms_yesterday = [s for s in all_symptoms if s.started_at and y_start <= normalize(s.started_at) <= y_end]
        return symptoms_today, symptoms_yesterday

    def _avg_effectiveness(self, meds: List[MedicationLog]) -> Optional[float]:
        vals = [m.effectiveness_rating for m in meds if m.effectiveness_rating is not None]
        return sum(vals) / len(vals) if vals else None

    def _avg_symptom_severity(self, symptoms: List[SymptomLog]) -> Optional[float]:
        vals = [s.severity for s in symptoms if s.severity is not None]
        return sum(vals) / len(vals) if vals else None

    def _severity_change(self, today: Optional[float], yesterday: Optional[float]) -> Optional[float]:
        if today is None or yesterday is None:
            return None
        return today - yesterday

    def _effectiveness_change(self, today: Optional[float], yesterday: Optional[float]) -> Optional[float]:
        if today is None or yesterday is None:
            return None
        return today - yesterday

    def _avg_side_effect_severity(self, meds: List[MedicationLog]) -> Optional[float]:
        vals = []
        for m in meds:
            sev = getattr(m, "side_effect_severity", None)
            if sev is not None:
                # Map SeverityLevel enum or int into numeric scale 0-3
                if isinstance(sev, SeverityLevel):
                    vals.append({SeverityLevel.MILD: 1, SeverityLevel.MODERATE: 2, SeverityLevel.SEVERE: 3}.get(sev, 0))
                elif isinstance(sev, int):
                    vals.append(sev)
        return sum(vals) / len(vals) if vals else None

    def _side_effect_change(self, today: Optional[float], yesterday: Optional[float]) -> Optional[float]:
        if today is None or yesterday is None:
            return None
        return today - yesterday

    def _build_details(self, meds_today, meds_yesterday, symptoms_today, symptoms_yesterday):
        eff_today = self._avg_effectiveness(meds_today)
        eff_yesterday = self._avg_effectiveness(meds_yesterday)
        sev_today = self._avg_symptom_severity(symptoms_today)
        sev_yesterday = self._avg_symptom_severity(symptoms_yesterday)
        se_today = self._avg_side_effect_severity(meds_today)
        se_yesterday = self._avg_side_effect_severity(meds_yesterday)
        return {
            "medication_count_today": len(meds_today),
            "medication_count_yesterday": len(meds_yesterday),
            "symptom_count_today": len(symptoms_today),
            "symptom_count_yesterday": len(symptoms_yesterday),
            "medication_effectiveness_change": self._effectiveness_change(eff_today, eff_yesterday),
            "symptom_severity_change": self._severity_change(sev_today, sev_yesterday),
            "side_effect_severity_change": self._side_effect_change(se_today, se_yesterday),
            "side_effect_avg_today": se_today,
            "side_effect_avg_yesterday": se_yesterday,
        }

    def _derive_status(self, details: dict) -> Tuple[str, float, str]:
        meds_change = details["medication_effectiveness_change"]
        symptom_change = details["symptom_severity_change"]
        side_effect_change = details.get("side_effect_severity_change")

        signals: List[str] = []
        # Medication effectiveness thresholds (wider deltas matter more)
        if meds_change is not None:
            if meds_change >= 1.0:
                signals.append("better_medication_strong")
            elif meds_change > 0.2:
                signals.append("better_medication")
            elif meds_change <= -1.0:
                signals.append("worse_medication_strong")
            elif meds_change < -0.2:
                signals.append("worse_medication")

        # Symptom severity (lower is better)
        if symptom_change is not None:
            if symptom_change <= -3.0:
                signals.append("better_symptoms_strong")
            elif symptom_change < -0.5:
                signals.append("better_symptoms")
            elif symptom_change >= 3.0:
                signals.append("worse_symptoms_strong")
            elif symptom_change > 0.5:
                signals.append("worse_symptoms")

        # Side effects (higher today worse). Even mild increase should influence confidence.
        if side_effect_change is not None:
            if side_effect_change > 0.5:
                signals.append("worse_side_effects")
            elif side_effect_change < -0.5:
                signals.append("better_side_effects")
        else:
            # If we have side effects today but none yesterday, treat as worsening.
            if details.get("side_effect_avg_today") is not None and details.get("side_effect_avg_yesterday") is None:
                signals.append("worse_side_effects")

        # Count-based heuristics
        if details["symptom_count_today"] < details["symptom_count_yesterday"]:
            signals.append("fewer_symptoms")
        if details["symptom_count_today"] > details["symptom_count_yesterday"]:
            signals.append("more_symptoms")

        positives = sum(1 for s in signals if s.startswith("better") or s == "fewer_symptoms")
        negatives = sum(1 for s in signals if s.startswith("worse") or s == "more_symptoms")

        if positives and not negatives:
            status = "better"
        elif negatives and not positives:
            status = "worse"
        elif positives and negatives:
            status = "same"  # mixed signals
        else:
            status = "same"

        # Confidence calculation:
        # Assign weights to signal strength
        weight_map = {
            "better_medication_strong": 0.25,
            "worse_medication_strong": 0.25,
            "better_symptoms_strong": 0.25,
            "worse_symptoms_strong": 0.25,
            "better_medication": 0.15,
            "worse_medication": 0.15,
            "better_symptoms": 0.15,
            "worse_symptoms": 0.15,
            "fewer_symptoms": 0.10,
            "more_symptoms": 0.10,
            "worse_side_effects": 0.15,
            "better_side_effects": 0.15,
        }
        raw_confidence = sum(weight_map.get(s, 0.05) for s in signals)

        # Synergy bonus: multiple strong directional signals same polarity
        strong_positives = sum(1 for s in signals if s.endswith("_strong") and s.startswith("better"))
        strong_negatives = sum(1 for s in signals if s.endswith("_strong") and s.startswith("worse"))
        if strong_positives >= 2 or strong_negatives >= 2:
            raw_confidence += 0.15

        # Floor adjustments
        if status != "same" and raw_confidence < 0.4:
            raw_confidence = 0.45
        elif status == "same" and raw_confidence == 0.0 and (positives or negatives):
            raw_confidence = 0.12  # slight floor for mixed/weak signals

        confidence = min(1.0, round(raw_confidence, 2))

        rationale_parts: List[str] = []
        mapping = {
            "better_medication_strong": "Medication effectiveness greatly improved",
            "better_medication": "Medication effectiveness improved",
            "worse_medication_strong": "Medication effectiveness greatly declined",
            "worse_medication": "Medication effectiveness declined",
            "better_symptoms_strong": "Symptom severity significantly decreased",
            "better_symptoms": "Symptom severity decreased",
            "worse_symptoms_strong": "Symptom severity significantly increased",
            "worse_symptoms": "Symptom severity increased",
            "fewer_symptoms": "Fewer symptoms logged",
            "more_symptoms": "More symptoms logged",
            "worse_side_effects": "Side effects worsened",
            "better_side_effects": "Side effects improved",
        }
        for s in signals:
            if s in mapping:
                rationale_parts.append(mapping[s])
        if not rationale_parts:
            rationale_parts.append("No strong change indicators")
        rationale = f"Overall feel is {status}. " + "; ".join(rationale_parts)
        return status, confidence, rationale


# Example usage and testing
if __name__ == "__main__":
    # This would typically be used in a FastAPI dependency injection context
    print("✅ FeelVsYesterdayService minimal implementation ready")