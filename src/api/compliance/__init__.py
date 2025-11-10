"""
Compliance Module for TutorMax

Provides comprehensive compliance features including:

FERPA (Family Educational Rights and Privacy Act):
- 7-year data retention policy enforcement
- Student record access control
- Educational record classification
- Parent/guardian access management
- FERPA disclosure logging

GDPR (General Data Protection Regulation):
- Right to access (data export)
- Right to erasure ("right to be forgotten")
- Right to rectification (data correction)
- Right to data portability
- Consent management
- Data breach notification

COPPA (Children's Online Privacy Protection Act):
- Age verification
- Parental consent workflow
- Under-13 data protection (minimal collection)
- Parental access to child data
- COPPA-compliant data deletion
"""

from .ferpa import (
    FERPAService,
    FERPAAccessControl,
    FERPARecordType,
    FERPAAccessType,
    FERPADisclosureReason,
)

from .gdpr import (
    GDPRService,
    ConsentManager,
    DataBreachNotifier,
    gdpr_service,
    consent_manager,
    data_breach_notifier,
)

from .coppa import (
    COPPAService,
    ParentalConsentStatus,
    coppa_service,
    verify_age,
    requires_parental_consent,
    can_collect_data,
)

from .data_retention import (
    DataRetentionService,
    RetentionStatus,
    RetentionAction,
    data_retention_service,
)

__all__ = [
    # FERPA
    'FERPAService',
    'FERPAAccessControl',
    'FERPARecordType',
    'FERPAAccessType',
    'FERPADisclosureReason',
    # GDPR
    'GDPRService',
    'ConsentManager',
    'DataBreachNotifier',
    'gdpr_service',
    'consent_manager',
    'data_breach_notifier',
    # COPPA
    'COPPAService',
    'ParentalConsentStatus',
    'coppa_service',
    'verify_age',
    'requires_parental_consent',
    'can_collect_data',
    # Data Retention
    'DataRetentionService',
    'RetentionStatus',
    'RetentionAction',
    'data_retention_service',
]
