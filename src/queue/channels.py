"""
Redis queue channel definitions for TutorMax.
"""
from enum import Enum


class QueueChannels(str, Enum):
    """
    Message queue channels for different data types.

    Each channel handles a specific type of data in the processing pipeline:
    - TUTORS: Tutor profile data and updates
    - SESSIONS: Tutoring session records
    - FEEDBACK: Student feedback data
    """

    TUTORS = "tutormax:tutors"
    SESSIONS = "tutormax:sessions"
    FEEDBACK = "tutormax:feedback"

    # Dead letter queue for failed messages
    DEAD_LETTER = "tutormax:dead_letter"

    @classmethod
    def all_channels(cls) -> list[str]:
        """Get all channel names as a list."""
        return [channel.value for channel in cls if channel != cls.DEAD_LETTER]

    @classmethod
    def get_retry_channel(cls, channel: str) -> str:
        """Get retry channel name for a given channel."""
        return f"{channel}:retry"

    @classmethod
    def get_processing_channel(cls, channel: str) -> str:
        """Get processing channel name for a given channel."""
        return f"{channel}:processing"


# Channel descriptions for documentation
CHANNEL_DESCRIPTIONS = {
    QueueChannels.TUTORS: "Tutor profile data including demographics, qualifications, and performance metrics",
    QueueChannels.SESSIONS: "Tutoring session records including duration, participants, and outcomes",
    QueueChannels.FEEDBACK: "Student feedback data including ratings, comments, and sentiment",
    QueueChannels.DEAD_LETTER: "Failed messages that exceeded retry limits",
}
