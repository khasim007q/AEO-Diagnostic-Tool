import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import DiagnosticForm from "../components/DiagnosticForm";

describe("DiagnosticForm Component", () => {
  it("renders form fields and submit button", () => {
    const handleSubmit = vi.fn();
    render(<DiagnosticForm onSubmit={handleSubmit} isLoading={false} />);

    expect(screen.getByLabelText(/Search Query/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Your Brand/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run Diagnostic/i })).toBeInTheDocument();
  });

  it("submits the entered query and optional brand", () => {
    const handleSubmit = vi.fn();
    render(<DiagnosticForm onSubmit={handleSubmit} isLoading={false} />);

    const queryInput = screen.getByLabelText(/Search Query/i);
    const brandInput = screen.getByLabelText(/Your Brand/i);
    const submitButton = screen.getByRole("button", { name: /Run Diagnostic/i });

    fireEvent.change(queryInput, { target: { value: "best whey protein" } });
    fireEvent.change(brandInput, { target: { value: "Optimum Nutrition" } });
    fireEvent.click(submitButton);

    expect(handleSubmit).toHaveBeenCalledWith({
      query: "best whey protein",
      your_brand: "Optimum Nutrition",
    });
  });

  it("disables inputs and displays running state when loading", () => {
    const handleSubmit = vi.fn();
    render(<DiagnosticForm onSubmit={handleSubmit} isLoading={true} />);

    const queryInput = screen.getByLabelText(/Search Query/i);
    const brandInput = screen.getByLabelText(/Your Brand/i);

    expect(queryInput).toBeDisabled();
    expect(brandInput).toBeDisabled();
    expect(screen.getByText("Running Diagnostic...")).toBeInTheDocument();
  });
});
