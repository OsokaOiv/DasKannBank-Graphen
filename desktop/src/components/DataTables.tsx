import { useState, useMemo } from "react";
import type { ExpenseRecord } from "../types";
import { formatDate } from "../utils";

interface Props {
  expenses: ExpenseRecord[];
}

type SortKey = "Datum" | "Kategorie" | "Betrag" | "Zahlungsempfänger*in";

const numFmt = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export default function DataTables({ expenses }: Props) {
  const [open, setOpen] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("Datum");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = useMemo(() => [...expenses].sort((a, b) => {
    const va = a[sortKey] ?? "";
    const vb = b[sortKey] ?? "";
    const cmp = typeof va === "number" && typeof vb === "number"
      ? va - vb
      : String(va).localeCompare(String(vb));
    return sortAsc ? cmp : -cmp;
  }), [expenses, sortKey, sortAsc]);

  const toggleSort = (k: SortKey) => {
    if (sortKey === k) setSortAsc(!sortAsc);
    else {
      setSortKey(k);
      setSortAsc(true);
    }
  };

  const arrow = (k: SortKey): string =>
    sortKey === k ? (sortAsc ? " \u25b2" : " \u25bc") : "";

  const sortProps = (k: SortKey) => ({
    onClick: () => toggleSort(k),
    onKeyDown: (event: React.KeyboardEvent) => { if (event.key === "Enter" || event.key === " ") toggleSort(k); },
    tabIndex: 0 as const,
    "aria-sort": sortKey === k ? (sortAsc ? "ascending" as const : "descending" as const) : "none" as const,
  });

  return (
    <div className="table-section">
      <button className="uncategorized-toggle" onClick={() => setOpen(!open)}>
        <span>📋 Transaktionen ({expenses.length})</span>
        <span>{open ? "\u25b2" : "\u25bc"}</span>
      </button>
      {open && (
        <div className="uncategorized-body" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th {...sortProps("Datum")}>
                  Datum{arrow("Datum")}
                </th>
                <th {...sortProps("Zahlungsempfänger*in")}>
                  Empfänger{arrow("Zahlungsempfänger*in")}
                </th>
                <th>Verwendungszweck</th>
                <th {...sortProps("Kategorie")}>
                  Kategorie{arrow("Kategorie")}
                </th>
                <th {...sortProps("Betrag")} style={{ textAlign: "right" }}>
                  Betrag{arrow("Betrag")}
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((record) => (
                <tr key={`${record.Datum}-${record.Betrag}-${record.Kategorie}`}>
                  <td>{formatDate(record.Datum)}</td>
                  <td>{record["Zahlungsempfänger*in"] ?? "\u2014"}</td>
                  <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {record.Verwendungszweck ?? "\u2014"}
                  </td>
                  <td>{record.Kategorie}</td>
                  <td style={{ textAlign: "right" }}>{numFmt.format(record.Betrag)} €</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
