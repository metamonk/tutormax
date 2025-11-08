"""
Queue monitoring script for TutorMax.

Displays real-time statistics about queue health, message counts,
and worker performance.

Usage:
    python examples/monitor_queues.py [--interval SECONDS]
"""
import argparse
import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.queue import (
    get_redis_client,
    MessagePublisher,
    QueueChannels,
    shutdown_redis_client
)


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def display_header():
    """Display monitoring header."""
    print("=" * 80)
    print("TutorMax Queue Monitor".center(80))
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def display_redis_health(client):
    """Display Redis health information."""
    health = client.health_check()

    print("\n┌─ Redis Health " + "─" * 64)
    print(f"│ Status: {health.get('status', 'unknown').upper()}")

    if health['status'] == 'healthy':
        print(f"│ Version: {health.get('redis_version', 'unknown')}")
        print(f"│ Connected Clients: {health.get('connected_clients', 0)}")
        print(f"│ Memory Usage: {health.get('used_memory_human', 'unknown')}")
        print(f"│ Uptime: {health.get('uptime_in_seconds', 0)} seconds")
    else:
        print(f"│ Error: {health.get('error', 'Unknown error')}")

    print("└" + "─" * 79)


def display_queue_stats(publisher):
    """Display queue statistics."""
    print("\n┌─ Queue Statistics " + "─" * 60)
    print("│")
    print(f"│ {'Channel':<30} {'Messages':>15} {'Status':>15}")
    print("│ " + "─" * 77)

    total_messages = 0

    for channel in QueueChannels.all_channels():
        length = publisher.get_stream_length(channel)
        total_messages += length

        # Determine status
        if length == 0:
            status = "✓ Empty"
        elif length < 100:
            status = "✓ Normal"
        elif length < 1000:
            status = "⚠ High"
        else:
            status = "⚠ Very High"

        channel_name = channel.split(':')[1] if ':' in channel else channel
        print(f"│ {channel_name:<30} {length:>15,} {status:>15}")

    print("│ " + "─" * 77)
    print(f"│ {'TOTAL':<30} {total_messages:>15,}")
    print("│")

    # Check dead letter queue
    dlq_length = publisher.get_stream_length(QueueChannels.DEAD_LETTER)
    if dlq_length > 0:
        print(f"│ ⚠ Dead Letter Queue: {dlq_length} failed messages")

    print("└" + "─" * 79)


def display_channel_details(publisher, channel):
    """Display detailed information for a channel."""
    info = publisher.get_stream_info(channel)

    print(f"\n┌─ Channel Details: {channel} " + "─" * (78 - len(channel) - 20))
    print(f"│ Length: {info.get('length', 0)} messages")
    print(f"│ Consumer Groups: {info.get('groups', 0)}")

    first_entry = info.get('first_entry')
    if first_entry:
        print(f"│ First Message ID: {first_entry[0]}")

    last_entry = info.get('last_entry')
    if last_entry:
        print(f"│ Last Message ID: {last_entry[0]}")

    print("└" + "─" * 79)


def monitor(interval=5, show_details=False):
    """
    Run monitoring loop.

    Args:
        interval: Update interval in seconds
        show_details: Show detailed channel information
    """
    try:
        client = get_redis_client()
        publisher = MessagePublisher(client)

        while True:
            clear_screen()
            display_header()
            display_redis_health(client)
            display_queue_stats(publisher)

            if show_details:
                for channel in QueueChannels.all_channels():
                    if publisher.get_stream_length(channel) > 0:
                        display_channel_details(publisher, channel)

            print("\n" + "─" * 80)
            print(f"Refreshing in {interval}s... (Press Ctrl+C to exit)")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")

    except Exception as e:
        print(f"\n\nError: {e}")

    finally:
        shutdown_redis_client()


def show_snapshot():
    """Show a single snapshot of queue status."""
    try:
        client = get_redis_client()
        publisher = MessagePublisher(client)

        display_header()
        display_redis_health(client)
        display_queue_stats(publisher)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        shutdown_redis_client()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='TutorMax Queue Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Update interval in seconds (default: 5)'
    )

    parser.add_argument(
        '--details',
        action='store_true',
        help='Show detailed channel information'
    )

    parser.add_argument(
        '--snapshot',
        action='store_true',
        help='Show single snapshot and exit'
    )

    return parser.parse_args()


def main():
    """Run the monitor."""
    args = parse_args()

    if args.snapshot:
        show_snapshot()
    else:
        monitor(interval=args.interval, show_details=args.details)


if __name__ == "__main__":
    main()
