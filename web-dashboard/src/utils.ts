export function formatDate(iso: string): string {
  if (!iso) return "\u2014";
  const datePart = iso.split("T")[0];
  const [y, m, d] = datePart.split("-");
  return `${d}.${m}.${y}`;
}
