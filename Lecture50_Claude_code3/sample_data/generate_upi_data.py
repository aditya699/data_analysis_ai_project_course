"""
Generate a synthetic UPI transactions dataset for testing the
Auto Data Analyst Agent.

Uses only the Python standard library (no pandas / openpyxl needed).

Usage:
    python generate_upi_data.py            # 5,000 rows (default)
    python generate_upi_data.py 20000      # custom row count

Outputs (next to this script):
    upi_transactions.csv
    upi_transactions.xlsx

All names, VPAs and IDs are fictional. A few data quality issues are
added on purpose (missing values, duplicates, outliers, messy text) so
the agent's quality checks have something to find.
"""

import csv
import random
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

SEED = 42
DEFAULT_ROWS = 5000
OUTPUT_DIR = Path(__file__).parent
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 9, 30, 23, 59, 59)

# ---------------------------------------------------------------- reference data

UPI_APPS = [("PhonePe", 46), ("Google Pay", 36), ("Paytm", 8), ("CRED", 3),
            ("Amazon Pay", 3), ("BHIM", 2), ("WhatsApp Pay", 2)]

# bank name -> VPA handle
BANKS = {
    "State Bank of India": "oksbi", "HDFC Bank": "okhdfcbank",
    "ICICI Bank": "okicici", "Axis Bank": "okaxis", "Kotak Mahindra Bank": "kotak",
    "Punjab National Bank": "pnb", "Bank of Baroda": "barodampay",
    "Yes Bank": "yesbank", "IDFC First Bank": "idfcbank", "Canara Bank": "cnrb",
}

CITIES = [
    ("Mumbai", "Maharashtra", 14), ("Delhi", "Delhi", 13), ("Bengaluru", "Karnataka", 12),
    ("Hyderabad", "Telangana", 8), ("Chennai", "Tamil Nadu", 7), ("Pune", "Maharashtra", 7),
    ("Kolkata", "West Bengal", 6), ("Ahmedabad", "Gujarat", 5), ("Jaipur", "Rajasthan", 4),
    ("Lucknow", "Uttar Pradesh", 4), ("Indore", "Madhya Pradesh", 3), ("Chandigarh", "Chandigarh", 3),
    ("Kochi", "Kerala", 3), ("Patna", "Bihar", 3), ("Bhubaneswar", "Odisha", 2),
    ("Guwahati", "Assam", 2), ("Nagpur", "Maharashtra", 2), ("Surat", "Gujarat", 2),
]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan",
               "Rohan", "Kabir", "Ananya", "Diya", "Aadhya", "Saanvi", "Priya", "Kavya",
               "Meera", "Isha", "Riya", "Neha", "Rahul", "Vikram", "Sneha", "Pooja", "Amit",
               "Suresh", "Lakshmi", "Farhan", "Zoya", "Harpreet", "Gurpreet", "Anjali"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Reddy", "Iyer", "Nair", "Gupta", "Singh",
              "Kumar", "Das", "Mehta", "Joshi", "Rao", "Khan", "Banerjee", "Chopra",
              "Pillai", "Mishra", "Agarwal", "Bhatt", "Shah", "Menon", "Ghosh", "Kaur"]

# category -> (weight, merchant name parts, typical amount range in INR)
MERCHANT_CATEGORIES = {
    "Groceries":        (20, ["FreshMart", "Daily Needs", "Green Basket", "Kirana Store"], (50, 3000)),
    "Food & Dining":    (18, ["Spice Route Cafe", "Tiffin Point", "Biryani House", "Chai Corner"], (40, 2500)),
    "Fuel":             (8,  ["City Fuels", "Highway Petro", "Metro Fuel Station"], (200, 5000)),
    "Shopping":         (10, ["Style Hub", "Urban Threads", "Gadget World", "Home Decor Co"], (300, 15000)),
    "Utilities":        (7,  ["Power Board Pay", "Water Works", "Gas Connect"], (300, 6000)),
    "Mobile Recharge":  (9,  ["Recharge Point", "Prepaid Plus"], (99, 999)),
    "Travel":           (5,  ["Rail Tickets Online", "Metro Card Topup", "Cab Rides", "Bus Yatra"], (30, 12000)),
    "Entertainment":    (5,  ["Movie Halls", "Stream Plus", "Gaming Zone"], (99, 1500)),
    "Healthcare":       (5,  ["Care Pharmacy", "City Diagnostics", "Wellness Clinic"], (100, 8000)),
    "Education":        (3,  ["Bright Tutors", "Book Depot", "Exam Fees Portal"], (500, 25000)),
    "Rent":             (4,  ["Rent Payment"], (5000, 45000)),
    "Insurance":        (2,  ["Secure Life Premium", "Health Shield Premium"], (1000, 30000)),
    "Investments":      (4,  ["Mutual Fund SIP", "Gold Savings"], (500, 50000)),
}

P2P_PURPOSES = ["Split bill", "Family transfer", "Rent share", "Gift", "Loan repayment",
                "Friends outing", "Household expenses", "Other"]

FAILURE_REASONS = [("Insufficient balance", 30), ("Bank server down", 20),
                   ("Incorrect UPI PIN", 18), ("Transaction timed out", 14),
                   ("Daily limit exceeded", 8), ("Beneficiary bank unavailable", 6),
                   ("Risk check declined", 4)]

DEVICES = [("Android", 78), ("iOS", 20), ("Feature phone (UPI 123PAY)", 2)]

COLUMNS = [
    "transaction_id", "timestamp", "date", "hour", "day_of_week",
    "transaction_type", "payer_name", "payer_vpa", "payer_bank",
    "payee_name", "payee_vpa", "payee_bank", "merchant_category",
    "amount_inr", "status", "failure_reason", "upi_app", "device_type",
    "city", "state", "is_first_time_payee", "remarks",
]


# ---------------------------------------------------------------- helpers

def weighted_choice(rng, pairs):
    """pairs: list of (value, weight) -> value"""
    values, weights = zip(*pairs)
    return rng.choices(values, weights=weights, k=1)[0]


def random_timestamp(rng):
    """Random time in range, skewed towards daytime and evenings."""
    span_days = (END_DATE - START_DATE).days
    day = START_DATE + timedelta(days=rng.randint(0, span_days))
    hour = rng.choices(range(24), weights=[1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 9,
                                           10, 9, 8, 8, 8, 9, 11, 12, 11, 8, 5, 2])[0]
    return day.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))


def make_person(rng):
    first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
    bank = rng.choice(list(BANKS))
    handle = f"{first.lower()}.{last.lower()}{rng.randint(1, 999)}"
    return {"name": f"{first} {last}", "vpa": f"{handle}@{BANKS[bank]}", "bank": bank}


def make_merchant(rng, category):
    _, names, _ = MERCHANT_CATEGORIES[category]
    base = rng.choice(names)
    bank = rng.choice(list(BANKS))
    vpa = base.lower().replace(" ", "").replace("&", "") + f"{rng.randint(10, 99)}@{BANKS[bank]}"
    return {"name": base, "vpa": vpa, "bank": bank}


def make_amount(rng, low, high):
    """Log-ish distribution: many small payments, fewer big ones."""
    value = low + (high - low) * (rng.random() ** 2.2)
    return round(value) if value > 500 else round(value, 2)


# ---------------------------------------------------------------- generation

def generate_rows(n_rows, rng):
    people = [make_person(rng) for _ in range(800)]
    category_weights = [(c, w) for c, (w, _, _) in MERCHANT_CATEGORIES.items()]
    merchants = {c: [make_merchant(rng, c) for _ in range(12)] for c in MERCHANT_CATEGORIES}
    seen_pairs = set()
    rows = []

    for i in range(n_rows):
        ts = random_timestamp(rng)
        payer = rng.choice(people)
        city, state, _ = weighted_choice(rng, [((c, s, w), w) for c, s, w in CITIES])
        is_p2m = rng.random() < 0.62

        if is_p2m:
            category = weighted_choice(rng, category_weights)
            payee = rng.choice(merchants[category])
            low, high = MERCHANT_CATEGORIES[category][2]
            amount = make_amount(rng, low, high)
            remarks = f"Payment to {payee['name']}"
        else:
            category = "Peer Transfer"
            payee = rng.choice(people)
            while payee is payer:
                payee = rng.choice(people)
            amount = make_amount(rng, 10, 20000)
            remarks = rng.choice(P2P_PURPOSES)

        # Failures rise slightly late at night and for large amounts
        fail_rate = 0.055 + (0.03 if ts.hour < 5 else 0) + (0.03 if amount > 20000 else 0)
        roll = rng.random()
        if roll < fail_rate:
            status, reason = "FAILED", weighted_choice(rng, FAILURE_REASONS)
        elif roll < fail_rate + 0.012:
            status, reason = "PENDING", ""
        else:
            status, reason = "SUCCESS", ""

        pair = (payer["vpa"], payee["vpa"])
        first_time = "Yes" if pair not in seen_pairs else "No"
        seen_pairs.add(pair)

        rows.append({
            "transaction_id": f"UPI{ts:%y%m%d}{i:07d}",
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "date": ts.strftime("%Y-%m-%d"),
            "hour": ts.hour,
            "day_of_week": ts.strftime("%A"),
            "transaction_type": "P2M" if is_p2m else "P2P",
            "payer_name": payer["name"],
            "payer_vpa": payer["vpa"],
            "payer_bank": payer["bank"],
            "payee_name": payee["name"],
            "payee_vpa": payee["vpa"],
            "payee_bank": payee["bank"],
            "merchant_category": category,
            "amount_inr": amount,
            "status": status,
            "failure_reason": reason,
            "upi_app": weighted_choice(rng, UPI_APPS),
            "device_type": weighted_choice(rng, DEVICES),
            "city": city,
            "state": state,
            "is_first_time_payee": first_time,
            "remarks": remarks,
        })

    rows.sort(key=lambda r: r["timestamp"])
    return rows


def add_quality_issues(rows, rng):
    """Inject realistic messiness so data-quality checks have work to do."""
    n = len(rows)
    issues = {"missing_city": 0, "missing_app": 0, "messy_category": 0,
              "outlier_amount": 0, "duplicates": 0}

    for row in rng.sample(rows, k=n // 60):           # ~1.7% missing city/state
        row["city"], row["state"] = "", ""
        issues["missing_city"] += 1
    for row in rng.sample(rows, k=n // 100):          # ~1% missing UPI app
        row["upi_app"] = ""
        issues["missing_app"] += 1
    for row in rng.sample(rows, k=n // 80):           # inconsistent casing / spaces
        row["merchant_category"] = rng.choice(
            [row["merchant_category"].upper(), " " + row["merchant_category"].lower() + " "])
        issues["messy_category"] += 1
    for row in rng.sample(rows, k=max(3, n // 1000)): # suspiciously large amounts
        row["amount_inr"] = rng.choice([99999, 100000, 250000, 499999])
        issues["outlier_amount"] += 1
    for row in rng.sample(rows, k=max(5, n // 250)):  # exact duplicate rows
        rows.append(dict(row))
        issues["duplicates"] += 1

    rows.sort(key=lambda r: r["timestamp"])
    return issues


# ---------------------------------------------------------------- writers

def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _column_letter(index):
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _cell_xml(ref, value, style=0):
    style_attr = f' s="{style}"' if style else ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    if value == "":
        return ""
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t xml:space="preserve">{escape(str(value))}</t></is></c>'


def write_xlsx(rows, path, sheet_name="UPI Transactions"):
    """Minimal but valid .xlsx writer using only zipfile (bold, frozen header)."""
    sheet_rows = []
    header = "".join(_cell_xml(f"{_column_letter(c)}1", name, style=1)
                     for c, name in enumerate(COLUMNS))
    sheet_rows.append(f'<row r="1">{header}</row>')
    for r, row in enumerate(rows, start=2):
        cells = "".join(_cell_xml(f"{_column_letter(c)}{r}", row[name])
                        for c, name in enumerate(COLUMNS))
        sheet_rows.append(f'<row r="{r}">{cells}</row>')

    last_ref = f"{_column_letter(len(COLUMNS) - 1)}{len(rows) + 1}"
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{last_ref}"/>'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        '<cols><col min="1" max="22" width="20" customWidth="1"/></cols>'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        f'<autoFilter ref="A1:{last_ref}"/>'
        '</worksheet>'
    )
    files = {
        "[Content_Types].xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>',
        "_rels/.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        "xl/workbook.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
            '<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">'
            f"'{escape(sheet_name)}'!$A$1:${_column_letter(len(COLUMNS) - 1)}${len(rows) + 1}"
            '</definedName></definedNames></workbook>',
        "xl/_rels/workbook.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>',
        "xl/styles.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
            '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
            '<cellXfs count="2"><xf fontId="0"/><xf fontId="1" applyFont="1"/></cellXfs>'
            '</styleSheet>',
        "xl/worksheets/sheet1.xml": sheet_xml,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)


# ---------------------------------------------------------------- main

def main():
    n_rows = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROWS
    rng = random.Random(SEED)

    rows = generate_rows(n_rows, rng)
    issues = add_quality_issues(rows, rng)

    csv_path = OUTPUT_DIR / "upi_transactions.csv"
    xlsx_path = OUTPUT_DIR / "upi_transactions.xlsx"
    write_csv(rows, csv_path)
    write_xlsx(rows, xlsx_path)

    print(f"Wrote {len(rows):,} rows x {len(COLUMNS)} columns")
    print(f"  {csv_path.name}  ({csv_path.stat().st_size / 1024:,.0f} KB)")
    print(f"  {xlsx_path.name} ({xlsx_path.stat().st_size / 1024:,.0f} KB)")
    print("Injected quality issues:", issues)


if __name__ == "__main__":
    main()
