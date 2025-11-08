"""
Tutor data generator for TutorMax system.

Generates synthetic tutor profiles with realistic behavioral archetypes
and characteristics as defined in the PRD.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from enum import Enum

from faker import Faker
import numpy as np


class BehavioralArchetype(str, Enum):
    """Behavioral archetypes for tutors as defined in PRD."""
    HIGH_PERFORMER = "high_performer"
    AT_RISK = "at_risk"
    NEW_TUTOR = "new_tutor"
    STEADY = "steady"
    CHURNER = "churner"


class Subject(str, Enum):
    """Subject categories with different churn patterns."""
    # STEM subjects - Lower churn (8%), higher reschedule rates
    MATHEMATICS = "Mathematics"
    ALGEBRA = "Algebra"
    CALCULUS = "Calculus"
    GEOMETRY = "Geometry"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    COMPUTER_SCIENCE = "Computer Science"

    # Language/Writing - Medium churn (12%), higher first-session failure
    ENGLISH = "English"
    WRITING = "Writing"
    LITERATURE = "Literature"
    SPANISH = "Spanish"
    FRENCH = "French"

    # Test Prep - Higher churn (15%), high performance variance
    SAT_PREP = "SAT Prep"
    ACT_PREP = "ACT Prep"
    AP_TEST_PREP = "AP Test Prep"
    GRE_PREP = "GRE Prep"


class TutorGenerator:
    """
    Generates synthetic tutor profiles with realistic characteristics.

    Implements behavioral archetypes:
    - High Performer (30%): Consistent, low reschedules, high ratings
    - At-Risk (20%): Declining engagement, increasing reschedules
    - New Tutor (25%): <30 days tenure, variable performance
    - Steady (20%): Average metrics, stable
    - Churner (5%): Exhibiting churn signals
    """

    # Archetype distribution (must sum to 1.0)
    ARCHETYPE_DISTRIBUTION = {
        BehavioralArchetype.HIGH_PERFORMER: 0.30,
        BehavioralArchetype.AT_RISK: 0.20,
        BehavioralArchetype.NEW_TUTOR: 0.25,
        BehavioralArchetype.STEADY: 0.20,
        BehavioralArchetype.CHURNER: 0.05,
    }

    # Subject type distribution
    SUBJECT_TYPES = {
        "STEM": [Subject.MATHEMATICS, Subject.ALGEBRA, Subject.CALCULUS,
                 Subject.GEOMETRY, Subject.PHYSICS, Subject.CHEMISTRY,
                 Subject.BIOLOGY, Subject.COMPUTER_SCIENCE],
        "Language": [Subject.ENGLISH, Subject.WRITING, Subject.LITERATURE,
                     Subject.SPANISH, Subject.FRENCH],
        "TestPrep": [Subject.SAT_PREP, Subject.ACT_PREP, Subject.AP_TEST_PREP,
                     Subject.GRE_PREP],
    }

    EDUCATION_LEVELS = [
        "High School",
        "Some College",
        "Bachelor's Degree",
        "Master's Degree",
        "PhD"
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the tutor generator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            np.random.seed(seed)

        self.fake = Faker()
        if seed is not None:
            self.fake.seed_instance(seed)

        self._tutor_counter = 0

    def generate_tutor(
        self,
        tutor_id: Optional[str] = None,
        archetype: Optional[BehavioralArchetype] = None,
        onboarding_date: Optional[datetime] = None
    ) -> Dict:
        """
        Generate a single tutor profile.

        Args:
            tutor_id: Optional custom tutor ID
            archetype: Optional specific archetype to assign
            onboarding_date: Optional onboarding date

        Returns:
            Dict containing tutor profile data
        """
        self._tutor_counter += 1

        # Generate tutor ID
        if tutor_id is None:
            tutor_id = f"tutor_{self._tutor_counter:05d}"

        # Assign archetype based on distribution
        if archetype is None:
            archetype = self._select_archetype()

        # Generate onboarding date
        if onboarding_date is None:
            onboarding_date = self._generate_onboarding_date(archetype)

        # Calculate tenure
        tenure_days = (datetime.now() - onboarding_date).days

        # Generate subject expertise (1-3 subjects)
        subject_count = random.randint(1, 3)
        subjects = self._generate_subjects(subject_count)

        # Determine subject type for churn patterns
        subject_type = self._determine_subject_type(subjects)

        # Generate baseline sessions per week based on archetype
        baseline_sessions = self._generate_baseline_sessions(archetype)

        # Generate demographics
        age = random.randint(22, 65)
        education_level = self._generate_education_level(age)

        tutor_data = {
            "tutor_id": tutor_id,
            "name": self.fake.name(),
            "email": self.fake.email(),
            "age": age,
            "location": self.fake.city(),
            "education_level": education_level,
            "subjects": [s.value for s in subjects],
            "subject_type": subject_type,
            "onboarding_date": onboarding_date.isoformat(),
            "tenure_days": tenure_days,
            "behavioral_archetype": archetype.value,
            "baseline_sessions_per_week": baseline_sessions,
            "status": "active",
            "created_at": onboarding_date.isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        return tutor_data

    def generate_tutors(
        self,
        count: int,
        start_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Generate multiple tutor profiles.

        Args:
            count: Number of tutors to generate
            start_date: Earliest possible onboarding date

        Returns:
            List of tutor profile dictionaries
        """
        tutors = []
        for _ in range(count):
            tutor = self.generate_tutor()
            tutors.append(tutor)

        return tutors

    def _select_archetype(self) -> BehavioralArchetype:
        """Select a behavioral archetype based on distribution."""
        archetypes = list(self.ARCHETYPE_DISTRIBUTION.keys())
        weights = list(self.ARCHETYPE_DISTRIBUTION.values())
        return random.choices(archetypes, weights=weights, k=1)[0]

    def _generate_onboarding_date(
        self,
        archetype: BehavioralArchetype
    ) -> datetime:
        """
        Generate onboarding date based on archetype.

        New tutors have tenure <30 days, others vary.
        """
        if archetype == BehavioralArchetype.NEW_TUTOR:
            # New tutors: 1-29 days ago
            days_ago = random.randint(1, 29)
        else:
            # Other tutors: 30-730 days ago (up to 2 years)
            days_ago = random.randint(30, 730)

        return datetime.now() - timedelta(days=days_ago)

    def _generate_subjects(self, count: int) -> List[Subject]:
        """Generate subject expertise for tutor."""
        # Prefer subjects from the same category
        subject_type = random.choice(list(self.SUBJECT_TYPES.keys()))
        available_subjects = self.SUBJECT_TYPES[subject_type]

        # Select subjects
        selected_count = min(count, len(available_subjects))
        subjects = random.sample(available_subjects, selected_count)

        return subjects

    def _determine_subject_type(self, subjects: List[Subject]) -> str:
        """Determine primary subject type from subject list."""
        for subject_type, subject_list in self.SUBJECT_TYPES.items():
            if any(s in subject_list for s in subjects):
                return subject_type
        return "STEM"  # Default

    def _generate_baseline_sessions(
        self,
        archetype: BehavioralArchetype
    ) -> int:
        """
        Generate baseline sessions per week based on archetype.

        PRD specifies: mean=15, range=5-30
        """
        if archetype == BehavioralArchetype.HIGH_PERFORMER:
            # High performers: above average (18-30)
            return random.randint(18, 30)
        elif archetype == BehavioralArchetype.CHURNER:
            # Churners: declining, currently low (5-12)
            return random.randint(5, 12)
        elif archetype == BehavioralArchetype.AT_RISK:
            # At-risk: below average (8-15)
            return random.randint(8, 15)
        elif archetype == BehavioralArchetype.NEW_TUTOR:
            # New tutors: variable (5-20)
            return random.randint(5, 20)
        else:  # STEADY
            # Steady: average (12-18)
            return random.randint(12, 18)

    def _generate_education_level(self, age: int) -> str:
        """Generate education level correlated with age."""
        if age < 25:
            # Younger tutors: mostly college students or recent grads
            return random.choice([
                "Some College",
                "Bachelor's Degree",
            ])
        elif age < 35:
            # Mid-age: mix of bachelor's and master's
            return random.choice([
                "Bachelor's Degree",
                "Bachelor's Degree",
                "Master's Degree",
            ])
        else:
            # Older tutors: higher degrees more likely
            return random.choice([
                "Bachelor's Degree",
                "Master's Degree",
                "Master's Degree",
                "PhD",
            ])

    def get_archetype_stats(self, tutors: List[Dict]) -> Dict:
        """
        Calculate archetype distribution statistics.

        Args:
            tutors: List of generated tutor profiles

        Returns:
            Dict with archetype counts and percentages
        """
        archetype_counts = {}
        for tutor in tutors:
            archetype = tutor["behavioral_archetype"]
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1

        total = len(tutors)
        stats = {
            archetype: {
                "count": count,
                "percentage": round(count / total * 100, 2)
            }
            for archetype, count in archetype_counts.items()
        }

        return stats
