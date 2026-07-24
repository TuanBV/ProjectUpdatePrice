#!/usr/bin/env python3
"""Gộp errors.txt, sitemap_files.txt, urls.csv, urls.txt của mỗi site trong
sitemap_output/<ten_thu_muc>/ thành một file <ten_thu_muc>.txt duy nhất,
chỉ giữ lại các dòng là URL https (bỏ dòng lỗi, header CSV, cột metadata).

Cách chạy:
    python merge_sitemap_files.py [thư_mục_sitemap_output]

Kết quả: sitemap_output/<ten_thu_muc>.txt cho từng site (URL đã loại trùng).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

DEFAULT_ROOT = "sitemap_output"
HTTPS_PREFIX = "https:"
EXCLUDE_KEYWORDS = ["tin-tuc", "sitemap", "chinh-sach"]


def has_excluded_keyword(url: str) -> bool:
    lowered = url.lower()
    return any(keyword in lowered for keyword in EXCLUDE_KEYWORDS)


def collect_urls_from_plain_txt(path: Path) -> list[str]:
    if not path.exists():
        return []
    urls = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.lower().startswith(HTTPS_PREFIX):
            urls.append(line)
    return urls


def collect_urls_from_csv(path: Path) -> list[str]:
    if not path.exists():
        return []
    urls = []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            loc = (row.get("loc") or "").strip()
            if loc.lower().startswith(HTTPS_PREFIX):
                urls.append(loc)
    return urls


def collect_urls_from_errors(path: Path) -> list[str]:
    if not path.exists():
        return []
    urls = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        first_field = line.split("\t", 1)[0].strip()
        if first_field.lower().startswith(HTTPS_PREFIX):
            urls.append(first_field)
    return urls


def merge_site(site_dir: Path, output_path: Path) -> int:
    seen: set[str] = set()
    ordered: list[str] = []

    def add_all(urls: list[str]) -> None:
        for url in urls:
            if url not in seen and not has_excluded_keyword(url):
                seen.add(url)
                ordered.append(url)

    add_all(collect_urls_from_plain_txt(site_dir / "urls.txt"))
    add_all(collect_urls_from_csv(site_dir / "urls.csv"))
    add_all(collect_urls_from_plain_txt(site_dir / "sitemap_files.txt"))
    add_all(collect_urls_from_errors(site_dir / "errors.txt"))

    output_path.write_text("\n".join(ordered) + ("\n" if ordered else ""), encoding="utf-8-sig")
    return len(ordered)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT)
    if not root.exists():
        print(f"Không tìm thấy thư mục: {root}")
        return

    site_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    if not site_dirs:
        print(f"Không có thư mục site nào trong {root}")
        return

    print(f"Gộp file cho {len(site_dirs)} site (chỉ giữ dòng https)...")

    for site_dir in site_dirs:
        output_path = root / f"{site_dir.name}.txt"
        count = merge_site(site_dir, output_path)
        print(f"- {site_dir.name}: {count} URL -> {output_path}")


if __name__ == "__main__":
    main()
