"""
Demo: Churn Prediction API

Demonstrates the prediction API endpoints including:
- Single tutor prediction via REST API
- Batch prediction
- Redis caching behavior
- Model information endpoint

Prerequisites:
1. Start Redis: redis-server (or via Docker)
2. Start FastAPI server: python -m src.api.main
3. Run this demo: python demos/demo_prediction_api.py
"""

import sys
from pathlib import Path
import requests
import json
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# API configuration
API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)


def check_api_health():
    """Check if API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        health = response.json()

        print("\n✅ API is healthy")
        print(f"   Status: {health['status']}")
        print(f"   Redis: {'Connected' if health['redis_connected'] else 'Not Connected'}")
        print(f"   Version: {health['version']}")

        return health['redis_connected']

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API is not accessible: {e}")
        print("\nPlease ensure the FastAPI server is running:")
        print("   python -m src.api.main")
        return False


def demo_model_info():
    """Get model information from API."""
    print_header("DEMO 1: Model Information")

    try:
        response = requests.get(f"{API_BASE_URL}{API_PREFIX}/predictions/model/info")
        response.raise_for_status()
        result = response.json()

        model = result['model']
        print("\n📦 Deployed Model:")
        print(f"   Type: {model['model_type']}")
        print(f"   Version: {model['model_version']}")
        print(f"   Features: {model['feature_count']}")

        print("\n🎯 Risk Thresholds:")
        for level, threshold in model['risk_thresholds'].items():
            print(f"   {level}: {threshold}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Failed to get model info: {e}")


def demo_single_prediction(redis_available: bool):
    """Demonstrate single tutor prediction."""
    print_header("DEMO 2: Single Tutor Prediction")

    # Use a known tutor ID from the generated data
    tutor_id = "tutor_00001"

    print(f"\n1️⃣ First prediction for tutor {tutor_id} (no cache)")

    # First request - should not be cached
    payload = {
        "tutor_id": tutor_id,
        "include_explanation": True
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}{API_PREFIX}/predictions/tutor",
            json=payload
        )
        elapsed = time.time() - start_time

        response.raise_for_status()
        result = response.json()

        print(f"\n✅ Prediction received:")
        print(f"   Tutor: {result['tutor_name']}")
        print(f"   Status: {result['tutor_status']}")
        print(f"   Churn Score: {result['churn_score']}/100")
        print(f"   Risk Level: {result['risk_level']}")
        print(f"   Churn Probability: {result['churn_probability']:.2%}")
        print(f"   Cached: {result['cached']}")
        print(f"   Time: {elapsed:.3f}s")

        if result.get('contributing_factors'):
            print(f"\n   Top Contributing Factors:")
            for feature, data in list(result['contributing_factors'].items())[:3]:
                print(f"     - {feature}: {data['value']:.3f} (importance: {data['importance']:.3f})")

        if redis_available:
            # Second request - should be cached
            print(f"\n2️⃣ Second prediction for same tutor (should be cached)")

            payload_no_explanation = {
                "tutor_id": tutor_id,
                "include_explanation": False
            }

            start_time = time.time()
            response2 = requests.post(
                f"{API_BASE_URL}{API_PREFIX}/predictions/tutor",
                json=payload_no_explanation
            )
            elapsed2 = time.time() - start_time

            response2.raise_for_status()
            result2 = response2.json()

            print(f"\n✅ Prediction received:")
            print(f"   Cached: {result2['cached']}")
            print(f"   Time: {elapsed2:.3f}s")

            if result2['cached']:
                speedup = elapsed / elapsed2 if elapsed2 > 0 else 0
                print(f"   ⚡ Cache speedup: {speedup:.1f}x faster")
        else:
            print("\n⚠️  Redis not available - caching disabled")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Prediction failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Error: {e.response.text}")


def demo_batch_prediction():
    """Demonstrate batch prediction."""
    print_header("DEMO 3: Batch Prediction")

    # Predict multiple tutors
    tutor_ids = ["tutor_00001", "tutor_00005", "tutor_00010", "tutor_00015", "tutor_00020"]

    payload = {
        "tutor_ids": tutor_ids,
        "include_explanation": False
    }

    print(f"\nRequesting predictions for {len(tutor_ids)} tutors...")

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}{API_PREFIX}/predictions/batch",
            json=payload
        )
        elapsed = time.time() - start_time

        response.raise_for_status()
        result = response.json()

        print(f"\n✅ Batch prediction completed:")
        print(f"   Total predictions: {result['count']}")
        print(f"   Time: {elapsed:.3f}s")
        print(f"   Avg per tutor: {elapsed/result['count']:.3f}s")

        # Show risk distribution
        risk_counts = {}
        cached_count = 0

        for pred in result['predictions']:
            risk_counts[pred['risk_level']] = risk_counts.get(pred['risk_level'], 0) + 1
            if pred['cached']:
                cached_count += 1

        print(f"\n   Risk Distribution:")
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = risk_counts.get(level, 0)
            if count > 0:
                print(f"     {level}: {count}")

        if cached_count > 0:
            print(f"\n   Cache hits: {cached_count}/{result['count']}")

        # Show sample predictions
        print(f"\n   Sample Predictions:")
        for pred in result['predictions'][:3]:
            cache_indicator = "💾" if pred['cached'] else "🆕"
            print(f"     {cache_indicator} {pred['tutor_name']}: Score={pred['churn_score']}, Risk={pred['risk_level']}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Batch prediction failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Error: {e.response.text}")


def demo_cache_invalidation(redis_available: bool):
    """Demonstrate cache invalidation."""
    if not redis_available:
        print_header("DEMO 4: Cache Invalidation")
        print("\n⚠️  Skipping - Redis not available")
        return

    print_header("DEMO 4: Cache Invalidation")

    tutor_id = "tutor_00001"

    print(f"\nInvalidating cache for tutor {tutor_id}...")

    try:
        response = requests.delete(
            f"{API_BASE_URL}{API_PREFIX}/predictions/cache/{tutor_id}"
        )
        response.raise_for_status()
        result = response.json()

        print(f"\n✅ {result['message']}")

        # Verify by making new prediction
        print(f"\nMaking new prediction (should not be cached)...")

        payload = {
            "tutor_id": tutor_id,
            "include_explanation": False
        }

        response2 = requests.post(
            f"{API_BASE_URL}{API_PREFIX}/predictions/tutor",
            json=payload
        )
        response2.raise_for_status()
        result2 = response2.json()

        print(f"   Cached: {result2['cached']}")

        if not result2['cached']:
            print(f"   ✅ Cache successfully invalidated")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Cache invalidation failed: {e}")


def demo_error_handling():
    """Demonstrate API error handling."""
    print_header("DEMO 5: Error Handling")

    # Test with non-existent tutor
    invalid_tutor_id = "tutor_99999"

    print(f"\nTrying to predict for non-existent tutor: {invalid_tutor_id}")

    payload = {
        "tutor_id": invalid_tutor_id,
        "include_explanation": False
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}{API_PREFIX}/predictions/tutor",
            json=payload
        )

        if response.status_code == 404:
            print(f"\n✅ Correct error handling:")
            print(f"   Status: {response.status_code}")
            error = response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"\n✅ API returned expected error: {e}")


def main():
    """Run all API demos."""
    print("\n" + "=" * 70)
    print("CHURN PREDICTION API DEMO".center(70))
    print("=" * 70)

    # Check API health
    redis_available = check_api_health()

    if not redis_available:
        print("\n⚠️  Warning: Redis is not connected")
        print("   Caching features will be disabled")
        print("\nTo enable caching:")
        print("   1. Start Redis: redis-server")
        print("   2. Restart the API server")

    # Run demos
    try:
        demo_model_info()
        demo_single_prediction(redis_available)
        demo_batch_prediction()
        demo_cache_invalidation(redis_available)
        demo_error_handling()

        # Summary
        print_header("API DEPLOYMENT SUMMARY")
        print("\n✅ Churn prediction API is operational!")
        print("\nEndpoints Available:")
        print(f"   POST {API_PREFIX}/predictions/tutor - Single prediction")
        print(f"   POST {API_PREFIX}/predictions/batch - Batch prediction")
        print(f"   GET  {API_PREFIX}/predictions/model/info - Model info")
        print(f"   DELETE {API_PREFIX}/predictions/cache/{{tutor_id}} - Invalidate cache")

        print("\nFeatures:")
        print("   ✓ REST API for predictions")
        print("   ✓ Redis caching" + (" (enabled)" if redis_available else " (disabled - start Redis)"))
        print("   ✓ Batch processing")
        print("   ✓ Feature explanations")
        print("   ✓ Error handling")

        print("\nAPI Documentation:")
        print(f"   Swagger UI: {API_BASE_URL}/docs")
        print(f"   ReDoc: {API_BASE_URL}/redoc")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()

    if exit_code != 0:
        print("\n💡 Troubleshooting:")
        print("   1. Ensure API server is running: python -m src.api.main")
        print("   2. Check API is accessible: curl http://localhost:8000/health")
        print("   3. Check generated data exists: ls output/churn_data/")

    sys.exit(exit_code)
