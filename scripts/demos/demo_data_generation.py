#!/usr/bin/env python3
"""
Demo script for TutorMax synthetic data generation.

Generates sample tutors, sessions, and feedback to demonstrate
the data generation engine per PRD specifications.
"""

import json
from datetime import datetime
from pathlib import Path

from src.data_generation.tutor_generator import TutorGenerator
from src.data_generation.session_generator import SessionGenerator
from src.data_generation.feedback_generator import FeedbackGenerator


def main():
    """Generate and display sample synthetic data."""

    print("=" * 70)
    print("TutorMax Synthetic Data Generation Demo")
    print("=" * 70)
    print()

    # Initialize generators with seed for reproducibility
    print("Initializing data generators...")
    tutor_gen = TutorGenerator(seed=42)
    session_gen = SessionGenerator(seed=42)
    feedback_gen = FeedbackGenerator(seed=42)
    print("✓ Generators initialized\n")

    # Generate tutors
    print("Generating tutor profiles...")
    num_tutors = 300  # Typical active tutor count
    tutors = tutor_gen.generate_tutors(count=num_tutors)
    print(f"✓ Generated {len(tutors)} tutor profiles\n")

    # Display tutor statistics
    tutor_stats = tutor_gen.get_archetype_stats(tutors)
    print("Tutor Archetype Distribution:")
    print("-" * 50)
    for archetype, stats in sorted(tutor_stats.items()):
        print(f"  {archetype:20s}: {stats['count']:3d} ({stats['percentage']:5.2f}%)")
    print()

    # Display sample tutors
    print("Sample Tutor Profiles:")
    print("-" * 50)
    for i, tutor in enumerate(tutors[:3], 1):
        print(f"\n{i}. {tutor['name']}")
        print(f"   ID: {tutor['tutor_id']}")
        print(f"   Archetype: {tutor['behavioral_archetype']}")
        print(f"   Subjects: {', '.join(tutor['subjects'])}")
        print(f"   Tenure: {tutor['tenure_days']} days")
        print(f"   Baseline sessions/week: {tutor['baseline_sessions_per_week']}")
    print()

    # Generate sessions for a day
    print("Generating daily sessions...")
    target_sessions = 3000  # PRD target: 3,000 sessions/day
    sessions = session_gen.generate_sessions_for_day(
        tutors=tutors,
        target_count=target_sessions
    )
    print(f"✓ Generated {len(sessions)} sessions\n")

    # Display session statistics
    session_stats = session_gen.get_session_stats(sessions)
    print("Session Statistics:")
    print("-" * 50)
    print(f"  Total sessions:           {session_stats['total_sessions']}")
    print(f"  First sessions:           {session_stats['first_sessions']} ({session_stats['first_session_rate']}%)")
    print(f"  Reschedule rate:          {session_stats['reschedule_rate']}%")
    print(f"  No-show rate:             {session_stats['no_show_rate']}%")
    print(f"  Late start rate (>5min):  {session_stats['late_start_rate']}%")
    print(f"  Objectives met rate:      {session_stats['objectives_met_rate']}%")
    print(f"  Avg engagement score:     {session_stats['avg_engagement_score']}")
    print()

    # Display sample sessions
    print("Sample Sessions:")
    print("-" * 50)
    for i, session in enumerate(sessions[:3], 1):
        print(f"\n{i}. Session {session['session_id'][:8]}...")
        print(f"   Tutor: {session['tutor_id']}")
        print(f"   Subject: {session['subject']}")
        print(f"   First session: {'Yes' if session['is_first_session'] else 'No'}")
        print(f"   Duration: {session['duration_minutes']} min")
        print(f"   Engagement: {session['engagement_score']:.2f}")
        print(f"   No-show: {'Yes' if session['no_show'] else 'No'}")
        if session['tutor_initiated_reschedule']:
            print(f"   ⚠️  Tutor-initiated reschedule")
    print()

    # Generate feedback
    print("Generating student feedback...")
    tutors_dict = {t["tutor_id"]: t for t in tutors}
    feedbacks = feedback_gen.generate_feedback_for_sessions(
        sessions=sessions,
        tutors=tutors_dict,
        feedback_rate=0.85  # 85% feedback rate
    )
    print(f"✓ Generated {len(feedbacks)} feedback entries\n")

    # Display feedback statistics
    feedback_stats = feedback_gen.get_feedback_stats(feedbacks)
    print("Feedback Statistics:")
    print("-" * 50)
    print(f"  Total feedback:           {feedback_stats['total_feedbacks']}")
    print(f"  Avg overall rating:       {feedback_stats['avg_overall_rating']:.2f}/5.0")
    print(f"  Poor ratings (<3):        {feedback_stats['poor_rating_count']} ({feedback_stats['poor_rating_rate']}%)")
    print(f"  First session feedback:   {feedback_stats['first_session_count']}")
    print(f"  First session avg rating: {feedback_stats['first_session_avg_rating']:.2f}/5.0")
    print(f"  Would recommend rate:     {feedback_stats['would_recommend_rate']}%")
    print(f"  Text feedback provided:   {feedback_stats['text_feedback_rate']}%")
    print()

    print("Rating Distribution:")
    for rating in range(1, 6):
        count = feedback_stats['rating_distribution'][rating]
        percentage = (count / feedback_stats['total_feedbacks'] * 100) if feedback_stats['total_feedbacks'] > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"  {rating} stars: {bar:25s} {count:4d} ({percentage:5.2f}%)")
    print()

    # Display sample feedback
    print("Sample Feedback Entries:")
    print("-" * 50)
    for i, feedback in enumerate(feedbacks[:3], 1):
        session = next(s for s in sessions if s["session_id"] == feedback["session_id"])
        print(f"\n{i}. Feedback for session {feedback['session_id'][:8]}...")
        print(f"   Overall rating: {feedback['overall_rating']}/5 ({'⭐' * feedback['overall_rating']})")
        print(f"   Subject knowledge: {feedback['subject_knowledge_rating']}/5")
        print(f"   Communication: {feedback['communication_rating']}/5")
        print(f"   Patience: {feedback['patience_rating']}/5")
        print(f"   First session: {'Yes' if feedback['is_first_session'] else 'No'}")
        if feedback.get('would_recommend') is not None:
            print(f"   Would recommend: {'Yes' if feedback['would_recommend'] else 'No'}")
        if feedback['free_text_feedback']:
            print(f"   Comment: \"{feedback['free_text_feedback']}\"")
    print()

    # Save sample data
    print("Saving sample data...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "sample_tutors.json", "w") as f:
        json.dump(tutors[:10], f, indent=2)

    with open(output_dir / "sample_sessions.json", "w") as f:
        json.dump(sessions[:50], f, indent=2)

    with open(output_dir / "sample_feedback.json", "w") as f:
        json.dump(feedbacks[:50], f, indent=2)

    print(f"✓ Sample data saved to {output_dir}/")
    print()

    # Summary
    print("=" * 70)
    print("Data Generation Summary")
    print("=" * 70)
    print(f"Tutors generated:    {len(tutors):6d}")
    print(f"Sessions generated:  {len(sessions):6d}")
    print(f"Feedback generated:  {len(feedbacks):6d}")
    print()
    print("✓ Data generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
