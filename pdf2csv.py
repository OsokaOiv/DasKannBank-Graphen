import argparse
import csv
import logging
import re
from pathlib import Path

from pdfplumber import open as open_pdf

PDF_DIR = Path(__file__).parent / "pdf"
CSV_DIR = Path(__file__).parent / "csv"

AMOUNT_END = re.compile(r"\s+([\-+])?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))\s*$")
DATE_START = re.compile(r"^(\d\d)\.(\d\d)\.(\d{4})")
DETAIL_LINE = re.compile(r"^\s{2,}(.+)$")


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

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        dm = DATE_START.match(line)
        if dm:
            day, month, year = dm.group(1), dm.group(2), dm.group(3)
            rest = line[dm.end():]
            am = AMOUNT_END.search(rest)
            amount = None
            ttype = rest

            if am:
                ttype = rest[:am.start()].strip()
                sign = am.group(1)
                raw_amount = am.group(2).replace(".", "").replace(",", ".")
                amount = float(raw_amount)
                if sign and sign == "-":
                    amount = -amount

            if amount is not None:
                transactions.append({
                    "Buchungsdatum": f"{day}.{month}.{year[-2:]}",
                    "Wertstellung": f"{day}.{month}.{year[-2:]}",
                    "Status": "Gebucht",
                    "Zahlungspflichtige*r": "",
                    "Zahlungsempfänger*in": ttype,
                    "Verwendungszweck": ttype,
                    "Umsatztyp": "Ausgang" if amount < 0 else "Eingang",
                    "IBAN": "",
                    "Betrag (€)": f"{amount:+.2f}".replace(".", ","),
                    "Gläubiger-ID": "",
                    "Mandatsreferenz": "",
                    "Kundenreferenz": "",
                })
                continue

        if transactions and DETAIL_LINE.match(raw_line):
            last = transactions[-1]
            detail = line
            if last["Zahlungsempfänger*in"] == last["Verwendungszweck"]:
                last["Zahlungsempfänger*in"] = detail
            last["Verwendungszweck"] += " " + detail

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
    parser = argparse.ArgumentParser(description="DKB-PDF zu CSV Konverter")
    parser.add_argument("--debug", action="store_true", help="Extrahierten Text als .txt speichern")
    args = parser.parse_args()

    pdf_files = scan_pdfs()
    if not pdf_files:
        print("Keine PDF-Dateien im Ordner 'pdf/' gefunden.")
        return

    for pdf_path in pdf_files:
        print(f"Verarbeite {pdf_path.name} ...")
        text = extract_text_from_pdf(pdf_path)

        if args.debug:
            dump_path = pdf_path.with_suffix(".txt")
            dump_path.write_text(text, encoding="utf-8")
            print(f"  -> Text extrahiert nach {dump_path.name}")

        transactions = parse_bank_statement(text)
        if not transactions:
            non_empty = sum(1 for line in text.splitlines() if line.strip())
            print(f"  Keine Transaktionen gefunden ({non_empty} nicht-leere Zeilen)")
            if args.debug:
                print(f"  -> Ersten 30 Zeilen:")
                for i, line in enumerate(text.splitlines()[:30]):
                    print(f"     [{i:>2}] {line}")
            continue

        out_path = CSV_DIR / f"{pdf_path.stem}.csv"
        write_csv(transactions, out_path)
        print(f"  -> {len(transactions)} Transaktionen geschrieben nach {out_path.name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
