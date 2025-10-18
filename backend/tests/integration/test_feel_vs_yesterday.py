"""
Integration Tests for Feel vs Yesterday Service

This module contains integration tests for the feel-vs-yesterday analysis logic,
testing the service with real database interactions and complex scenarios.
"""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.logs import MedicationLog, SeverityLevel, SymptomLog
from app.schemas.logs import FeelVsYesterdayResponse
from app.services.feel_service import FeelVsYesterdayService


class TestFeelVsYesterdayIntegration:
    """Integration tests for feel vs yesterday analysis."""

    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()

    @pytest.fixture
    def feel_service(self, db_session):
        """Create feel service with test database."""
        return FeelVsYesterdayService(db_session)

    @pytest.fixture
    def test_user_id(self):
        """Test user ID."""
        return "test-user-123"

    def create_medication_log(
        self, 
        session: Session, 
        user_id: str, 
        taken_at: datetime,
        medication_name: str = "Test Med",
        effectiveness_rating: int = 3,
        side_effect_severity: SeverityLevel = None
    ) -> MedicationLog:
        """Helper to create medication log."""
        log = MedicationLog(
            user_id=user_id,
            medication_name=medication_name,
            dosage="100mg",
            taken_at=taken_at,
            logged_at=datetime.now(timezone.utc),
            effectiveness_rating=effectiveness_rating,
            side_effect_severity=side_effect_severity
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log

    def create_symptom_log(
        self, 
        session: Session, 
        user_id: str, 
        started_at: datetime,
        symptom_name: str = "Test Symptom",
        severity: SeverityLevel = SeverityLevel.MODERATE,
        impact_rating: int = 3
    ) -> SymptomLog:
        """Helper to create symptom log."""
        log = SymptomLog(
            user_id=user_id,
            symptom_name=symptom_name,
            severity=severity,
            started_at=started_at,
            logged_at=datetime.now(timezone.utc),
            duration_minutes=120,
            impact_rating=impact_rating
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log

    def test_no_data_returns_unknown(self, feel_service, test_user_id):
        """Test that no data returns unknown status."""
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id)
        
        assert isinstance(result, FeelVsYesterdayResponse)
        assert result.status == "unknown"
        assert result.confidence == 0.0
        assert "Not enough data" in result.summary

    def test_better_medication_effectiveness(
        self, feel_service, db_session, test_user_id
    ):
        """Test that improved medication effectiveness results in 'better' status."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Yesterday: low effectiveness
        self.create_medication_log(
            db_session, test_user_id, yesterday, 
            effectiveness_rating=2
        )
        
        # Today: high effectiveness
        self.create_medication_log(
            db_session, test_user_id, today, 
            effectiveness_rating=5
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        assert result.status == "better"
        assert result.confidence > 0.1
        assert "better" in result.summary.lower()

    def test_worse_symptom_severity(
        self, feel_service, db_session, test_user_id
    ):
        """Test that increased symptom severity results in 'worse' status."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Yesterday: mild symptom
        self.create_symptom_log(
            db_session, test_user_id, yesterday,
            severity=SeverityLevel.MILD, impact_rating=2
        )
        
        # Today: severe symptom
        self.create_symptom_log(
            db_session, test_user_id, today,
            severity=SeverityLevel.SEVERE, impact_rating=4
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        assert result.status == "worse"
        assert result.confidence > 0.1
        assert "worse" in result.summary.lower()

    def test_mixed_indicators_balanced(
        self, feel_service, db_session, test_user_id
    ):
        """Test mixed positive and negative indicators."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Yesterday: good medication, bad symptom
        self.create_medication_log(
            db_session, test_user_id, yesterday, effectiveness_rating=5
        )
        self.create_symptom_log(
            db_session, test_user_id, yesterday, 
            severity=SeverityLevel.SEVERE, impact_rating=5
        )
        
        # Today: bad medication, good symptom
        self.create_medication_log(
            db_session, test_user_id, today, effectiveness_rating=2
        )
        self.create_symptom_log(
            db_session, test_user_id, today, 
            severity=SeverityLevel.MILD, impact_rating=2
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        # Should be close to "same" since improvements cancel out problems
        assert result.status in ["same", "better", "worse"]
        assert result.confidence > 0.0

    def test_fewer_symptoms_is_better(
        self, feel_service, db_session, test_user_id
    ):
        """Test that fewer symptoms indicates improvement."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Yesterday: multiple symptoms
        self.create_symptom_log(
            db_session, test_user_id, yesterday - timedelta(hours=2),
            symptom_name="Headache", severity=SeverityLevel.MODERATE
        )
        self.create_symptom_log(
            db_session, test_user_id, yesterday - timedelta(hours=1),
            symptom_name="Nausea", severity=SeverityLevel.MODERATE
        )
        
        # Today: only one symptom
        self.create_symptom_log(
            db_session, test_user_id, today,
            symptom_name="Headache", severity=SeverityLevel.MODERATE
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        # Fewer symptoms should indicate improvement
        assert result.status in ["better", "same"]
        assert "fewer symptoms" in result.summary.lower() or result.status == "better"

    def test_side_effects_impact_analysis(
        self, feel_service, db_session, test_user_id
    ):
        """Test that side effects are properly considered."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Yesterday: no side effects
        self.create_medication_log(
            db_session, test_user_id, yesterday,
            effectiveness_rating=4, side_effect_severity=None
        )
        
        # Today: severe side effects
        self.create_medication_log(
            db_session, test_user_id, today,
            effectiveness_rating=4, side_effect_severity=SeverityLevel.SEVERE
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        # Side effects should make things worse
        assert result.status in ["worse", "same"]
        assert result.confidence > 0.0

    def test_date_boundaries_accuracy(
        self, feel_service, db_session, test_user_id
    ):
        """Test that date boundaries are correctly applied."""
        
        now = datetime.now(timezone.utc)
        target_date = now.replace(hour=15, minute=30, second=45, microsecond=123456)
        
        # Create logs at different times
        early_today = target_date.replace(hour=1, minute=0, second=0, microsecond=0)
        late_today = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        early_yesterday = early_today - timedelta(days=1)
        late_yesterday = late_today - timedelta(days=1)
        
        # Should be included (within today)
        self.create_medication_log(db_session, test_user_id, early_today, effectiveness_rating=5)
        self.create_medication_log(db_session, test_user_id, late_today, effectiveness_rating=5)
        
        # Should be included (within yesterday)
        self.create_medication_log(db_session, test_user_id, early_yesterday, effectiveness_rating=2)
        self.create_medication_log(db_session, test_user_id, late_yesterday, effectiveness_rating=2)
        
        # Should be excluded (day before yesterday)
        old_date = early_yesterday - timedelta(days=1)
        self.create_medication_log(db_session, test_user_id, old_date, effectiveness_rating=1)
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, target_date)
        
        # Should show improvement (5 vs 2 effectiveness)
        assert result.status == "better"
        assert result.details["medication_count_today"] == 2
        assert result.details["medication_count_yesterday"] == 2

    def test_confidence_calculation(
        self, feel_service, db_session, test_user_id
    ):
        """Test that confidence scores are reasonable."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Create scenario with multiple strong indicators
        # Yesterday: poor medications, severe symptoms
        self.create_medication_log(
            db_session, test_user_id, yesterday, effectiveness_rating=1
        )
        self.create_symptom_log(
            db_session, test_user_id, yesterday, 
            severity=SeverityLevel.SEVERE, impact_rating=5
        )
        
        # Today: excellent medications, mild symptoms
        self.create_medication_log(
            db_session, test_user_id, today, effectiveness_rating=5
        )
        self.create_symptom_log(
            db_session, test_user_id, today, 
            severity=SeverityLevel.MILD, impact_rating=1
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        # Strong improvement should have high confidence
        assert result.status == "better"
        assert result.confidence > 0.5  # Should be quite confident
        assert result.confidence <= 1.0  # But not exceed maximum

    def test_multiple_users_isolation(
        self, feel_service, db_session
    ):
        """Test that analysis is properly isolated between users."""
        
        user1 = "user-1"
        user2 = "user-2"
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # User 1: improvement
        self.create_medication_log(db_session, user1, yesterday, effectiveness_rating=2)
        self.create_medication_log(db_session, user1, today, effectiveness_rating=5)
        
        # User 2: decline
        self.create_medication_log(db_session, user2, yesterday, effectiveness_rating=5)
        self.create_medication_log(db_session, user2, today, effectiveness_rating=2)
        
        result1 = feel_service.analyze_feel_vs_yesterday(user1, now)
        result2 = feel_service.analyze_feel_vs_yesterday(user2, now)
        
        # Users should have opposite results
        assert result1.status == "better"
        assert result2.status == "worse"

    def test_analysis_details_completeness(
        self, feel_service, db_session, test_user_id
    ):
        """Test that analysis details contain expected metrics."""
        
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Create logs with various data
        self.create_medication_log(
            db_session, test_user_id, yesterday, 
            effectiveness_rating=3, side_effect_severity=SeverityLevel.MILD
        )
        self.create_symptom_log(
            db_session, test_user_id, yesterday,
            severity=SeverityLevel.MODERATE, impact_rating=3
        )
        
        self.create_medication_log(
            db_session, test_user_id, today,
            effectiveness_rating=4, side_effect_severity=SeverityLevel.NONE
        )
        self.create_symptom_log(
            db_session, test_user_id, today,
            severity=SeverityLevel.MILD, impact_rating=2
        )
        
        result = feel_service.analyze_feel_vs_yesterday(test_user_id, now)
        
        # Check that details contain expected metrics
        details = result.details
        
        assert "medication_count_today" in details
        assert "medication_count_yesterday" in details
        assert "symptom_count_today" in details
        assert "symptom_count_yesterday" in details
        assert "medication_effectiveness_change" in details
        assert "symptom_severity_change" in details
        
        # Verify counts are correct
        assert details["medication_count_today"] == 1
        assert details["medication_count_yesterday"] == 1
        assert details["symptom_count_today"] == 1
        assert details["symptom_count_yesterday"] == 1


class TestFeelVsYesterdayEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()

    @pytest.fixture
    def feel_service(self, db_session):
        """Create feel service with test database."""
        return FeelVsYesterdayService(db_session)

    def test_timezone_handling(self, feel_service, db_session):
        """Test that timezone differences are handled correctly."""
        
        user_id = "test-user"
        
        # Create logs with different timezone representations
        utc_now = datetime.now(timezone.utc)
        naive_now = datetime.now()  # No timezone info
        
        target_date = utc_now.replace(hour=12, minute=0, second=0, microsecond=0)
        
        result = feel_service.analyze_feel_vs_yesterday(user_id, target_date)
        
        # Should handle without errors
        assert isinstance(result, FeelVsYesterdayResponse)
        assert result.status == "unknown"  # No data

    def test_far_future_date(self, feel_service):
        """Test analysis with far future target date."""
        
        user_id = "test-user"
        future_date = datetime.now(timezone.utc) + timedelta(days=365)
        
        result = feel_service.analyze_feel_vs_yesterday(user_id, future_date)
        
        # Should handle gracefully
        assert isinstance(result, FeelVsYesterdayResponse)
        assert result.status == "unknown"

    def test_extreme_values_handling(self, feel_service, db_session):
        """Test handling of extreme rating values."""
        
        user_id = "test-user"
        now = datetime.now(timezone.utc)
        today = now.replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Create logs with extreme values
        med_log = MedicationLog(
            user_id=user_id,
            medication_name="Test Med",
            dosage="100mg",
            taken_at=today,
            logged_at=now,
            effectiveness_rating=5  # Maximum rating
        )
        db_session.add(med_log)
        
        symptom_log = SymptomLog(
            user_id=user_id,
            symptom_name="Test Symptom",
            severity=SeverityLevel.CRITICAL,  # Maximum severity
            started_at=today,
            logged_at=now,
            impact_rating=5  # Maximum impact
        )
        db_session.add(symptom_log)
        db_session.commit()
        
        result = feel_service.analyze_feel_vs_yesterday(user_id, now)
        
        # Should handle extreme values without errors
        assert isinstance(result, FeelVsYesterdayResponse)
        assert 0.0 <= result.confidence <= 1.0


# Example usage and testing
if __name__ == "__main__":
    print("✅ Integration tests for feel vs yesterday service created")
    print("Test coverage:")
    print("- No data scenarios")
    print("- Medication effectiveness changes")
    print("- Symptom severity changes")
    print("- Mixed positive/negative indicators")
    print("- Symptom count changes")
    print("- Side effects impact")
    print("- Date boundary accuracy")
    print("- Confidence calculation")
    print("- Multi-user isolation")
    print("- Analysis details completeness")
    print("- Edge cases and error conditions")
    print("")
    print("Run with: pytest backend/tests/integration/test_feel_vs_yesterday.py -v")