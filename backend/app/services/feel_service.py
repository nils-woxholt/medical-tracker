"""
Feel vs Yesterday Service

This service implements the logic to compare today's medication and symptom
logs with yesterday's to determine if the user is feeling better, same, or worse.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.logs import MedicationLog, SeverityLevel, SymptomLog
from app.schemas.logs import FeelVsYesterdayResponse

logger = structlog.get_logger(__name__)


class FeelVsYesterdayService:
    """
    Service for analyzing how the user feels today compared to yesterday.
    
    This service analyzes medication effectiveness, symptom severity, and overall
    patterns to provide a meaningful comparison between today and yesterday.
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def analyze_feel_vs_yesterday(self, user_id: str, target_date: Optional[datetime] = None) -> FeelVsYesterdayResponse:
        """
        Analyze how the user feels today compared to yesterday.
        
        Args:
            user_id: ID of the user to analyze
            target_date: Date to compare against (defaults to today)
            
        Returns:
            FeelVsYesterdayResponse with analysis results
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc)
            
        # Get date boundaries
        today_start, today_end = self._get_date_boundaries(target_date)
        yesterday_start, yesterday_end = self._get_date_boundaries(target_date - timedelta(days=1))
        
        logger.info(
            "Analyzing feel vs yesterday",
            user_id=user_id,
            target_date=target_date.date().isoformat(),
            today_range=(today_start.isoformat(), today_end.isoformat()),
            yesterday_range=(yesterday_start.isoformat(), yesterday_end.isoformat())
        )

        # Get logs for both days
        today_medications = self._get_medication_logs(user_id, today_start, today_end)
        yesterday_medications = self._get_medication_logs(user_id, yesterday_start, yesterday_end)
        
        today_symptoms = self._get_symptom_logs(user_id, today_start, today_end)
        yesterday_symptoms = self._get_symptom_logs(user_id, yesterday_start, yesterday_end)

        # Perform analysis
        analysis = self._analyze_changes(
            today_medications, yesterday_medications,
            today_symptoms, yesterday_symptoms
        )

        # Generate response
        status, confidence = self._determine_status_and_confidence(analysis)
        summary = self._generate_summary(analysis, status)

        return FeelVsYesterdayResponse(
            status=status,
            confidence=confidence,
            summary=summary,
            details=analysis,
            date_compared=(target_date - timedelta(days=1)).date().isoformat()
        )

    def _get_date_boundaries(self, date: datetime) -> Tuple[datetime, datetime]:
        """Get start and end boundaries for a given date."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        return start, end

    def _get_medication_logs(self, user_id: str, start: datetime, end: datetime) -> List[MedicationLog]:
        """Get medication logs for a date range."""
        return (
            self.db.query(MedicationLog)
            .filter(
                and_(
                    MedicationLog.user_id == user_id,
                    MedicationLog.taken_at >= start,
                    MedicationLog.taken_at <= end
                )
            )
            .all()
        )

    def _get_symptom_logs(self, user_id: str, start: datetime, end: datetime) -> List[SymptomLog]:
        """Get symptom logs for a date range."""
        return (
            self.db.query(SymptomLog)
            .filter(
                and_(
                    SymptomLog.user_id == user_id,
                    SymptomLog.started_at >= start,
                    SymptomLog.started_at <= end
                )
            )
            .all()
        )

    def _analyze_changes(
        self, 
        today_medications: List[MedicationLog], 
        yesterday_medications: List[MedicationLog],
        today_symptoms: List[SymptomLog], 
        yesterday_symptoms: List[SymptomLog]
    ) -> Dict:
        """
        Analyze changes between today and yesterday.
        
        Returns a dictionary with various analysis metrics.
        """
        analysis = {}

        # Medication analysis
        analysis.update(self._analyze_medication_changes(today_medications, yesterday_medications))
        
        # Symptom analysis
        analysis.update(self._analyze_symptom_changes(today_symptoms, yesterday_symptoms))
        
        # Overall counts
        analysis['medication_count_today'] = len(today_medications)
        analysis['medication_count_yesterday'] = len(yesterday_medications)
        analysis['symptom_count_today'] = len(today_symptoms)
        analysis['symptom_count_yesterday'] = len(yesterday_symptoms)
        
        # Count changes
        analysis['medication_count_change'] = len(today_medications) - len(yesterday_medications)
        analysis['symptom_count_change'] = len(today_symptoms) - len(yesterday_symptoms)

        return analysis

    def _analyze_medication_changes(
        self, 
        today_meds: List[MedicationLog], 
        yesterday_meds: List[MedicationLog]
    ) -> Dict:
        """Analyze changes in medication effectiveness and side effects."""
        
        # Calculate average effectiveness
        today_effectiveness = self._calculate_average_effectiveness(today_meds)
        yesterday_effectiveness = self._calculate_average_effectiveness(yesterday_meds)
        
        effectiveness_change = today_effectiveness - yesterday_effectiveness if both_exist(today_effectiveness, yesterday_effectiveness) else 0

        # Calculate side effect severity changes
        today_side_effects = self._calculate_average_side_effect_severity(today_meds)
        yesterday_side_effects = self._calculate_average_side_effect_severity(yesterday_meds)
        
        side_effect_change = today_side_effects - yesterday_side_effects if both_exist(today_side_effects, yesterday_side_effects) else 0

        return {
            'medication_effectiveness_today': today_effectiveness,
            'medication_effectiveness_yesterday': yesterday_effectiveness,
            'medication_effectiveness_change': effectiveness_change,
            'medication_side_effects_today': today_side_effects,
            'medication_side_effects_yesterday': yesterday_side_effects,
            'medication_side_effects_change': side_effect_change
        }

    def _analyze_symptom_changes(
        self, 
        today_symptoms: List[SymptomLog], 
        yesterday_symptoms: List[SymptomLog]
    ) -> Dict:
        """Analyze changes in symptom severity and impact."""
        
        # Calculate average severity
        today_severity = self._calculate_average_symptom_severity(today_symptoms)
        yesterday_severity = self._calculate_average_symptom_severity(yesterday_symptoms)
        
        severity_change = today_severity - yesterday_severity if both_exist(today_severity, yesterday_severity) else 0

        # Calculate average impact
        today_impact = self._calculate_average_symptom_impact(today_symptoms)
        yesterday_impact = self._calculate_average_symptom_impact(yesterday_symptoms)
        
        impact_change = today_impact - yesterday_impact if both_exist(today_impact, yesterday_impact) else 0

        return {
            'symptom_severity_today': today_severity,
            'symptom_severity_yesterday': yesterday_severity,
            'symptom_severity_change': severity_change,
            'symptom_impact_today': today_impact,
            'symptom_impact_yesterday': yesterday_impact,
            'symptom_impact_change': impact_change
        }

    def _calculate_average_effectiveness(self, medications: List[MedicationLog]) -> Optional[float]:
        """Calculate average effectiveness rating for medications."""
        ratings = [med.effectiveness_rating for med in medications if med.effectiveness_rating is not None]
        return sum(ratings) / len(ratings) if ratings else None

    def _calculate_average_side_effect_severity(self, medications: List[MedicationLog]) -> Optional[float]:
        """Calculate average side effect severity for medications."""
        severities = [
            self._severity_to_numeric(med.side_effect_severity) 
            for med in medications 
            if med.side_effect_severity is not None
        ]
        return sum(severities) / len(severities) if severities else None

    def _calculate_average_symptom_severity(self, symptoms: List[SymptomLog]) -> Optional[float]:
        """Calculate average severity for symptoms."""
        severities = [self._severity_to_numeric(symptom.severity) for symptom in symptoms]
        return sum(severities) / len(severities) if severities else None

    def _calculate_average_symptom_impact(self, symptoms: List[SymptomLog]) -> Optional[float]:
        """Calculate average impact rating for symptoms."""
        impacts = [symptom.impact_rating for symptom in symptoms if symptom.impact_rating is not None]
        return sum(impacts) / len(impacts) if impacts else None

    def _severity_to_numeric(self, severity: SeverityLevel) -> float:
        """Convert severity enum to numeric value for calculations."""
        severity_map = {
            SeverityLevel.NONE: 0.0,
            SeverityLevel.MILD: 1.0,
            SeverityLevel.MODERATE: 2.0,
            SeverityLevel.SEVERE: 3.0,
            SeverityLevel.CRITICAL: 4.0
        }
        return severity_map.get(severity, 0.0)

    def _determine_status_and_confidence(self, analysis: Dict) -> Tuple[str, float]:
        """
        Determine overall status and confidence based on analysis.
        
        Returns:
            Tuple of (status, confidence) where status is 'better'|'same'|'worse'|'unknown'
            and confidence is a float between 0.0 and 1.0
        """
        
        # Start with unknown status and low confidence
        status = "unknown"
        confidence = 0.0
        
        # Check if we have enough data to make a determination
        has_med_data = analysis.get('medication_count_today', 0) > 0 or analysis.get('medication_count_yesterday', 0) > 0
        has_symptom_data = analysis.get('symptom_count_today', 0) > 0 or analysis.get('symptom_count_yesterday', 0) > 0
        
        if not (has_med_data or has_symptom_data):
            return "unknown", 0.0

        # Calculate improvement score (positive = better, negative = worse)
        improvement_score = 0.0
        factors_count = 0

        # Medication effectiveness (positive change is good)
        if analysis.get('medication_effectiveness_change') is not None:
            improvement_score += analysis['medication_effectiveness_change'] * 0.3
            factors_count += 1

        # Medication side effects (negative change is good)
        if analysis.get('medication_side_effects_change') is not None:
            improvement_score -= analysis['medication_side_effects_change'] * 0.2
            factors_count += 1

        # Symptom severity (negative change is good)
        if analysis.get('symptom_severity_change') is not None:
            improvement_score -= analysis['symptom_severity_change'] * 0.4
            factors_count += 1

        # Symptom impact (negative change is good)
        if analysis.get('symptom_impact_change') is not None:
            improvement_score -= analysis['symptom_impact_change'] * 0.3
            factors_count += 1

        # Symptom count (fewer symptoms is generally better)
        symptom_count_change = analysis.get('symptom_count_change', 0)
        if symptom_count_change != 0:
            improvement_score -= symptom_count_change * 0.2
            factors_count += 1

        if factors_count == 0:
            return "unknown", 0.0

        # Determine status based on improvement score
        if improvement_score > 0.1:
            status = "better"
        elif improvement_score < -0.1:
            status = "worse"
        else:
            status = "same"

        # Calculate confidence based on number of factors and magnitude of change
        confidence = min(0.95, max(0.1, (factors_count / 5) * (1 - 1 / (1 + abs(improvement_score)))))

        return status, confidence

    def _generate_summary(self, analysis: Dict, status: str) -> str:
        """Generate human-readable summary of the analysis."""
        
        if status == "unknown":
            return "Not enough data to compare with yesterday"

        # Build summary components
        components = []

        if status == "better":
            components.append("Feeling better today")
        elif status == "worse":
            components.append("Feeling worse today")
        else:
            components.append("Feeling about the same as yesterday")

        # Add specific details
        details = []
        
        effectiveness_change = analysis.get('medication_effectiveness_change', 0)
        if effectiveness_change > 0.5:
            details.append("medications were more effective")
        elif effectiveness_change < -0.5:
            details.append("medications were less effective")

        severity_change = analysis.get('symptom_severity_change', 0)
        if severity_change < -0.5:
            details.append("symptoms were milder")
        elif severity_change > 0.5:
            details.append("symptoms were more severe")

        symptom_count_change = analysis.get('symptom_count_change', 0)
        if symptom_count_change < 0:
            details.append("fewer symptoms occurred")
        elif symptom_count_change > 0:
            details.append("more symptoms occurred")

        if details:
            components.append(" - " + ", ".join(details))

        return "".join(components)


def both_exist(val1, val2) -> bool:
    """Check if both values exist (are not None)."""
    return val1 is not None and val2 is not None


# Example usage and testing
if __name__ == "__main__":
    # This would typically be used in a FastAPI dependency injection context
    print("✅ FeelVsYesterdayService created successfully")
    print("Service provides methods:")
    print("- analyze_feel_vs_yesterday(): Main analysis method")
    print("- _get_date_boundaries(): Date range calculation")
    print("- _analyze_changes(): Change analysis")
    print("- _determine_status_and_confidence(): Status determination")
    print("- _generate_summary(): Human-readable summary generation")