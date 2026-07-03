import csv
import logging
import re
from datetime import datetime
from pathlib import Path

from pdfplumber import open as open_pdf

PDF_DIR = Path(__file__).parent / "pdf"
CSV_DIR = Path(__file__).parent / "csv"

DECIMAL = r"\d{1,3}(?:\.\d{3})*(?:,\d+)?"
DECIMAL_FIXED = r"\d{1,3}(?:\.\d{3})*(?:,\d{2})"
DATE_NO_YEAR = r"(\d\d)\.(\d\d)\."
BLANK = r"\s{3,}"

re_range = re.compile(r"Kontoauszug Nummer (\d*) / (\d*) vom (\d\d)\.(\d\d)\.(\d\d\d\d) bis (\d\d)\.(\d\d)\.(\d\d\d\d)")
re_account = re.compile(r"Kontonummer (\d*) / IBAN ([A-Z0-9 ]*)")
re_table_header = re.compile(r"(Bu\.Tag)\s+(Wert)\s+(Wir haben für Sie gebucht)")
re_transaction = re.compile(
    rf"^\s*({DATE_NO_YEAR})\s+({DATE_NO_YEAR})\s+(.+?)\s+([\-+SH])?({DECIMAL_FIXED})\s*$"
)
re_detail = re.compile(r"^\s{3,}(.+)$")


def extract_text_from_pdf(path: Path) -> str:
    lines = []
    with open_pdf(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())
    return "\n".join(lines)


def parse_bank_statement(text: str) -> list[dict]:
    transactions: list[dict] = []
    lines = text.splitlines()

    iban = ""
    year = ""
    in_table = False

    for line in lines:
        m = re_range.search(line)
        if m:
            year = m.group(2)

        m = re_account.search(line)
        if m:
            iban = m.group(2).replace(" ", "")

        if re_table_header.search(line):
            in_table = True

        m = re_transaction.match(line)
        if m and in_table:
            booked = f"{m.group(1)}{m.group(2)}{year[-2:]}"
            valued = f"{m.group(3)}{m.group(4)}{year[-2:]}"
            ttype = m.group(5).strip()
            sign_raw = m.group(6)
            raw_amount = m.group(7).replace(".", "").replace(",", ".")
            amount = float(raw_amount)

            if sign_raw and sign_raw in ["-", "S"]:
                amount = -amount

            transactions.append({
                "Buchungsdatum": booked,
                "Wertstellung": valued,
                "Status": "Gebucht",
                "Zahlungspflichtige*r": "",
                "Zahlungsempfänger*in": ttype,
                "Verwendungszweck": ttype,
                "Umsatztyp": "Ausgang" if amount < 0 else "Eingang",
                "IBAN": iban,
                "Betrag (€)": f"{amount:+.2f}".replace(".", ","),
                "Gläubiger-ID": "",
                "Mandatsreferenz": "",
                "Kundenreferenz": "",
            })

        if transactions and re_detail.match(line):
            last = transactions[-1]
            last["Verwendungszweck"] += " " + line.strip()

    return transactions


def scan_pdfs() -> list[Path]:
    return sorted(PDF_DIR.glob("*.pdf"))


def write_csv(transactions: list[dict], out_path: Path) -> None:
    fieldnames = [
        "Buchungsdatum", "Wertstellung", "Status", "Zahlungspflichtige*r",
        "Zahlungsempfänger*in", "Verwendungszweck", "Umsatztyp", "IBAN",
        "Betrag (€)", "Gläubiger-ID", "Mandatsreferenz", "Kundenreferenz",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(transactions)


def main() -> None:
    pdf_files = scan_pdfs()
    if not pdf_files:
        print("Keine PDF-Dateien im Ordner 'pdf/' gefunden.")
        return

    for pdf_path in pdf_files:
        print(f"Verarbeite {pdf_path.name} ...")
        text = extract_text_from_pdf(pdf_path)
        transactions = parse_bank_statement(text)
        if not transactions:
            print(f"  Keine Transaktionen gefunden in {pdf_path.name}")
            continue

        out_path = CSV_DIR / f"{pdf_path.stem}.csv"
        write_csv(transactions, out_path)
        print(f"  -> {len(transactions)} Transaktionen geschrieben nach {out_path.name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
