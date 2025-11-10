/**
 * API client for Intervention Management
 */

import axios from 'axios';
import type {
  Intervention,
  InterventionStats,
  AssignInterventionRequest,
  UpdateStatusRequest,
  RecordOutcomeRequest,
  InterventionStatus,
  InterventionType,
} from '@/types/intervention';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class InterventionAPI {
  /**
   * Get interventions with optional filtering
   */
  static async getInterventions(params?: {
    status?: InterventionStatus;
    assigned_to?: string;
    intervention_type?: InterventionType;
    tutor_id?: string;
    include_overdue?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<Intervention[]> {
    const response = await axios.get(`${API_BASE_URL}/api/interventions/`, {
      params,
    });
    return response.data;
  }

  /**
   * Get intervention statistics
   */
  static async getStats(assigned_to?: string): Promise<InterventionStats> {
    const response = await axios.get(`${API_BASE_URL}/api/interventions/stats`, {
      params: assigned_to ? { assigned_to } : undefined,
    });
    return response.data;
  }

  /**
   * Get a specific intervention by ID
   */
  static async getIntervention(interventionId: string): Promise<Intervention> {
    const response = await axios.get(
      `${API_BASE_URL}/api/interventions/${interventionId}`
    );
    return response.data;
  }

  /**
   * Assign an intervention to a user
   */
  static async assignIntervention(
    interventionId: string,
    request: AssignInterventionRequest
  ): Promise<Intervention> {
    const response = await axios.post(
      `${API_BASE_URL}/api/interventions/${interventionId}/assign`,
      request
    );
    return response.data;
  }

  /**
   * Update intervention status
   */
  static async updateStatus(
    interventionId: string,
    request: UpdateStatusRequest
  ): Promise<Intervention> {
    const response = await axios.patch(
      `${API_BASE_URL}/api/interventions/${interventionId}/status`,
      request
    );
    return response.data;
  }

  /**
   * Record intervention outcome
   */
  static async recordOutcome(
    interventionId: string,
    request: RecordOutcomeRequest
  ): Promise<Intervention> {
    const response = await axios.post(
      `${API_BASE_URL}/api/interventions/${interventionId}/outcome`,
      request
    );
    return response.data;
  }
}
