#!/usr/bin/env python3
"""
Lấy toàn bộ URL từ sitemap của các website đối thủ trong danh-sach-doi-thu.txt,
lọc bỏ URL chứa 'tin-tuc', rồi gộp mỗi site thành một file <ten_site>.txt.
Chạy 1 lần là ra đủ kết quả, không cần chạy thêm file nào khác.

Cách chạy (đọc danh sách, chạy toàn bộ site):
    python get_site_map.py

Chỉ định file danh sách / thư mục đầu ra khác:
    python get_site_map.py --list danh-sach-doi-thu.txt --output-dir sitemap_output

Chạy 1 site duy nhất (bỏ qua danh sách), giữ tương thích cách dùng cũ:
    python get_site_map.py https://dienmaythienphu.vn/sitemap.xml dienmaythienphu_sitemap_output

Kết quả cho mỗi site (thư mục con sitemap_output/<ten_site>/):
    - sitemap_files.txt          : toàn bộ sitemap/index đã đọc
    - urls.txt / urls.csv        : URL sản phẩm (đã lọc bỏ URL chứa 'tin-tuc')
    - urls.txt.bak / urls.csv.bak: bản gốc trước khi lọc (chỉ tạo ở lần lọc đầu tiên)
    - errors.txt                 : các sitemap không đọc được (nếu có)
Và ở gốc thư mục đầu ra:
    - all_sites_summary.csv      : tổng hợp số liệu từng site
    - <ten_site>.txt              : gộp 4 file trên, chỉ giữ dòng URL https, đã loại trùng
"""
from __future__ import annotations

import argparse
import csv
import gzip
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

DEFAULT_LIST_FILE = "danh-sach-doi-thu.txt"
DEFAULT_OUTPUT_DIR = "sitemap_output"

SITEMAP_CANDIDATE_PATHS = ["sitemap.xml", "sitemap_index.xml", "wp-sitemap.xml"]

# Từ khóa loại bỏ khỏi urls.txt/urls.csv/file gộp: tin tức/tư vấn, sitemap XML,
# trang chính sách - đều không phải trang sản phẩm.
EXCLUDE_KEYWORDS = ["tin-tuc", "sitemap", "chinh-sach"]

HTTPS_PREFIX = "https:"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/150.0 Safari/537.36 SitemapCollector/1.0"
)


def local_name(tag: str) -> str:
    """Bỏ namespace XML, ví dụ {namespace}loc -> loc."""
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def fetch(url: str, retries: int = 3, timeout: int = 35) -> bytes:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/xml,text/xml,text/plain,*/*;q=0.8",
        "Accept-Encoding": "gzip",
        "Cache-Control": "no-cache",
    }

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
                content_encoding = (response.headers.get("Content-Encoding") or "").lower()
                content_type = (response.headers.get("Content-Type") or "").lower()

                if "gzip" in content_encoding or url.lower().endswith(".gz"):
                    try:
                        data = gzip.decompress(data)
                    except OSError:
                        # Một số server đã tự giải nén nhưng vẫn giữ header hoặc URL .gz
                        pass

                # Phòng trường hợp gzip được trả về mà không có header đúng.
                if data[:2] == b"\x1f\x8b":
                    data = gzip.decompress(data)

                if response.status >= 400:
                    raise RuntimeError(
                        f"HTTP {response.status}; Content-Type={content_type}"
                    )
                return data

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)

    raise RuntimeError(f"Không tải được {url}: {last_error}")


def parse_sitemap(xml_bytes: bytes) -> tuple[str, list[dict[str, str]]]:
    # Loại BOM/khoảng trắng trước XML.
    xml_bytes = xml_bytes.lstrip(b"\xef\xbb\xbf \t\r\n")
    root = ET.fromstring(xml_bytes)
    root_type = local_name(root.tag)

    if root_type == "sitemapindex":
        children: list[dict[str, str]] = []
        for item in root:
            if local_name(item.tag) != "sitemap":
                continue
            loc = child_text(item, "loc")
            if loc:
                children.append(
                    {
                        "loc": loc,
                        "lastmod": child_text(item, "lastmod"),
                    }
                )
        return "index", children

    if root_type == "urlset":
        urls: list[dict[str, str]] = []
        for item in root:
            if local_name(item.tag) != "url":
                continue
            loc = child_text(item, "loc")
            if loc:
                urls.append(
                    {
                        "loc": loc,
                        "lastmod": child_text(item, "lastmod"),
                        "changefreq": child_text(item, "changefreq"),
                        "priority": child_text(item, "priority"),
                    }
                )
        return "urlset", urls

    raise ValueError(f"Không nhận diện được XML root: {root.tag}")


def write_lines(path: Path, values: Iterable[str]) -> None:
    path.write_text("\n".join(values) + "\n", encoding="utf-8-sig")


# ---------------------------------------------------------------------------
# Danh sách đối thủ + dò tìm sitemap khởi đầu cho từng domain
# ---------------------------------------------------------------------------

def load_domain_list(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file danh sách: {path}")

    domains = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        domains.append(line)
    return domains


def normalize_domain(line: str) -> tuple[str, str]:
    """Trả về (base_url, nhãn hiển thị/tên thư mục) từ một dòng trong danh sách."""
    if re.match(r"^https?://", line, re.IGNORECASE):
        base_url = line.rstrip("/")
        label = urlparse(base_url).netloc or line
    else:
        label = line
        base_url = f"https://{line.rstrip('/')}"
    return base_url, label


def sanitize_label(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", label).strip("_") or "site"


def discover_sitemap_urls(base_url: str) -> list[str]:
    """Tìm sitemap khởi đầu: ưu tiên robots.txt, fallback các đường dẫn phổ biến."""
    found: list[str] = []

    try:
        robots = fetch(f"{base_url}/robots.txt").decode("utf-8", errors="replace")
    except Exception:
        robots = ""

    if robots:
        for match in re.finditer(r"^\s*Sitemap:\s*(\S+)\s*$", robots, re.IGNORECASE | re.MULTILINE):
            sitemap_url = match.group(1).strip()
            if sitemap_url not in found:
                found.append(sitemap_url)

    if found:
        return found

    for path in SITEMAP_CANDIDATE_PATHS:
        candidate = f"{base_url}/{path}"
        try:
            data = fetch(candidate)
            parse_sitemap(data)
        except Exception:
            continue
        found.append(candidate)
        break

    return found


# ---------------------------------------------------------------------------
# Thu thập đệ quy sitemap cho một site
# ---------------------------------------------------------------------------

def collect(start_urls: list[str], output_dir: Path, label: str) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    queue: deque[str] = deque(start_urls)
    queued = set(start_urls)
    processed: list[str] = []
    errors: list[str] = []

    # Dùng dict để giữ thứ tự và loại URL trùng.
    urls_by_loc: dict[str, dict[str, str]] = {}

    while queue:
        sitemap_url = queue.popleft()
        print(f"[{label}] [SITEMAP] {sitemap_url}")

        try:
            data = fetch(sitemap_url)
            kind, items = parse_sitemap(data)
            processed.append(sitemap_url)

            if kind == "index":
                print(f"[{label}]           -> {len(items):,} sitemap con")
                for item in items:
                    child_url = item["loc"]
                    if child_url not in queued:
                        queue.append(child_url)
                        queued.add(child_url)
            else:
                print(f"[{label}]           -> {len(items):,} URL")
                for item in items:
                    loc = item["loc"]
                    if loc not in urls_by_loc:
                        urls_by_loc[loc] = {
                            "loc": loc,
                            "lastmod": item.get("lastmod", ""),
                            "changefreq": item.get("changefreq", ""),
                            "priority": item.get("priority", ""),
                            "source_sitemap": sitemap_url,
                        }

        except Exception as exc:
            message = f"{sitemap_url}\t{type(exc).__name__}: {exc}"
            errors.append(message)
            print(f"[{label}] [LỖI]    {message}", file=sys.stderr)

    write_lines(output_dir / "sitemap_files.txt", processed)
    write_lines(output_dir / "urls.txt", urls_by_loc.keys())

    with (output_dir / "urls.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "loc",
                "lastmod",
                "changefreq",
                "priority",
                "source_sitemap",
            ],
        )
        writer.writeheader()
        writer.writerows(urls_by_loc.values())

    write_lines(output_dir / "errors.txt", errors)

    print(f"\n[{label}] HOÀN TẤT")
    print(f"[{label}] - Sitemap đã đọc : {len(processed):,}")
    print(f"[{label}] - URL duy nhất    : {len(urls_by_loc):,}")
    print(f"[{label}] - Sitemap lỗi     : {len(errors):,}")
    print(f"[{label}] - Thư mục kết quả : {output_dir.resolve()}")

    if errors:
        print(
            f"[{label}] Có sitemap lỗi. Hãy mở errors.txt để kiểm tra; "
            "có thể chạy lại do website giới hạn tần suất hoặc timeout."
        )

    return {
        "sitemap_count": len(processed),
        "url_count": len(urls_by_loc),
        "error_count": len(errors),
    }


def write_summary(base_output: Path, rows: list[dict[str, object]]) -> None:
    with (base_output / "all_sites_summary.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["domain", "sitemap_count", "url_count", "error_count", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Lọc bỏ URL chứa 'tin-tuc' khỏi urls.txt / urls.csv (bản gốc sao lưu .bak)
# ---------------------------------------------------------------------------

def backup_if_needed(path: Path) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_bytes(path.read_bytes())


def has_excluded_keyword(url: str, keywords: list[str] = EXCLUDE_KEYWORDS) -> bool:
    lowered = url.lower()
    return any(keyword in lowered for keyword in keywords)


def filter_urls_txt(path: Path, keywords: list[str] = EXCLUDE_KEYWORDS) -> tuple[int, int]:
    if not path.exists():
        return 0, 0

    backup_if_needed(path)

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    kept = [line for line in lines if line.strip() and not has_excluded_keyword(line, keywords)]
    removed = len(lines) - len(kept)

    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8-sig")
    return len(lines), removed


def filter_urls_csv(path: Path, keywords: list[str] = EXCLUDE_KEYWORDS) -> tuple[int, int]:
    if not path.exists():
        return 0, 0

    backup_if_needed(path)

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    kept_rows = [row for row in rows if not has_excluded_keyword(row.get("loc") or "", keywords)]
    removed = len(rows) - len(kept_rows)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)

    return len(rows), removed


def filter_site_dir(site_dir: Path, label: str) -> None:
    total_txt, removed_txt = filter_urls_txt(site_dir / "urls.txt")
    total_csv, removed_csv = filter_urls_csv(site_dir / "urls.csv")
    keywords_label = ", ".join(f"'{k}'" for k in EXCLUDE_KEYWORDS)
    print(
        f"[{label}] Lọc {keywords_label}: urls.txt xóa {removed_txt}/{total_txt}, "
        f"urls.csv xóa {removed_csv}/{total_csv}"
    )


# ---------------------------------------------------------------------------
# Gộp sitemap_files.txt/urls.csv/urls.txt/errors.txt thành một file <site>.txt
# ---------------------------------------------------------------------------

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


def merge_site_files(site_dir: Path, output_path: Path) -> int:
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


def process_site_dir(site_dir: Path, output_path: Path, label: str) -> None:
    """Lọc 'tin-tuc' rồi gộp 4 file của một site thành output_path, theo đúng thứ tự cũ."""
    filter_site_dir(site_dir, label)
    merged_count = merge_site_files(site_dir, output_path)
    print(f"[{label}] Gộp file -> {output_path} ({merged_count} URL)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thu thập sitemap, lọc 'tin-tuc' và gộp file cho danh sách đối thủ."
    )
    parser.add_argument(
        "sitemap",
        nargs="?",
        default=None,
        help="URL sitemap cụ thể - nếu truyền vào thì chỉ chạy 1 site này, bỏ qua --list.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Thư mục đầu ra khi chạy 1 sitemap cụ thể ở trên.",
    )
    parser.add_argument(
        "--list",
        default=DEFAULT_LIST_FILE,
        help=f"File danh sách domain đối thủ, mỗi dòng một domain (mặc định: {DEFAULT_LIST_FILE}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Thư mục gốc chứa kết quả từng site (mặc định: {DEFAULT_OUTPUT_DIR}).",
    )
    args = parser.parse_args()

    if args.sitemap:
        # Chế độ tương thích ngược: chạy đúng 1 sitemap được chỉ định.
        label = sanitize_label(urlparse(args.sitemap).netloc or args.sitemap)
        output_dir = Path(args.output or f"{label}_sitemap_output")
        collect([args.sitemap], output_dir, label)
        process_site_dir(output_dir, output_dir.parent / f"{label}.txt", label)
        return

    domains = load_domain_list(Path(args.list))
    if not domains:
        print(f"Danh sách {args.list} rỗng, không có gì để chạy.")
        return

    base_output = Path(args.output_dir)
    base_output.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []

    for domain in domains:
        base_url, label = normalize_domain(domain)
        folder_name = sanitize_label(label)
        print(f"\n=== {label} ({base_url}) ===")

        start_urls = discover_sitemap_urls(base_url)
        if not start_urls:
            print(f"[{label}] [CẢNH BÁO] Không tìm được sitemap (robots.txt lẫn đường dẫn mặc định), bỏ qua.")
            summary_rows.append({
                "domain": label,
                "sitemap_count": 0,
                "url_count": 0,
                "error_count": 0,
                "status": "NO_SITEMAP_FOUND",
            })
            continue

        stats = collect(start_urls, base_output / folder_name, label)
        process_site_dir(base_output / folder_name, base_output / f"{folder_name}.txt", label)

        summary_rows.append({
            "domain": label,
            "sitemap_count": stats["sitemap_count"],
            "url_count": stats["url_count"],
            "error_count": stats["error_count"],
            "status": "OK",
        })

    write_summary(base_output, summary_rows)

    print("\n=== TỔNG KẾT TOÀN BỘ DANH SÁCH ===")
    total_urls = 0
    for row in summary_rows:
        print(
            f"- {row['domain']}: {row['status']}, "
            f"{row['sitemap_count']} sitemap, {row['url_count']} URL, {row['error_count']} lỗi"
        )
        total_urls += int(row["url_count"])
    print(f"Tổng URL thu được: {total_urls:,}")
    print(f"Thư mục kết quả  : {base_output.resolve()}")
    print(f"File tổng hợp    : {(base_output / 'all_sites_summary.csv').resolve()}")


if __name__ == "__main__":
    main()
