import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("react-plotly.js", () => ({
  default: () => <div data-testid="mock-plot" />,
}));

vi.mock("../api", () => ({
  fetchDashboardData: vi.fn().mockResolvedValue({
    expenses: [],
    income: [],
    profit_loss: [],
    categories: ["Food", "Transport"],
  }),
  fetchCategories: vi.fn().mockResolvedValue([]),
  saveCategories: vi.fn().mockResolvedValue(undefined),
}));

import App from "../App";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders the dashboard view by default", async () => {
    render(<App />);
    expect(await screen.findByText("DKB Finanz-Dashboard")).toBeInTheDocument();
  });

  it("switches to data view when clicking Daten", async () => {
    render(<App />);
    const dataTab = await screen.findByText("Daten");
    fireEvent.click(dataTab);
    expect(await screen.findByText("Kategorie-Editor")).toBeInTheDocument();
  });

  it("switches back to dashboard view when clicking Dashboard", async () => {
    render(<App />);
    const dataTab = await screen.findByText("Daten");
    fireEvent.click(dataTab);
    const dashTab = await screen.findByText("Dashboard");
    fireEvent.click(dashTab);
    expect(await screen.findByText("DKB Finanz-Dashboard")).toBeInTheDocument();
  });

  it("has a dark mode toggle", async () => {
    render(<App />);
    const toggle = await screen.findByRole("button", { name: /🌙|☀️/i });
    expect(toggle).toBeInTheDocument();
  });

  it("applies dark class when toggling dark mode", async () => {
    render(<App />);
    const toggle = await screen.findByRole("button", { name: /🌙|☀️/i });
    fireEvent.click(toggle);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });
});
