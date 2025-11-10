"""
Prediction API endpoints for churn prediction.

Provides REST endpoints for single and batch churn predictions with caching.
"""

import logging
from datetime import datetime
from typing import Optional
import pandas as pd
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .config import settings
from .models import (
    PredictionRequest,
    BatchPredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
)
from .redis_service import redis_service, get_redis_service, RedisService
from ..evaluation.prediction_service import ChurnPredictionService
from ..database.database import get_async_session

logger = logging.getLogger(__name__)

# Initialize prediction service (loaded once at startup)
_prediction_service: Optional[ChurnPredictionService] = None


def get_prediction_service() -> ChurnPredictionService:
    """
    Get or create prediction service instance.

    Returns:
        ChurnPredictionService instance
    """
    global _prediction_service

    if _prediction_service is None:
        model_path = Path("output/models/churn_model.pkl")
        if not model_path.exists():
            raise RuntimeError(f"Model file not found: {model_path}")

        _prediction_service = ChurnPredictionService(str(model_path))
        logger.info("Prediction service initialized")

    return _prediction_service


def load_tutor_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load tutor, session, and feedback data from database or files.

    For now, loads from generated CSV files. In production, would query database.

    Returns:
        Tuple of (tutors_df, sessions_df, feedback_df)
    """
    # Try to load from output directory
    data_dir = Path("output/churn_data")

    if not data_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Churn data not available. Run data preparation first."
        )

    try:
        tutors_df = pd.read_csv(data_dir / "tutors.csv")
        sessions_df = pd.read_csv(data_dir / "sessions.csv")
        feedback_df = pd.read_csv(data_dir / "feedback.csv")

        logger.debug(
            f"Loaded data: {len(tutors_df)} tutors, "
            f"{len(sessions_df)} sessions, {len(feedback_df)} feedback"
        )

        return tutors_df, sessions_df, feedback_df

    except Exception as e:
        logger.error(f"Failed to load tutor data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load tutor data"
        )


# Create router
router = APIRouter(prefix=f"{settings.api_prefix}/predictions", tags=["Predictions"])


@router.post(
    "/tutor",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def predict_tutor_churn(
    request: PredictionRequest,
    redis: RedisService = Depends(get_redis_service),
) -> PredictionResponse:
    """
    Predict churn for a single tutor.

    Checks Redis cache first, then makes prediction if not cached.
    Stores result in cache for future requests.
    """
    tutor_id = request.tutor_id
    include_explanation = request.include_explanation

    # Check cache first
    cached_prediction = await redis.get_cached_prediction(tutor_id)
    if cached_prediction and not include_explanation:
        # Return cached result
        logger.info(f"Returning cached prediction for tutor {tutor_id}")
        return PredictionResponse(
            success=True,
            cached=True,
            timestamp=datetime.now().isoformat(),
            **cached_prediction
        )

    try:
        # Load data
        tutors_df, sessions_df, feedback_df = load_tutor_data()

        # Check tutor exists
        if tutor_id not in tutors_df['tutor_id'].values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get prediction service
        service = get_prediction_service()

        # Make prediction
        prediction = service.predict_tutor(
            tutor_id=tutor_id,
            tutors_df=tutors_df,
            sessions_df=sessions_df,
            feedback_df=feedback_df,
            include_explanation=include_explanation
        )

        # Cache result (without explanation to save space)
        if not include_explanation:
            await redis.cache_prediction(tutor_id, prediction)

        # Build response
        response = PredictionResponse(
            success=True,
            cached=False,
            timestamp=datetime.now().isoformat(),
            **prediction
        )

        logger.info(
            f"Prediction for {tutor_id}: "
            f"score={prediction['churn_score']}, "
            f"risk={prediction['risk_level']}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def predict_batch_churn(
    request: BatchPredictionRequest,
    redis: RedisService = Depends(get_redis_service),
) -> BatchPredictionResponse:
    """
    Predict churn for multiple tutors.

    Returns predictions for all requested tutors.
    Uses cache where available, makes new predictions otherwise.
    """
    tutor_ids = request.tutor_ids
    include_explanation = request.include_explanation

    logger.info(f"Batch prediction requested for {len(tutor_ids)} tutors")

    try:
        # Load data
        tutors_df, sessions_df, feedback_df = load_tutor_data()

        # Get prediction service
        service = get_prediction_service()

        predictions = []
        cache_hits = 0

        for tutor_id in tutor_ids:
            # Check cache first
            if not include_explanation:
                cached = await redis.get_cached_prediction(tutor_id)
                if cached:
                    predictions.append(
                        PredictionResponse(
                            success=True,
                            cached=True,
                            timestamp=datetime.now().isoformat(),
                            **cached
                        )
                    )
                    cache_hits += 1
                    continue

            # Make new prediction
            try:
                if tutor_id not in tutors_df['tutor_id'].values:
                    logger.warning(f"Tutor {tutor_id} not found, skipping")
                    continue

                prediction = service.predict_tutor(
                    tutor_id=tutor_id,
                    tutors_df=tutors_df,
                    sessions_df=sessions_df,
                    feedback_df=feedback_df,
                    include_explanation=include_explanation
                )

                # Cache if not including explanation
                if not include_explanation:
                    await redis.cache_prediction(tutor_id, prediction)

                predictions.append(
                    PredictionResponse(
                        success=True,
                        cached=False,
                        timestamp=datetime.now().isoformat(),
                        **prediction
                    )
                )

            except Exception as e:
                logger.error(f"Failed to predict for tutor {tutor_id}: {e}")
                # Continue with other tutors

        logger.info(
            f"Batch prediction completed: "
            f"{len(predictions)} predictions ({cache_hits} cached)"
        )

        return BatchPredictionResponse(
            success=True,
            message=f"Batch prediction completed ({cache_hits}/{len(tutor_ids)} cached)",
            predictions=predictions,
            count=len(predictions),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


@router.get(
    "/model/info",
    tags=["Predictions"],
)
async def get_model_info():
    """
    Get information about the deployed model.

    Returns model version, configuration, and metadata.
    """
    try:
        service = get_prediction_service()
        info = service.get_model_info()

        return {
            "success": True,
            "model": info,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information"
        )


@router.delete(
    "/cache/{tutor_id}",
    tags=["Predictions"],
)
async def invalidate_prediction_cache(
    tutor_id: str,
    redis: RedisService = Depends(get_redis_service),
):
    """
    Invalidate cached prediction for a tutor.

    Useful when tutor data has been updated and prediction should be recalculated.
    """
    success = await redis.invalidate_prediction_cache(tutor_id)

    if success:
        return {
            "success": True,
            "message": f"Cache invalidated for tutor {tutor_id}",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache"
        )
