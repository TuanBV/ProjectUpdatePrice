#!/usr/bin/env python3
"""Xóa các URL có chứa 'tin-tuc'/'sitemap'/'chinh-sach' khỏi urls.txt/urls.csv
trong sitemap_output/.

Duyệt từng dòng của urls.txt và từng dòng (row) của urls.csv trong mỗi
thư mục site, loại bỏ dòng nào có URL chứa một trong các từ khóa trên rồi
ghi đè lại file.

Cách chạy:
    python filter_tin_tuc_urls.py [thư_mục_sitemap_output]

File gốc được sao lưu thành <ten_file>.bak (chỉ ở lần chạy đầu tiên,
các lần chạy sau không ghi đè .bak) để có thể khôi phục nếu cần.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

DEFAULT_ROOT = "sitemap_output"
KEYWORDS = ["tin-tuc", "sitemap", "chinh-sach"]


def has_excluded_keyword(url: str) -> bool:
    lowered = url.lower()
    return any(keyword in lowered for keyword in KEYWORDS)


def backup_if_needed(path: Path) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_bytes(path.read_bytes())


def filter_urls_txt(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0

    backup_if_needed(path)

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    kept = [line for line in lines if line.strip() and not has_excluded_keyword(line)]
    removed = len(lines) - len(kept)

    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8-sig")
    return len(lines), removed


def filter_urls_csv(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0

    backup_if_needed(path)

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    kept_rows = [row for row in rows if not has_excluded_keyword(row.get("loc") or "")]
    removed = len(rows) - len(kept_rows)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)

    return len(rows), removed


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT)
    if not root.exists():
        print(f"Không tìm thấy thư mục: {root}")
        return

    site_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    if not site_dirs:
        print(f"Không có thư mục site nào trong {root}")
        return

    keywords_label = ", ".join(f"'{k}'" for k in KEYWORDS)
    print(f"Lọc URL chứa {keywords_label} trong {len(site_dirs)} site...")

    total_removed = 0
    for site_dir in site_dirs:
        total_txt, removed_txt = filter_urls_txt(site_dir / "urls.txt")
        total_csv, removed_csv = filter_urls_csv(site_dir / "urls.csv")
        total_removed += removed_txt
        print(
            f"- {site_dir.name}: urls.txt xóa {removed_txt}/{total_txt}, "
            f"urls.csv xóa {removed_csv}/{total_csv}"
        )

    print(f"\nTổng URL đã xóa (urls.txt): {total_removed}")
    print("Bản gốc đã lưu dạng .bak (nếu là lần chạy đầu) để có thể khôi phục.")


if __name__ == "__main__":
    main()
