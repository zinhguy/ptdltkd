[![SVG Banners](https://svg-banners.vercel.app/api?type=rainbow&text1=Zinh%20Guy%20🌈&width=800&height=400)](https://github.com/Akshay090/svg-banners)
# PTDLTKD
[![SVG Banners](https://svg-banners.vercel.app/api?type=textBox&text1=zinh%20guy%20🤖&width=800&height=400&bg=007bff)](https://github.com/Akshay090/svg-banners)

Repository này chứa các file code Python dùng để thu thập, xử lý và trực quan hóa dữ liệu bình luận Facebook.

Người dùng có thể tự thay đổi link Facebook, file dữ liệu đầu vào, stopwords, teencode, nhóm từ khóa và biểu đồ theo mục đích phân tích riêng.

## File code

| File | Chức năng |
|---|---|
| `scrape_links.py` | Chạy thu thập dữ liệu từ nhiều link Facebook và xuất dữ liệu ra file Excel. |
| `quy.py` | Chứa các hàm hỗ trợ scrape Facebook bằng Selenium, gồm mở trình duyệt, cuộn trang, mở thêm bình luận, tách nội dung bình luận và xuất Excel. |
| `sentiment_full.py` | Gộp dữ liệu, làm sạch văn bản, chuẩn hóa teencode, tách từ, trích xuất từ khóa, gom nhóm chủ đề và phân tích cảm xúc. |
| `visualize_starbucks_hp.py` | Vẽ các biểu đồ từ dữ liệu đã xử lý, gồm WordCloud, biểu đồ cột, biểu đồ đường và biểu đồ tròn. |
| `teencode_dict.csv` | Từ điển teencode dùng để chuẩn hóa các từ viết tắt trong dữ liệu văn bản. |

## Cài đặt thư viện

Trên macOS:

```bash
python3 -m pip install pandas numpy emoji matplotlib wordcloud underthesea transformers scikit-learn openpyxl torch selenium webdriver-manager
Cách chạy
1. Thu thập dữ liệu Facebook

Mở file scrape_links.py, chỉnh danh sách link Facebook trong biến links.

Ví dụ:

links = [
    "link_facebook_1",
    "link_facebook_2",
    "link_facebook_3"
]

Sau đó chạy:

python3 scrape_links.py

Dữ liệu thu thập sẽ được lưu trong thư mục data/.

2. Làm sạch và xử lý dữ liệu

Sau khi đã có file dữ liệu đầu vào, chạy:

python3 sentiment_full.py

File này dùng để gộp dữ liệu, làm sạch văn bản, chuẩn hóa teencode, tách từ, trích xuất từ khóa, gom nhóm chủ đề và phân tích cảm xúc.

3. Vẽ biểu đồ

Sau khi đã có dữ liệu làm sạch, chạy:

python3 visualize_starbucks_hp.py

Các biểu đồ sẽ được lưu trong thư mục charts/.

Cấu trúc thư mục gợi ý
ptdltkd/
│
├── scrape_links.py
├── quy.py
├── sentiment_full.py
├── visualize_starbucks_hp.py
├── teencode_dict.csv
│
├── data/
│   ├── link1.xlsx
│   ├── link2.xlsx
│   ├── link3.xlsx
│   ├── fb_comments_merged.xlsx
│   ├── fb_comments_cleaned.xlsx
│   └── fb_comments_with_content_group.xlsx
│
├── charts/
│   ├── wordcloud.png
│   ├── bar_chart.png
│   ├── line_chart.png
│   └── pie_chart.png
│
├── Result.xlsx
├── TFIDF_keywords.xlsx
└── LDA_topics.xlsx
Ghi chú
Người dùng cần tự thay đổi link Facebook trong scrape_links.py.
Người dùng cần tự điều chỉnh tên cột dữ liệu nếu file Excel có cấu trúc khác.
Có thể thay đổi stopwords, teencode và nhóm từ khóa theo mục đích phân tích riêng.
Nếu Facebook thay đổi giao diện, code thu thập dữ liệu có thể cần chỉnh lại XPath hoặc cách bấm nút.
Khi chạy lần đầu, mô hình PhoBERT có thể mất thời gian tải về máy.
