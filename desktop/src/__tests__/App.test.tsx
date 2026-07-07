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
    const toggle = await screen.findByRole("button", { name: /helles design|dunkles design/i });
    expect(toggle).toBeInTheDocument();
  });

  it("applies dark class when toggling dark mode", async () => {
    render(<App />);
    const toggle = await screen.findByRole("button", { name: /helles design|dunkles design/i });
    fireEvent.click(toggle);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("has a theme selector", async () => {
    render(<App />);
    const select = await screen.findByRole("combobox", { name: /design wählen/i });
    expect(select).toBeInTheDocument();
  });

  it("switches theme and applies correct class", async () => {
    render(<App />);
    const select = await screen.findByRole("combobox", { name: /design wählen/i }) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "terminal-pro" } });
    expect(document.documentElement.classList.contains("theme-terminal-pro")).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("switches to Persona 5 theme and toggles dark mode", async () => {
    render(<App />);
    const select = await screen.findByRole("combobox", { name: /design wählen/i }) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "persona-5" } });
    expect(document.documentElement.classList.contains("theme-persona-5")).toBe(true);
    const toggle = await screen.findByRole("button", { name: /helles design|dunkles design/i });
    expect(toggle).toBeInTheDocument();
    fireEvent.click(toggle);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });
});
