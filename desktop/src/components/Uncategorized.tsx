import { useState, useMemo } from "react";
import type { ExpenseRecord } from "../types";
import { formatDate } from "../utils";

interface Props {
  expenses: ExpenseRecord[];
}

const CATEGORY_OTHER = "Sonstige";

export default function Uncategorized({ expenses }: Props) {
  const [open, setOpen] = useState(false);
  const sonstige = useMemo(() => expenses.filter((e) => e.Kategorie === CATEGORY_OTHER), [expenses]);

  if (sonstige.length === 0) {
    return (
      <button className="uncategorized-toggle success" disabled>
        ✅ Alle Ausgaben sind kategorisiert!
      </button>
    );
  }

  return (
    <div>
      <button className="uncategorized-toggle" onClick={() => setOpen(!open)}>
        <span>⚠️ Nicht kategorisiert ({sonstige.length} Transaktionen)</span>
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="uncategorized-body" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Datum</th>
                <th>Empfänger</th>
                <th>Verwendungszweck</th>
                <th style={{ textAlign: "right" }}>Betrag (€)</th>
              </tr>
            </thead>
            <tbody>
              {sonstige.map((record) => (
                <tr key={`${record.Datum}-${record.Betrag}`}>
                  <td>{formatDate(record.Datum)}</td>
                  <td>{record["Zahlungsempfänger*in"] ?? "\u2014"}</td>
                  <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {record.Verwendungszweck ?? "\u2014"}
                  </td>
                  <td style={{ textAlign: "right" }}>{record.Betrag.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


