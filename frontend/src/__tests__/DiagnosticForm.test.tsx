import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import DiagnosticForm from "../components/DiagnosticForm";

describe("DiagnosticForm Component", () => {
  it("renders form fields and submit button", () => {
    const handleSubmit = vi.fn();
    render(<DiagnosticForm onSubmit={handleSubmit} isLoading={false} />);

    expect(screen.getByLabelText(/Product Search Query/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Target Brand/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Brand Website/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run Diagnostic/i })).toBeInTheDocument();
  });

  it("submits the entered query, brand, and defaults", () => {
    const handleSubmit = vi.fn();
    render(<DiagnosticForm onSubmit={handleSubmit} isLoading={false} />);

    const queryInput = screen.getByLabelText(/Product Search Query/i);
    const brandInput = screen.getByLabelText(/Target Brand/i);
    const submitButton = screen.getByRole("button", { name: /Run Diagnostic/i });

    fireEvent.change(queryInput, { target: { value: "best running shoes" } });
    fireEvent.change(brandInput, { target: { value: "Nike" } });
    fireEvent.click(submitButton);

    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        query: "best running shoes",
        your_brand: "Nike",
        market: "US",
      })
    );
  });

  it("disables inputs and displays running state when loading", () => {
    const handleSubmit = vi.fn();
    render(<DiagnosticForm onSubmit={handleSubmit} isLoading={true} />);

    const queryInput = screen.getByLabelText(/Product Search Query/i);
    const brandInput = screen.getByLabelText(/Target Brand/i);

    expect(queryInput).toBeDisabled();
    expect(brandInput).toBeDisabled();
    expect(screen.getByText(/Running Diagnostic/i)).toBeInTheDocument();
  });
});
