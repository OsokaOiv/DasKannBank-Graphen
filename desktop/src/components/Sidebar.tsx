import type { FilterState } from "../types";

interface SidebarProps {
  categories: string[];
  filter: FilterState;
  onFilterChange: (f: FilterState) => void;
}

export default function Sidebar({ categories, filter, onFilterChange }: SidebarProps) {
  return (
    <aside className="sidebar">
      <h2>Filter</h2>

      <div className="filter-group">
        <label>Zeitraum</label>
        <div className="date-row">
          <label htmlFor="filter-date-from" style={{ fontSize: 12, color: "#888", minWidth: 28 }}>Von</label>
          <input
            id="filter-date-from"
            type="date"
            value={filter.dateFrom}
            onChange={(e) => onFilterChange({ ...filter, dateFrom: e.target.value })}
          />
        </div>
        <div className="date-row">
          <label htmlFor="filter-date-to" style={{ fontSize: 12, color: "#888", minWidth: 28 }}>Bis</label>
          <input
            id="filter-date-to"
            type="date"
            value={filter.dateTo}
            onChange={(e) => onFilterChange({ ...filter, dateTo: e.target.value })}
          />
        </div>
      </div>

      <div className="filter-group">
        <label htmlFor="filter-categories">Kategorien</label>
        <select
          id="filter-categories"
          multiple
          value={filter.categories}
          onChange={(e) => {
            const opts = Array.from(e.target.selectedOptions, (o) => o.value);
            onFilterChange({ ...filter, categories: opts });
          }}
          style={{ height: Math.min(categories.length * 24 + 8, 240) }}
        >
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>
    </aside>
  );
}
