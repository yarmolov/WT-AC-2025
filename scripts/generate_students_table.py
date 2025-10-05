#!/usr/bin/env python3
"""
Generate Markdown table from students/students.csv and insert into README.md
between markers <!-- STUDENTS_TABLE_START --> and <!-- STUDENTS_TABLE_END -->.

Usage: python scripts/generate_students_table.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "students" / "students.csv"
README = ROOT / "README.md"

START_MARKER = "<!-- STUDENTS_TABLE_START -->"
END_MARKER = "<!-- STUDENTS_TABLE_END -->"

def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = [r for r in reader]
    return rows

def make_md_table(rows):
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    expected_cols = len(header)
    # check rows for column count mismatches; we'll normalize but report
    bad_rows = []
    for i, r in enumerate(body, start=2):
        if len(r) != expected_cols:
            bad_rows.append((i, len(r)))
    if bad_rows:
        print(f"Warning: CSV column count mismatch (expected {expected_cols} columns) - will normalize rows:")
        for lineno, cols in bad_rows[:20]:
            print(f"  line {lineno}: {cols} columns")
        if len(bad_rows) > 20:
            print(f"  ... and {len(bad_rows)-20} more")
    # sanitize pipes in cells
    def esc(cell):
        return cell.replace('|', '\\|') if cell is not None else ''
    # header
    out = []
    out.append('| ' + ' | '.join(esc(c) for c in header) + ' |')
    out.append('| ' + ' | '.join('---' for _ in header) + ' |')

    # find index of Github Username column (case-insensitive)
    gh_idx = None
    for idx, h in enumerate(header):
        if h and h.strip().lower() in ('github username', 'github_username', 'github'):
            gh_idx = idx
            break

    for r in body:
        # normalize row length: pad with empty strings or truncate
        if len(r) < expected_cols:
            r = r + [''] * (expected_cols - len(r))
        elif len(r) > expected_cols:
            r = r[:expected_cols]
        row = [esc(c) for c in r]
        # render github username as link if present
        if gh_idx is not None and gh_idx < len(row):
            uname = row[gh_idx].strip()
            if uname:
                # handle existing markdown links like [name](url)
                if '](' in uname and uname.count('](') >= 1:
                    # assume already a link; leave as-is
                    uname_clean = uname
                else:
                    # strip surrounding brackets and whitespace
                    uname_clean = uname.replace('[', '').replace(']', '').strip()
                    # if given a full URL, extract username
                    if uname_clean.startswith('http') or 'github.com/' in uname_clean:
                        # remove protocol and domain
                        parts = uname_clean.split('github.com/')
                        uname_clean = parts[-1].rstrip('/').strip()
                    # remove leading @ if present
                    if uname_clean.startswith('@'):
                        uname_clean = uname_clean[1:]
                    # keep only valid GitHub username chars (alphanumeric and hyphen)
                    import re
                    m = re.match(r"^([A-Za-z0-9\-]+)", uname_clean)
                    if m:
                        uname_clean = m.group(1)
                    else:
                        uname_clean = uname_clean
                    # produce markdown link
                    uname_clean = f"[{uname_clean}](https://github.com/{uname_clean})"
                row[gh_idx] = uname_clean
        out.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(out)


def main():
    rows = read_csv(CSV_PATH)
    table_md = make_md_table(rows)

    readme_text = README.read_text(encoding='utf-8')

    if START_MARKER in readme_text and END_MARKER in readme_text:
        before, rest = readme_text.split(START_MARKER, 1)
        _, after = rest.split(END_MARKER, 1)
        new_content = before + START_MARKER + '\n\n' + table_md + '\n\n' + END_MARKER + after
    else:
        # append at end
        new_content = readme_text + '\n\n' + START_MARKER + '\n\n' + table_md + '\n\n' + END_MARKER + '\n'

    README.write_text(new_content, encoding='utf-8')
    print(f"Updated {README} with table from {CSV_PATH}")

if __name__ == '__main__':
    main()
