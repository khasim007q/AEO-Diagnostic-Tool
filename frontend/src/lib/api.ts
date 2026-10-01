// api.ts
import {
  DiagnosticRequest,
  DiagnosticResponse,
  DiagnosticResponseSchema,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT_MS = 45000;

export class ApiError extends Error {
  statusCode?: number;
  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

export async function runDiagnostic(
  request: DiagnosticRequest,
  signal?: AbortSignal,
): Promise<DiagnosticResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  // Link caller signal if provided
  if (signal) {
    signal.addEventListener("abort", () => controller.abort());
  }

  try {
    const response = await fetch(`${API_URL}/diagnostic`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let detail = "";
      try {
        const errJson = await response.json();
        detail = errJson.detail || "";
      } catch {
        // Fallback to text or generic message
      }

      if (response.status === 429) {
        throw new ApiError(
          detail || "Diagnostic rate limit reached. Please wait 60 seconds before submitting again.",
          429,
        );
      }
      if (response.status === 504) {
        throw new ApiError(
          detail || "Diagnostic timed out while evaluating AI models and Google search.",
          504,
        );
      }
      if (response.status >= 500) {
        throw new ApiError(
          detail || "A backend server error occurred while processing your diagnostic.",
          response.status,
        );
      }
      throw new ApiError(
        detail || `Request failed with status ${response.status}`,
        response.status,
      );
    }

    const data = await response.json();
    const parseResult = DiagnosticResponseSchema.safeParse(data);
    if (!parseResult.success) {
      console.error("Diagnostic response validation failure:", parseResult.error);
      throw new ApiError(
        "Received an unexpected response format from the diagnostic service.",
        502,
      );
    }

    return parseResult.data;
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError(
        "Diagnostic timed out after 45 seconds. Please try again with a more specific query.",
        504,
      );
    }
    throw new ApiError(
      "Unable to connect to the diagnostic service. Please check your network connection.",
      0,
    );
  }
}
