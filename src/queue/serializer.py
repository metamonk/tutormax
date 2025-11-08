"""
Message serialization and deserialization utilities.
"""
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


class MessageSerializer:
    """
    Handles message serialization/deserialization with metadata.

    Message format:
    {
        "id": "unique-message-id",
        "timestamp": "2024-01-01T12:00:00",
        "channel": "tutormax:tutors",
        "data": {...},
        "metadata": {...},
        "checksum": "sha256-hash"
    }
    """

    @staticmethod
    def serialize(
        channel: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Serialize data to JSON message format.

        Args:
            channel: Queue channel name
            data: Message payload data
            metadata: Optional metadata (e.g., retry count, source)

        Returns:
            JSON string ready for publishing
        """
        message = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "data": data,
            "metadata": metadata or {},
        }

        # Add checksum for data integrity
        data_str = json.dumps(message["data"], sort_keys=True)
        message["checksum"] = hashlib.sha256(data_str.encode()).hexdigest()

        return json.dumps(message)

    @staticmethod
    def deserialize(message: str) -> Dict[str, Any]:
        """
        Deserialize JSON message and validate checksum.

        Args:
            message: JSON string message

        Returns:
            Deserialized message dictionary

        Raises:
            ValueError: If message format is invalid or checksum doesn't match
        """
        try:
            msg_dict = json.loads(message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON message: {e}")

        # Validate required fields
        required_fields = ["id", "timestamp", "channel", "data", "checksum"]
        missing_fields = [f for f in required_fields if f not in msg_dict]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate checksum
        data_str = json.dumps(msg_dict["data"], sort_keys=True)
        expected_checksum = hashlib.sha256(data_str.encode()).hexdigest()
        if msg_dict["checksum"] != expected_checksum:
            raise ValueError("Message checksum validation failed")

        return msg_dict

    @staticmethod
    def extract_data(message: str) -> Dict[str, Any]:
        """
        Deserialize message and return only the data payload.

        Args:
            message: JSON string message

        Returns:
            Message data payload
        """
        msg_dict = MessageSerializer.deserialize(message)
        return msg_dict["data"]

    @staticmethod
    def extract_metadata(message: str) -> Dict[str, Any]:
        """
        Deserialize message and return metadata.

        Args:
            message: JSON string message

        Returns:
            Message metadata dictionary
        """
        msg_dict = MessageSerializer.deserialize(message)
        return {
            "id": msg_dict["id"],
            "timestamp": msg_dict["timestamp"],
            "channel": msg_dict["channel"],
            "metadata": msg_dict.get("metadata", {}),
        }
