import { useMutation } from '@tanstack/react-query';
import { runDiagnostic } from '../lib/api';
import { DiagnosticRequest, DiagnosticResponse } from '../lib/types';

export function useDiagnostic() {
  return useMutation<DiagnosticResponse, Error, DiagnosticRequest>({
    mutationFn: runDiagnostic,
  });
}
