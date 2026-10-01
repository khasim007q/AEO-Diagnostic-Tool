import { DiagnosticRequest, DiagnosticResponse } from "./types";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function runDiagnostic(request: DiagnosticRequest): Promise<DiagnosticResponse> {
  const response = await fetch(`${API_URL}/diagnostic`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorMessage = 'Failed to run diagnostic';
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch (e) {
      // Ignore JSON parse errors
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
