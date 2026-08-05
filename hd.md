# XÂY DỰNG HỆ THỐNG THU THẬP VÀ SO SÁNH GIÁ SẢN PHẨM TỪ ĐẦU

Bạn là một Senior Software Architect, Senior Python Backend Engineer và Data Engineer.

Hãy xây dựng từ đầu một hệ thống hoàn chỉnh để thu thập thông tin sản phẩm từ các website đối thủ, chuẩn hóa dữ liệu, ghép sản phẩm theo SKU/model, kiểm tra chất lượng dữ liệu và xuất báo cáo so sánh giá.

Không được chỉ viết một script crawl đơn giản. Hệ thống phải được thiết kế thành một pipeline có thể chạy lại, tiếp tục khi bị gián đoạn, kiểm tra được dữ liệu sai và dễ mở rộng thêm website mới.

---

# 1. Bối cảnh nghiệp vụ

Doanh nghiệp có danh mục sản phẩm nội bộ, bao gồm:

* Tên sản phẩm.
* SKU hoặc mã model.
* Thương hiệu.
* Danh mục.
* Giá bán hiện tại.
* Giá tối thiểu cho phép.
* Trạng thái tồn kho.
* URL sản phẩm nội bộ nếu có.

Cần thu thập dữ liệu từ các website đối thủ, ban đầu gồm:

```text
sgt.com.vn
dienmay88.vn
dienmaythienphu.vn
dienmayabc.com
```

Danh sách website phải được cấu hình bên ngoài mã nguồn để có thể thêm hoặc loại bỏ website mà không cần sửa logic chương trình.

Dữ liệu cần thu thập từ đối thủ:

* Tên sản phẩm.
* SKU/model.
* Thương hiệu.
* Danh mục.
* URL sản phẩm.
* Giá niêm yết.
* Giá khuyến mãi.
* Giá thực tế dùng để so sánh.
* Trạng thái còn hàng, hết hàng hoặc liên hệ.
* Thời gian crawl.
* Website nguồn.
* Trạng thái crawl.
* Lý do lỗi nếu có.

Mục tiêu cuối cùng là tạo được bảng dữ liệu đáng tin cậy để biết:

* Giá sản phẩm nội bộ.
* Giá tối thiểu nội bộ.
* Giá của từng đối thủ.
* Giá thấp nhất trên thị trường.
* Đối thủ đang bán thấp nhất.
* Chênh lệch giá.
* Sản phẩm nào chưa ghép được với đối thủ.
* Sản phẩm nào có dữ liệu đáng nghi ngờ.
* Sản phẩm nào cần kiểm tra thủ công.

---

# 2. Mục tiêu tổng thể

Xây dựng pipeline hoàn chỉnh:

```text
Phân tích yêu cầu
        ↓
Khảo sát website
        ↓
Thiết kế kiến trúc
        ↓
Thu thập sitemap và URL sản phẩm
        ↓
Crawl nội dung sản phẩm
        ↓
Trích xuất dữ liệu thô
        ↓
Chuẩn hóa dữ liệu
        ↓
Xác định SKU/model
        ↓
Ghép sản phẩm giữa các nguồn
        ↓
Kiểm tra chất lượng dữ liệu
        ↓
Đối soát và phát hiện bất thường
        ↓
Lưu dữ liệu
        ↓
Xuất báo cáo Excel
        ↓
Triển khai và vận hành định kỳ
```

Hệ thống phải ưu tiên độ chính xác của dữ liệu hơn số lượng URL crawl được.

---

# 3. Nguyên tắc triển khai

Tuân thủ các nguyên tắc sau:

1. Không hard-code logic của tất cả website vào một file duy nhất.

2. Mỗi website phải có một adapter hoặc parser riêng.

3. Phần lấy dữ liệu, chuẩn hóa dữ liệu, ghép sản phẩm và xuất báo cáo phải tách biệt.

4. Không coi mọi URL trong sitemap là URL sản phẩm.

5. Không coi mọi số tiền xuất hiện trên trang là giá sản phẩm.

6. Không tự động ghép hai sản phẩm chỉ vì tên gần giống nhau.

7. Mọi bản ghi phải lưu nguồn, thời gian crawl và mức độ tin cậy.

8. Dữ liệu không chắc chắn phải được đưa vào danh sách kiểm tra thủ công.

9. Hệ thống phải chạy lại an toàn mà không tạo dữ liệu trùng.

10. Hệ thống phải tiếp tục được sau khi bị dừng giữa chừng.

11. Tôn trọng `robots.txt`, giới hạn tốc độ truy cập và điều khoản sử dụng của website.

12. Không thu thập thông tin tài khoản, dữ liệu cá nhân hoặc dữ liệu không cần thiết cho nghiệp vụ so sánh giá.

---

# 4. Giai đoạn 1 — Phân tích yêu cầu

Trước khi viết code, hãy tạo tài liệu phân tích bao gồm:

## 4.1. Input

Xác định chính xác các nguồn đầu vào:

* File danh mục sản phẩm nội bộ.
* File giá tối thiểu.
* File danh sách website đối thủ.
* Các cột bắt buộc trong từng file.
* Định dạng dữ liệu.
* Cột nào có thể thiếu.
* Cột nào được dùng làm khóa.

## 4.2. Output

Thiết kế file báo cáo cuối với ít nhất các cột:

```text
internal_product_id
internal_product_name
brand
model
category
internal_price
minimum_price

sgt_price
sgt_url
sgt_status

dienmay88_price
dienmay88_url
dienmay88_status

dienmaythienphu_price
dienmaythienphu_url
dienmaythienphu_status

dienmayabc_price
dienmayabc_url
dienmayabc_status

lowest_competitor_price
lowest_competitor
price_difference
match_confidence
data_quality_status
last_crawled_at
review_note
```

## 4.3. Quy tắc nghiệp vụ

Làm rõ và triển khai các quy tắc:

* Giá nào được dùng để so sánh khi có cả giá cũ và giá sale.
* Cách xử lý giá bằng `Liên hệ`.
* Cách xử lý sản phẩm hết hàng.
* Cách xử lý một website có nhiều URL cho cùng model.
* Cách xử lý sản phẩm có nhiều biến thể dung lượng, màu sắc hoặc công suất.
* Cách xử lý giá bằng 0 hoặc giá thiếu.
* Cách xử lý sản phẩm combo, phụ kiện hoặc quà tặng.
* Cách xử lý sản phẩm cùng tên nhưng khác model.
* Cách tính chênh lệch giữa giá nội bộ và giá thấp nhất của đối thủ.

Nếu chưa đủ thông tin nghiệp vụ, hãy đưa các quy tắc này vào file cấu hình để có thể chỉnh sửa mà không sửa code.

---

# 5. Giai đoạn 2 — Khảo sát từng website

Trước khi xây parser, hãy khảo sát từng website và lập tài liệu:

* Có `robots.txt` hay không.
* Có sitemap hay không.
* Sitemap là sitemap index hay sitemap URL.
* Sitemap có nén GZIP hay không.
* Sitemap có chia theo sản phẩm, bài viết và danh mục hay không.
* Mẫu URL sản phẩm.
* Mẫu URL danh mục.
* Cấu trúc trang sản phẩm.
* Có JSON-LD `Product` hay không.
* Có dữ liệu giá trong HTML hay được tải bằng JavaScript.
* Có API nội bộ trả dữ liệu sản phẩm hay không.
* Có chống bot, CAPTCHA hoặc rate limit hay không.
* Cách biểu diễn giá thường, giá sale, giá liên hệ và hết hàng.
* Cách tìm SKU/model.
* Cách xác định thương hiệu.
* Cách xác định trạng thái còn hàng.

Tạo một tài liệu riêng cho từng website trong:

```text
docs/sites/
```

Ví dụ:

```text
docs/sites/sgt.com.vn.md
docs/sites/dienmay88.vn.md
docs/sites/dienmaythienphu.vn.md
docs/sites/dienmayabc.com.md
```

Không bắt đầu viết parser chính thức trước khi hoàn thành khảo sát.

---

# 6. Giai đoạn 3 — Thiết kế kiến trúc

Thiết kế project theo kiến trúc module rõ ràng.

Cấu trúc tham khảo:

```text
project/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   ├── settings.yaml
│   ├── competitors.yaml
│   ├── matching_rules.yaml
│   └── category_mapping.yaml
├── data/
│   ├── input/
│   ├── raw/
│   ├── processed/
│   ├── output/
│   └── review/
├── docs/
│   ├── architecture.md
│   ├── data-flow.md
│   ├── operations.md
│   └── sites/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── logging_config.py
│   ├── models/
│   │   ├── product.py
│   │   ├── crawl_task.py
│   │   └── match_result.py
│   ├── discovery/
│   │   ├── robots_parser.py
│   │   ├── sitemap_parser.py
│   │   ├── url_classifier.py
│   │   └── category_discovery.py
│   ├── crawler/
│   │   ├── http_client.py
│   │   ├── crawl_queue.py
│   │   ├── retry_policy.py
│   │   └── crawler_service.py
│   ├── parsers/
│   │   ├── base_parser.py
│   │   ├── sgt_parser.py
│   │   ├── dienmay88_parser.py
│   │   ├── dienmaythienphu_parser.py
│   │   └── dienmayabc_parser.py
│   ├── normalization/
│   │   ├── text_normalizer.py
│   │   ├── price_normalizer.py
│   │   ├── brand_normalizer.py
│   │   ├── model_extractor.py
│   │   └── category_normalizer.py
│   ├── matching/
│   │   ├── exact_matcher.py
│   │   ├── fuzzy_matcher.py
│   │   ├── matching_service.py
│   │   └── confidence_calculator.py
│   ├── validation/
│   │   ├── schema_validator.py
│   │   ├── price_validator.py
│   │   ├── anomaly_detector.py
│   │   └── quality_service.py
│   ├── storage/
│   │   ├── database.py
│   │   ├── repositories.py
│   │   └── migrations/
│   └── reporting/
│       ├── excel_exporter.py
│       ├── summary_report.py
│       └── review_exporter.py
├── tests/
│   ├── fixtures/
│   ├── unit/
│   └── integration/
└── scripts/
    ├── discover_urls.py
    ├── crawl_products.py
    ├── match_products.py
    ├── validate_data.py
    └── export_report.py
```

Có thể điều chỉnh cấu trúc nếu có lý do kỹ thuật hợp lý, nhưng phải giữ nguyên nguyên tắc phân tách trách nhiệm.

---

# 7. Giai đoạn 4 — Thiết kế dữ liệu

Sử dụng SQLite cho bản chạy đầu tiên. Thiết kế để sau này có thể chuyển sang PostgreSQL.

Không sử dụng Excel làm hàng đợi crawl hoặc cơ sở dữ liệu chính.

Tạo các bảng tối thiểu:

## `competitor_sites`

```text
id
name
domain
enabled
rate_limit
parser_name
created_at
updated_at
```

## `discovered_urls`

```text
id
site_id
url
url_hash
source_type
source_url
url_type
discovered_at
last_seen_at
is_active
```

`url_type` có thể là:

```text
PRODUCT
CATEGORY
ARTICLE
POLICY
SITEMAP
UNKNOWN
```

## `crawl_tasks`

```text
id
site_id
url_id
status
priority
retry_count
next_retry_at
last_error
http_status
started_at
completed_at
created_at
updated_at
```

Trạng thái:

```text
PENDING
PROCESSING
DONE
RETRY
SKIPPED
FAILED
```

## `raw_crawl_results`

```text
id
site_id
url_id
http_status
content_hash
html_path
response_time_ms
crawled_at
parser_version
```

## `competitor_products`

```text
id
site_id
url
source_product_id
raw_name
normalized_name
brand
raw_model
normalized_model
category
list_price
sale_price
effective_price
currency
stock_status
price_status
data_confidence
first_seen_at
last_seen_at
last_crawled_at
content_hash
is_active
```

## `internal_products`

```text
id
source_id
sku
raw_name
normalized_name
brand
model
category
internal_price
minimum_price
stock_status
source_file
updated_at
```

## `product_matches`

```text
id
internal_product_id
competitor_product_id
match_type
match_score
model_score
brand_score
name_score
category_score
status
review_note
created_at
updated_at
```

Trạng thái ghép:

```text
AUTO_APPROVED
REVIEW_REQUIRED
REJECTED
MANUALLY_APPROVED
```

## `price_history`

```text
id
competitor_product_id
list_price
sale_price
effective_price
stock_status
observed_at
```

## `data_quality_issues`

```text
id
entity_type
entity_id
issue_code
severity
description
detected_at
resolved_at
```

Bổ sung index và unique constraint phù hợp để tránh dữ liệu trùng.

---

# 8. Giai đoạn 5 — Thu thập URL sản phẩm

Xây dựng module discovery theo thứ tự:

```text
robots.txt
    ↓
sitemap được khai báo
    ↓
các sitemap phổ biến
    ↓
sitemap index
    ↓
sitemap sản phẩm
    ↓
trang danh mục nếu sitemap không đủ
```

Hỗ trợ:

* XML sitemap.
* Sitemap index.
* GZIP sitemap.
* Sitemap lồng nhau.
* Namespace XML.
* URL trùng lặp.
* Sitemap lỗi.
* Redirect.
* Encoding khác UTF-8.
* Retry với exponential backoff.

Không giới hạn cứng 100 sitemap nếu chưa có lý do. Giới hạn phải được cấu hình.

Tạo bộ phân loại URL dựa trên:

* Regex URL.
* Segment URL.
* Sitemap nguồn.
* Từ khóa loại trừ.
* HTTP content type.
* Kiểm tra HTML nếu cần.

Các URL chứa nội dung sau không được mặc định coi là sản phẩm:

```text
tin-tuc
blog
news
chinh-sach
gioi-thieu
lien-he
tuyen-dung
tag
author
search
cart
checkout
sitemap
feed
```

Mọi URL phải được chuẩn hóa trước khi lưu:

* Bỏ fragment.
* Chuẩn hóa scheme và hostname.
* Xử lý dấu `/` cuối.
* Loại tracking parameter.
* Sắp xếp query parameter nếu cần.
* Tạo hash để chống trùng.

---

# 9. Giai đoạn 6 — HTTP crawler

Xây dựng HTTP client dùng chung với:

* Connection pooling.
* Timeout cấu hình được.
* Retry.
* Exponential backoff.
* Random jitter.
* User-Agent hợp lệ.
* Rate limit riêng cho từng domain.
* Kiểm soát số request đồng thời.
* Ghi nhận thời gian response.
* Xử lý redirect.
* Xử lý HTTP 403, 404, 429 và 5xx.
* Circuit breaker cơ bản nếu website lỗi liên tục.

Không retry vô hạn.

Quy tắc tham khảo:

```text
404: không retry nhiều lần
429: đọc Retry-After và retry có giới hạn
500/502/503/504: retry có backoff
403: dừng hoặc giảm tốc độ, không cố vượt cơ chế bảo vệ
timeout: retry có giới hạn
parse error: lưu HTML để debug
```

Nếu trang cần JavaScript mới hiển thị dữ liệu:

1. Kiểm tra JSON-LD.
2. Kiểm tra API/XHR công khai được trang sử dụng.
3. Chỉ sử dụng Playwright khi HTTP request thông thường không đủ.
4. Không dùng browser automation cho mọi URL nếu không cần thiết.

Lưu snapshot HTML cho:

* Trang parse lỗi.
* Trang có dữ liệu bất thường.
* Một số trang mẫu dùng cho test.
* Không nhất thiết lưu toàn bộ HTML nếu dung lượng quá lớn.

---

# 10. Giai đoạn 7 — Parser theo từng website

Tạo interface chung:

```python
class BaseProductParser:
    def is_product_page(self, html: str, url: str) -> bool:
        ...

    def parse_product(self, html: str, url: str) -> ParsedProduct:
        ...
```

Mỗi website có parser riêng.

Parser phải ưu tiên nguồn dữ liệu theo thứ tự:

1. JSON-LD `Product`.
2. Microdata/schema.org.
3. Meta tags.
4. HTML selector riêng của website.
5. Regex chỉ dùng như phương án cuối.

Trích xuất:

```text
product_name
brand
model
sku
category
list_price
sale_price
effective_price
currency
stock_status
source_product_id
```

Mọi trường phải lưu thêm thông tin nguồn nếu cần:

```text
price_source = JSON_LD
price_source = HTML_SELECTOR
price_source = META
price_source = REGEX
```

Không được lấy một số tiền bất kỳ làm giá sản phẩm.

Phải loại trừ:

* Giá trả góp mỗi tháng.
* Số tiền tiết kiệm.
* Giá quà tặng.
* Giá của sản phẩm liên quan.
* Giá trong menu.
* Giá của biến thể khác.
* Số điện thoại.
* Mã sản phẩm bị hiểu nhầm thành giá.

---

# 11. Giai đoạn 8 — Xử lý giá

Xây dựng hàm chuẩn hóa giá hỗ trợ:

```text
12.990.000₫
12,990,000 VND
12 990 000
12.990.000
Liên hệ
Call
Hết hàng
```

Kết quả chuẩn hóa:

```text
list_price: Decimal | None
sale_price: Decimal | None
effective_price: Decimal | None
price_status: AVAILABLE | CONTACT | MISSING | INVALID
currency: VND
```

Quy tắc `effective_price`:

```text
Nếu sale_price hợp lệ và nhỏ hơn hoặc bằng list_price:
    effective_price = sale_price

Nếu chỉ có list_price:
    effective_price = list_price

Nếu giá là Liên hệ:
    effective_price = null
    price_status = CONTACT

Nếu sale_price lớn hơn list_price:
    đánh dấu dữ liệu bất thường
    không tự động tin tưởng
```

Sử dụng `Decimal`, không sử dụng `float` để xử lý giá tiền.

---

# 12. Giai đoạn 9 — Chuẩn hóa dữ liệu sản phẩm

Chuẩn hóa tên sản phẩm:

* Chuyển Unicode về dạng thống nhất.
* Chuyển chữ thường để so sánh.
* Loại khoảng trắng thừa.
* Chuẩn hóa dấu gạch nối.
* Loại từ marketing không ảnh hưởng đến model.
* Giữ lại thông số quan trọng.
* Không loại bỏ dung lượng, công suất, kích thước hoặc mã model.

Danh sách từ marketing có thể cấu hình:

```text
chính hãng
giá rẻ
khuyến mãi
mới 100%
trả góp 0%
giao hàng miễn phí
bảo hành chính hãng
```

Chuẩn hóa thương hiệu:

```text
LG Electronics → LG
Samsung Việt Nam → Samsung
Daikin Vietnam → Daikin
```

Chuẩn hóa model:

* Chuyển về chữ hoa.
* Loại khoảng trắng không cần thiết.
* Chuẩn hóa `/`, `-`, `_`.
* Không phá vỡ cấu trúc model.
* Bảo toàn các ký tự có ý nghĩa.

Ví dụ:

```text
FTKF35XVMV / RKF35XVMV
FTKF35XVMV-RKF35XVMV
ftkf35xvmv rkf35xvmv
```

Có thể chuẩn hóa về cùng một representation, nhưng phải giữ giá trị gốc để kiểm tra.

---

# 13. Giai đoạn 10 — Trích xuất SKU/model

Model là khóa quan trọng nhất để ghép dữ liệu.

Xây dựng nhiều lớp trích xuất:

1. Trường SKU/model có cấu trúc trên trang.
2. JSON-LD `sku`, `mpn` hoặc `productID`.
3. Thuộc tính kỹ thuật.
4. Tên sản phẩm.
5. URL.
6. Regex theo từng thương hiệu hoặc danh mục.

Không sử dụng một regex duy nhất cho tất cả sản phẩm.

Tạo model extractor theo nhóm:

* Điều hòa.
* Tivi.
* Tủ lạnh.
* Máy giặt.
* Máy sấy.
* Máy lọc không khí.
* Gia dụng.
* Thiết bị bếp.
* Các nhóm khác được phát hiện trong dữ liệu.

Mỗi model được trích xuất phải có:

```text
raw_model
normalized_model
model_source
model_confidence
```

Nếu tìm được nhiều model trên cùng trang, phải xác định:

* Model sản phẩm chính.
* Model dàn nóng/dàn lạnh nếu là điều hòa.
* Model phụ kiện.
* Model biến thể.

Không tự động chọn khi chưa đủ căn cứ.

---

# 14. Giai đoạn 11 — Ghép sản phẩm

Thực hiện matching theo nhiều cấp.

## Cấp 1 — Exact match

Tự động ghép khi:

```text
normalized_model giống nhau
AND brand giống nhau
```

Đây là mức tin cậy cao nhất.

## Cấp 2 — Composite model match

Dùng cho sản phẩm có nhiều mã, ví dụ bộ dàn nóng và dàn lạnh.

Ghép khi tập hợp model tương đương và thương hiệu giống nhau.

## Cấp 3 — Model gần đúng

Chỉ dùng khi:

* Model khác nhau do dấu cách hoặc ký tự phân cách.
* Có hậu tố thị trường.
* Có quy tắc đã được xác minh.

Không dùng fuzzy model tùy tiện.

## Cấp 4 — Name-based candidate

Khi thiếu model, có thể tạo ứng viên dựa trên:

* Thương hiệu.
* Danh mục.
* Tên chuẩn hóa.
* Công suất.
* Kích thước.
* Dung lượng.
* Loại sản phẩm.
* Các thuộc tính kỹ thuật quan trọng.

Kết quả này chỉ nên là `REVIEW_REQUIRED`, không tự động chấp nhận trừ khi đáp ứng ngưỡng và quy tắc nghiêm ngặt.

Công thức điểm tham khảo:

```text
model_score: 0–100
brand_score: 0–100
name_score: 0–100
category_score: 0–100
attribute_score: 0–100
```

Tính `match_score` có trọng số.

Ví dụ:

```text
model_score: 50%
brand_score: 20%
name_score: 15%
category_score: 5%
attribute_score: 10%
```

Ngưỡng tham khảo:

```text
95–100: AUTO_APPROVED
80–94: REVIEW_REQUIRED
Dưới 80: không ghép tự động
```

Nếu model chính xác nhưng thương hiệu khác, phải từ chối hoặc yêu cầu kiểm tra.

---

# 15. Giai đoạn 12 — Kiểm tra chất lượng dữ liệu

Mỗi bản ghi phải được kiểm tra trước khi dùng trong báo cáo.

Các lỗi cần phát hiện:

```text
MISSING_PRODUCT_NAME
MISSING_MODEL
MISSING_PRICE
INVALID_PRICE
SALE_PRICE_GREATER_THAN_LIST_PRICE
PRICE_TOO_LOW
PRICE_TOO_HIGH
PRICE_CHANGED_ABNORMALLY
DUPLICATE_URL
DUPLICATE_MODEL
MULTIPLE_PRODUCTS_ON_ONE_URL
NON_PRODUCT_PAGE
BRAND_CONFLICT
CATEGORY_CONFLICT
LOW_MATCH_CONFIDENCE
STALE_DATA
CRAWL_ERROR
PARSER_ERROR
```

Không dùng một ngưỡng giá cố định cho mọi danh mục.

Phát hiện bất thường dựa trên:

* Khoảng giá của danh mục.
* Giá lịch sử của cùng sản phẩm.
* Giá của các đối thủ khác.
* Giá nội bộ.
* Phần trăm thay đổi so với lần crawl trước.

Ví dụ:

```text
Giá giảm trên 60% trong một lần crawl:
    đánh dấu cần kiểm tra

Giá chỉ bằng 1/10 giá trung vị của các nguồn:
    đánh dấu nghi ngờ lấy nhầm giá trả góp

Giá tăng hoặc giảm bất thường:
    giữ dữ liệu nhưng không tự động dùng để ra quyết định
```

Mỗi bản ghi có:

```text
data_confidence: 0–100
data_quality_status:
    VALID
    WARNING
    INVALID
    REVIEW_REQUIRED
```

---

# 16. Giai đoạn 13 — Đối soát dữ liệu

Xây dựng bước đối soát trước khi xuất báo cáo.

Đối với mỗi sản phẩm:

1. So sánh model giữa các website.
2. So sánh thương hiệu.
3. Kiểm tra giá có cùng đơn vị không.
4. Kiểm tra đúng biến thể không.
5. Kiểm tra trạng thái còn hàng.
6. Kiểm tra thời gian crawl.
7. Kiểm tra mức độ tin cậy.
8. Kiểm tra giá có bất thường so với nguồn khác không.

Không đưa dữ liệu `INVALID` vào cột giá chính thức.

Dữ liệu `WARNING` phải được đánh dấu màu hoặc ghi chú trong Excel.

Dữ liệu `REVIEW_REQUIRED` phải xuất riêng thành file:

```text
data/output/manual_review.xlsx
```

File review cần có:

* Sản phẩm nội bộ.
* Ứng viên đối thủ.
* Model hai bên.
* Giá hai bên.
* Điểm matching.
* Lý do cần review.
* URL để người dùng kiểm tra.
* Cột quyết định thủ công.

---

# 17. Giai đoạn 14 — Lịch sử giá

Không chỉ lưu giá mới nhất.

Mỗi lần giá thay đổi phải thêm bản ghi vào `price_history`.

Không thêm lịch sử mới nếu:

* Nội dung giá không thay đổi.
* Trạng thái tồn kho không thay đổi.

Hỗ trợ truy vấn:

* Giá hiện tại.
* Giá thấp nhất trong 7 ngày.
* Giá thấp nhất trong 30 ngày.
* Giá trung bình.
* Ngày thay đổi gần nhất.
* Số lần thay đổi giá.
* Website nào thường xuyên có giá thấp nhất.

---

# 18. Giai đoạn 15 — Xuất báo cáo Excel

Tạo các file:

## `competitor_prices.xlsx`

Dữ liệu giá đã chuẩn hóa của từng website.

Mỗi website có một sheet riêng.

## `price_comparison.xlsx`

Báo cáo chính dùng cho nghiệp vụ.

Các sheet tối thiểu:

```text
Tổng hợp
Thiếu giá đối thủ
Chưa ghép được
Cần kiểm tra
Lỗi crawl
Giá bất thường
Biến động giá
Thống kê
```

Sheet `Tổng hợp` cần:

* Freeze header.
* Auto filter.
* Định dạng tiền VND.
* Conditional formatting.
* Tô màu khi giá nội bộ cao hơn giá đối thủ.
* Tô màu khi giá thấp hơn giá Min.
* Tô màu dữ liệu cần kiểm tra.
* Hyperlink đến trang sản phẩm.
* Ghi thời gian cập nhật.

## `manual_review.xlsx`

Danh sách cần người dùng xác nhận.

## `crawl_summary.xlsx` hoặc báo cáo tương đương

Bao gồm:

```text
Tổng URL phát hiện
Tổng URL sản phẩm
Tổng URL crawl thành công
Tổng URL skip
Tổng URL lỗi
Số sản phẩm có model
Số sản phẩm thiếu model
Số sản phẩm có giá
Số sản phẩm giá liên hệ
Số sản phẩm ghép tự động
Số sản phẩm cần review
Tỷ lệ dữ liệu hợp lệ
```

---

# 19. Giai đoạn 16 — Command-line interface

Tạo CLI rõ ràng.

Ví dụ:

```bash
python -m src.main init-db
```

```bash
python -m src.main import-internal \
  --catalog data/input/catalog.xlsx \
  --price-file data/input/minimum_price.xlsx
```

```bash
python -m src.main discover --site all
```

```bash
python -m src.main crawl --site all
```

```bash
python -m src.main normalize
```

```bash
python -m src.main match
```

```bash
python -m src.main validate
```

```bash
python -m src.main export
```

```bash
python -m src.main run-all
```

Hỗ trợ thêm:

```bash
python -m src.main retry-errors
python -m src.main show-status
python -m src.main export-review
python -m src.main approve-match
```

`run-all` phải chạy theo thứ tự:

```text
import internal data
        ↓
discover
        ↓
crawl
        ↓
normalize
        ↓
match
        ↓
validate
        ↓
export
```

Nếu một bước lỗi, phải ghi log và không làm mất dữ liệu của các bước đã hoàn thành.

---

# 20. Giai đoạn 17 — Logging và theo dõi

Sử dụng logging chuẩn, không chỉ dùng `print`.

Log cần có:

```text
timestamp
level
module
site
url
task_id
status
duration
error_type
error_message
```

Xuất:

```text
logs/application.log
logs/crawler.log
logs/errors.log
```

Không ghi toàn bộ HTML hoặc thông tin nhạy cảm vào log.

Hiển thị thống kê khi chạy:

```text
Pending
Processing
Done
Retry
Skipped
Failed
Requests/minute
Average response time
Success rate
Parse success rate
```

---

# 21. Giai đoạn 18 — Retry và phục hồi

Hệ thống phải phục hồi được sau khi:

* Mất mạng.
* Website timeout.
* Chương trình bị tắt.
* Máy tính restart.
* File đầu vào lỗi.
* Parser gặp HTML mới.
* Một website tạm thời không truy cập được.

Task ở trạng thái `PROCESSING` quá thời gian cho phép phải được chuyển lại `RETRY`.

Cấu hình:

```text
max_retry
retry_delay
request_timeout
processing_timeout
batch_size
max_workers
requests_per_second
```

Không được xóa hàng đợi khi chạy lại.

---

# 22. Giai đoạn 19 — Testing

Viết unit test cho:

* Chuẩn hóa giá.
* Chuẩn hóa tên.
* Chuẩn hóa model.
* Trích xuất model.
* Phân loại URL.
* Parser từng website.
* Matching.
* Tính confidence.
* Phát hiện giá bất thường.
* Upsert dữ liệu.
* Retry state transition.

Lưu HTML fixture trong:

```text
tests/fixtures/<site>/
```

Mỗi website cần fixture cho:

* Trang sản phẩm có giá thường.
* Trang có giá sale.
* Trang giá liên hệ.
* Trang hết hàng.
* Trang không phải sản phẩm.
* Trang thiếu dữ liệu.
* Trang có nhiều giá gây nhầm lẫn.

Không để test phụ thuộc hoàn toàn vào website thật vì HTML có thể thay đổi.

---

# 23. Giai đoạn 20 — Kiểm thử nghiệm thu dữ liệu

Trước khi cho chạy toàn bộ, chọn một tập mẫu khoảng 20–50 sản phẩm cho mỗi website.

Với từng sản phẩm mẫu:

1. Mở URL thủ công.
2. Ghi lại tên, model, giá và tồn kho.
3. Chạy crawler.
4. So sánh kết quả crawler với kết quả thủ công.
5. Ghi nhận sai lệch.
6. Điều chỉnh parser.
7. Chạy lại test.

Tạo file:

```text
data/validation/golden_dataset.xlsx
```

Golden dataset gồm:

```text
site
url
expected_name
expected_brand
expected_model
expected_list_price
expected_sale_price
expected_effective_price
expected_stock_status
verified_at
verified_by
```

Parser chỉ được coi là đạt khi đáp ứng:

```text
Tỷ lệ nhận diện đúng trang sản phẩm >= 98%
Tỷ lệ lấy đúng tên >= 98%
Tỷ lệ lấy đúng giá >= 97%
Tỷ lệ lấy đúng model >= 95%
Tỷ lệ lấy nhầm giá nghiêm trọng < 1%
```

Nếu không đạt, không chạy toàn bộ dữ liệu.

---

# 24. Giai đoạn 21 — Triển khai

Cung cấp hai phương án chạy:

## Phương án 1 — Chạy local

* Python virtual environment.
* SQLite.
* CLI.
* Windows Task Scheduler hoặc cron.

## Phương án 2 — Docker

Tạo:

```text
Dockerfile
docker-compose.yml
```

Có volume cho:

```text
database
logs
input
output
raw snapshots
```

Không ghi dữ liệu quan trọng bên trong container mà không có volume.

---

# 25. Giai đoạn 22 — Lịch chạy

Thiết kế lịch tham khảo:

```text
Discovery sitemap: 1 lần/ngày
Crawl sản phẩm đang hoạt động: 1–2 lần/ngày
Retry lỗi tạm thời: mỗi 30–60 phút
Full recrawl: 1 lần/tuần
Export báo cáo: sau mỗi lần crawl hoàn tất
Cleanup snapshot cũ: 1 lần/tuần
```

Tần suất phải cấu hình được theo từng website.

Không crawl lại toàn bộ sitemap quá thường xuyên nếu không cần thiết.

Ưu tiên crawl:

1. Sản phẩm vừa thay đổi giá.
2. Sản phẩm nội bộ đang bán.
3. Sản phẩm đã ghép thành công.
4. Sản phẩm lâu chưa crawl.
5. URL mới.
6. URL từng lỗi.

---

# 26. Yêu cầu bảo mật

* Không lưu tài khoản hoặc mật khẩu trực tiếp trong code.
* Không commit `.env`.
* Không commit database, Excel nghiệp vụ hoặc HTML chứa dữ liệu nhạy cảm.
* Tạo `.env.example`.
* Thông tin nhạy cảm phải đọc từ biến môi trường.
* Không log token, cookie hoặc header nhạy cảm.
* Không cố gắng vượt CAPTCHA hoặc cơ chế kiểm soát truy cập.
* Không sử dụng proxy hoặc kỹ thuật né chặn nếu chưa được cho phép.

---

# 27. Yêu cầu về tài liệu

Tạo đầy đủ:

## `README.md`

Bao gồm:

* Mục tiêu project.
* Kiến trúc.
* Cài đặt.
* Cấu hình.
* Lệnh chạy.
* Input.
* Output.
* Cách thêm website mới.
* Cách xử lý lỗi.
* Cách review dữ liệu.
* Cách chạy test.
* Cách triển khai.

## `docs/architecture.md`

Mô tả module và trách nhiệm.

## `docs/data-flow.md`

Mô tả luồng dữ liệu từ discovery đến báo cáo.

## `docs/data-quality.md`

Mô tả các quy tắc kiểm tra chất lượng.

## `docs/add-new-site.md`

Hướng dẫn thêm parser cho website mới.

## `docs/operations.md`

Hướng dẫn vận hành, retry, backup và phục hồi.

---

# 28. Tiêu chí hoàn thành

Project chỉ được xem là hoàn thành khi đáp ứng tất cả điều kiện:

1. Cài đặt được trên máy mới theo README.

2. Import được dữ liệu nội bộ.

3. Phát hiện được URL sản phẩm từ cả 4 website.

4. Không crawl sitemap hai lần trong cùng một pipeline nếu không cần thiết.

5. Có hàng đợi crawl được lưu trong database.

6. Có retry và tiếp tục sau khi chương trình bị dừng.

7. Trích xuất được tên, model, giá và tồn kho.

8. Lưu được giá lịch sử.

9. Ghép được sản phẩm theo model.

10. Có confidence score.

11. Không tự động ghép dữ liệu có độ tin cậy thấp.

12. Có báo cáo manual review.

13. Có kiểm tra giá bất thường.

14. Có báo cáo Excel hoàn chỉnh.

15. Có test parser bằng HTML fixture.

16. Có golden dataset dùng để nghiệm thu.

17. Có thống kê tỷ lệ dữ liệu đúng.

18. Có log và báo cáo lỗi rõ ràng.

19. Có Docker hoặc hướng dẫn triển khai local đầy đủ.

20. Không chứa mật khẩu hoặc dữ liệu nhạy cảm trong repository.

---

# 29. Thứ tự thực hiện bắt buộc

Không triển khai toàn bộ trong một bước lớn.

Thực hiện theo từng milestone:

## Milestone 1 — Phân tích và khảo sát

Deliverables:

```text
requirements.md
architecture.md
data-flow.md
Tài liệu khảo sát 4 website
Danh sách câu hỏi nghiệp vụ còn thiếu
```

## Milestone 2 — Nền tảng dữ liệu

Deliverables:

```text
Cấu trúc project
Configuration
Database schema
Migration
CLI cơ bản
Logging
```

## Milestone 3 — URL discovery

Deliverables:

```text
robots parser
sitemap parser
URL normalizer
URL classifier
Database storage
Unit tests
```

## Milestone 4 — Crawler và parser

Deliverables:

```text
HTTP client
Queue
Retry
Parser cho từng website
HTML fixtures
Parser tests
```

## Milestone 5 — Chuẩn hóa và matching

Deliverables:

```text
Text normalization
Price normalization
Brand normalization
Model extraction
Matching
Confidence score
Review workflow
```

## Milestone 6 — Data quality

Deliverables:

```text
Validation rules
Anomaly detection
Quality status
Golden dataset
Accuracy report
```

## Milestone 7 — Reporting

Deliverables:

```text
competitor_prices.xlsx
price_comparison.xlsx
manual_review.xlsx
crawl_summary.xlsx
```

## Milestone 8 — Triển khai

Deliverables:

```text
README hoàn chỉnh
Docker
Scheduler
Backup
Operations guide
```

Sau mỗi milestone:

1. Chạy test.
2. Báo cáo những gì đã hoàn thành.
3. Liệt kê file đã tạo hoặc sửa.
4. Liệt kê rủi ro còn lại.
5. Cung cấp lệnh chạy kiểm tra.
6. Không chuyển sang milestone tiếp theo nếu milestone hiện tại chưa chạy được.

---

# 30. Cách phản hồi khi triển khai

Trước khi viết code, hãy trả về:

1. Tóm tắt cách hiểu yêu cầu.
2. Kiến trúc đề xuất.
3. Data flow.
4. Database schema.
5. Cấu trúc thư mục.
6. Các rủi ro về dữ liệu.
7. Kế hoạch milestone.

Sau đó bắt đầu triển khai Milestone 1.

Trong quá trình triển khai:

* Không tạo code giả chỉ để minh họa.
* Code phải chạy được.
* Không bỏ trống TODO ở luồng chính.
* Không che giấu lỗi bằng `try/except Exception: pass`.
* Không tự động bỏ qua dữ liệu không hợp lệ.
* Mọi giả định phải được ghi rõ.
* Ưu tiên tính đúng đắn, khả năng kiểm tra và khả năng bảo trì.
* Mỗi module phải có type hints.
* Những logic quan trọng phải có unit test.
* Chỉ dùng thư viện cần thiết và ghi đầy đủ trong `requirements.txt`.

Kết quả cuối cùng phải là một hệ thống có thể vận hành thực tế để thu được dữ liệu giá chính xác, có thể truy vết nguồn và có quy trình kiểm tra dữ liệu trước khi sử dụng.
