import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Login from "../pages/Login";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Login page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders role selector and phone input", () => {
    render(<Login />, { wrapper });
    expect(screen.getByText("footbAIl")).toBeTruthy();
    expect(screen.getByText("Player")).toBeTruthy();
    expect(screen.getByText("Coach")).toBeTruthy();
    expect(screen.getByPlaceholderText("98765 43210")).toBeTruthy();
  });

  it("disables Send OTP button if phone < 10 digits", () => {
    render(<Login />, { wrapper });
    const btn = screen.getByText(/Send OTP/i).closest("button");
    expect(btn).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText("98765 43210"), {
      target: { value: "9876543" },
    });
    expect(btn).toBeDisabled();
  });

  it("enables Send OTP button when 10 digits entered", () => {
    render(<Login />, { wrapper });
    fireEvent.change(screen.getByPlaceholderText("98765 43210"), {
      target: { value: "9876543210" },
    });
    const btn = screen.getByText(/Send OTP/i).closest("button");
    expect(btn).not.toBeDisabled();
  });

  it("selects coach role on click", () => {
    render(<Login />, { wrapper });
    const coachBtn = screen.getByText("Coach").closest("button");
    if (coachBtn) fireEvent.click(coachBtn);
    expect(coachBtn?.className).toContain("text-[#00ff88]");
  });
});

describe("StatCard component", () => {
  it("renders value and label", async () => {
    const { default: StatCard } = await import("../components/StatCard");
    render(<StatCard val="9.1" label="AVG RATING" delta="+0.4" />, {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });
    expect(screen.getByText("9.1")).toBeTruthy();
    expect(screen.getByText("AVG RATING")).toBeTruthy();
    expect(screen.getByText("+0.4")).toBeTruthy();
  });
});
