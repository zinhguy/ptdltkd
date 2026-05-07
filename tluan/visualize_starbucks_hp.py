# ============================================================
# VẼ 4 BIỂU ĐỒ PHÂN TÍCH PHẢN HỒI KHÁCH HÀNG FACEBOOK
# Đề tài: Phân tích phản hồi khách hàng trên Facebook
# về chiến dịch Starbucks x Harry Potter của Starbucks Vietnam
# ============================================================

# Cài thư viện nếu chưa có:
# python3 -m pip install pandas matplotlib wordcloud openpyxl

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os
import re


# =========================
# 1. CẤU HÌNH
# =========================
INPUT_FILE = "data/fb_comments_cleaned.xlsx"
OUTPUT_DIR = "charts"

TEXT_COLUMN = "clean_text"
TIME_COLUMN = "Created_time"
AUTHOR_COLUMN = "Author"

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")


# =========================
# 2. ĐỌC DỮ LIỆU
# =========================
df = pd.read_excel(INPUT_FILE)

required_cols = [TEXT_COLUMN]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Không tìm thấy cột '{col}' trong file dữ liệu.")

df[TEXT_COLUMN] = df[TEXT_COLUMN].fillna("").astype(str)

if AUTHOR_COLUMN in df.columns:
    df[AUTHOR_COLUMN] = df[AUTHOR_COLUMN].fillna("").astype(str)

if TIME_COLUMN in df.columns:
    df[TIME_COLUMN] = pd.to_datetime(df[TIME_COLUMN], errors="coerce")

print("Đã đọc dữ liệu.")
print(f"Tổng số dòng dữ liệu: {len(df)}")
print("Các cột hiện có:", list(df.columns))


# =========================
# 3. STOPWORDS CƠ BẢN
# =========================
base_stopwords = {
    "là", "thì", "mà", "và", "có", "đã", "đang", "rồi", "một",
    "những", "các", "cho", "với", "khi", "đó", "này", "kia",
    "được", "không", "tôi", "bạn", "mọi", "người", "ơi", "à",
    "ạ", "ha", "nha", "nhé", "đi", "chứ", "vậy", "cũng", "rất",
    "luôn", "thôi", "nữa", "đây", "của", "mình", "cái", "như",
    "tui", "thấy", "ở", "trong", "để", "vẫn", "ra", "còn",
    "nên", "bị", "vào", "lại", "lên", "xuống", "qua", "về",
    "từ", "theo", "nếu", "vì", "do", "nào", "ấy", "gì", "ai",
    "đâu", "sao", "bao", "nhiêu", "nơi", "lúc", "ngày", "giờ",
    "phút", "hôm", "nay", "mai", "rằng", "thế", "thôi", "nhỉ",
    "ừ", "ờ", "ơ", "ui", "ôi", "trời", "haha", "hihi", "kkk",
    "kk", "hic", "huhu"
}

# Từ quá chung của Facebook / bối cảnh đăng bài
platform_stopwords = {
    "facebook", "fb", "comment", "comments", "cmt", "bình_luận",
    "like", "share", "chia_sẻ", "tag", "rep", "reply", "trả_lời",
    "page", "post", "bài", "bài_viết", "link", "xem", "xem_thêm",
    "thêm", "phản_hồi"
}

# Từ quá chung của chiến dịch, nếu để lại sẽ làm lệch WordCloud
campaign_general_stopwords = {
    "starbucks", "starbuck", "starbucks_vietnam",
    "harry", "potter", "harry_potter", "hp",
    "vietnam", "việt", "nam"
}

# Từ quá chung về mua bán / cảm xúc, không phản ánh rõ vấn đề
generic_issue_stopwords = {
    "mua", "đặt", "order", "thích", "mê", "muốn", "yêu", "iu",
    "xinh", "đẹp", "cute", "xịn", "ưng", "quá", "ok", "oke",
    "oki", "sản_phẩm", "sp", "hàng", "món", "loại", "mẫu"
}


# =========================
# 4. LỌC TÊN NGƯỜI COMMENT
# =========================
author_name_stopwords = set()

if AUTHOR_COLUMN in df.columns:
    authors = df[AUTHOR_COLUMN].dropna().astype(str)

    for author in authors:
        author = author.lower().strip()

        for ch in [".", ",", "_", "-", "(", ")", "[", "]", "{", "}", "/", "\\", "|", ":", ";", "!", "?", "@", "#", "'"]:
            author = author.replace(ch, " ")

        for token in author.split():
            token = token.strip()
            if len(token) >= 2 and not token.isdigit():
                author_name_stopwords.add(token)

all_stopwords = (
    base_stopwords
    | platform_stopwords
    | campaign_general_stopwords
    | generic_issue_stopwords
    | author_name_stopwords
)


# =========================
# 5. NHÓM NỘI DUNG PHÂN TÍCH THEO ĐỀ TÀI
# =========================
topic_keywords = {
    "Sản phẩm / quà tặng / merchandise": [
        "ly", "cốc", "bình", "tumbler", "cup", "mug",
        "móc", "móc_khóa", "keychain", "sticker", "card",
        "quà", "gift", "set", "combo", "merch", "merchandise",
        "áo", "túi", "gấu", "figure", "phụ_kiện"
    ],

    "Giá cả / khuyến mãi": [
        "giá", "tiền", "đắt", "mắc", "rẻ", "chát",
        "voucher", "sale", "khuyến_mãi", "mã", "mã_giảm_giá",
        "freeship", "giảm", "ưu_đãi", "nghèo", "ví", "lương"
    ],

    "Nhu cầu sở hữu / săn hàng": [
        "săn", "chốt", "xin", "cần", "ước", "muốn",
        "phải_mua", "muốn_mua", "sở_hữu", "rinh", "hốt"
    ],

    "Tình trạng hàng / khan hiếm": [
        "hết", "cháy", "sold", "soldout", "sold_out",
        "limited", "giới_hạn", "cháy_hàng", "hết_hàng",
        "còn", "stock", "restock", "đợt", "suất", "full"
    ],

    "Vận chuyển / đặt hàng / mua hộ": [
        "ship", "giao", "giao_hàng", "vận_chuyển",
        "đơn", "đơn_hàng", "nhận", "inbox", "ib",
        "mua_hộ", "order_hộ", "đặt_hộ", "cod", "check_inbox"
    ],

    "Thiết kế / chủ đề Harry Potter": [
        "hogwarts", "gryffindor", "slytherin", "hufflepuff", "ravenclaw",
        "phù_thủy", "phép_thuật", "magic", "đũa", "thần_chú",
        "thiết_kế", "concept", "theme", "chủ_đề", "màu", "logo", "in"
    ]
}

topic_keyword_set = set()
for kws in topic_keywords.values():
    topic_keyword_set.update(kws)


# =========================
# 6. HÀM HỖ TRỢ
# =========================
def normalize_token(token):
    token = str(token).lower().strip()
    token = re.sub(r"^[^\wÀ-ỹ_]+|[^\wÀ-ỹ_]+$", "", token)
    return token


def classify_comment(text):
    text = str(text).lower()
    scores = {}

    for group, keywords in topic_keywords.items():
        score = 0
        for kw in keywords:
            if kw in text:
                score += 1
        scores[group] = score

    best_group = max(scores, key=scores.get)

    if scores[best_group] == 0:
        return "Khác"

    return best_group


def extract_relevant_words(text):
    """
    Chỉ giữ các từ liên quan trực tiếp đến đề tài:
    sản phẩm, giá, săn hàng, hết hàng, vận chuyển, thiết kế/chủ đề HP
    """
    words = []
    text = str(text).lower()

    for token in text.split():
        token = normalize_token(token)

        if not token:
            continue

        if token in all_stopwords:
            continue

        if len(token) <= 1:
            continue

        if token.isdigit():
            continue

        # Chỉ giữ các từ thuộc bộ từ khóa của đề tài
        if token in topic_keyword_set:
            words.append(token)

    return words


# =========================
# 7. GÁN NHÓM NỘI DUNG CHO BÌNH LUẬN
# =========================
df["content_group"] = df[TEXT_COLUMN].apply(classify_comment)


# =========================
# 8. WORDCLOUD
# Chỉ hiện các từ khóa thật sự liên quan đề tài
# =========================
relevant_words = []

for text in df[TEXT_COLUMN]:
    relevant_words.extend(extract_relevant_words(text))

text_for_wordcloud = " ".join(relevant_words)

if text_for_wordcloud.strip():
    wordcloud = WordCloud(
        width=1400,
        height=700,
        background_color="white",
        max_words=120,
        collocations=False
    ).generate(text_for_wordcloud)

    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(
        "WordCloud các nội dung phản hồi nổi bật về chiến dịch Starbucks x Harry Potter",
        fontsize=14
    )
    plt.savefig(
        f"{OUTPUT_DIR}/01_wordcloud_starbucks_harry_potter.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()
else:
    print("Không đủ dữ liệu phù hợp để vẽ WordCloud.")


# =========================
# 9. BIỂU ĐỒ CỘT: Số lượng phản hồi theo từng bài đăng Facebook
# =========================
if "source_post" in df.columns:
    post_counts = df["source_post"].value_counts().sort_index()
    
    plt.figure(figsize=(10, 6))
    plt.bar(post_counts.index, post_counts.values)
    plt.title("Số lượng phản hồi theo từng bài đăng Facebook", fontsize=14)
    plt.xlabel("Nguồn bài đăng")
    plt.ylabel("Số lượng bình luận")
    
    for i, value in enumerate(post_counts.values):
        plt.text(i, value, str(value), ha="center", va="bottom")
    
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/02_bar_post_counts.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()
else:
    print("Không tìm thấy cột 'source_post' để vẽ biểu đồ theo bài đăng.")


# =========================
# 10. BIỂU ĐỒ CỘT: Số lượng phản hồi theo nhóm nội dung
# =========================
bar_counts = df["content_group"].value_counts()

plt.figure(figsize=(10, 6))
plt.bar(bar_counts.index, bar_counts.values)
plt.title("Số lượng phản hồi theo nhóm nội dung", fontsize=14)
plt.xlabel("Nhóm nội dung phản hồi")
plt.ylabel("Số lượng bình luận")
plt.xticks(rotation=20, ha="right")

for i, value in enumerate(bar_counts.values):
    plt.text(i, value, str(value), ha="center", va="bottom")

plt.tight_layout()
plt.savefig(
    f"{OUTPUT_DIR}/03_bar_content_groups.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()


# =========================
# 11. BIỂU ĐỒ ĐƯỜNG: Xu hướng phản hồi khách hàng theo thời gian (Tổng)
# =========================
if TIME_COLUMN in df.columns and df[TIME_COLUMN].notna().sum() > 0:
    df_time = df.dropna(subset=[TIME_COLUMN]).copy()
    df_time["date"] = df_time[TIME_COLUMN].dt.date
    total_trend = df_time.groupby("date").size()
    
    plt.figure(figsize=(11, 6))
    plt.plot(total_trend.index.astype(str), total_trend.values, marker="o", linewidth=2)
    plt.title("Xu hướng phản hồi khách hàng theo thời gian", fontsize=14)
    plt.xlabel("Ngày bình luận")
    plt.ylabel("Số lượng bình luận")
    plt.xticks(rotation=45)
    
    for i, txt in enumerate(total_trend.values):
        plt.text(i, txt, str(txt), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/04_line_total_trend.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()
else:
    print(f"Không có dữ liệu thời gian hợp lệ để vẽ xu hướng tổng.")


# =========================
# 12. BIỂU ĐỒ ĐƯỜNG: Xu hướng phản hồi theo thời gian của các nhóm nội dung nổi bật
# =========================
if TIME_COLUMN in df.columns and df[TIME_COLUMN].notna().sum() > 0:
    # Lấy 3 nhóm nổi bật nhất, bỏ "Khác" nếu có thể
    top_groups = [g for g in bar_counts.index if g != "Khác"][:3]

    if len(top_groups) > 0:
        trend_df = (
            df_time[df_time["content_group"].isin(top_groups)]
            .groupby(["date", "content_group"])
            .size()
            .unstack(fill_value=0)
        )

        plt.figure(figsize=(11, 6))
        for col in trend_df.columns:
            plt.plot(trend_df.index.astype(str), trend_df[col], marker="o", label=col)

        plt.title("Xu hướng phản hồi theo thời gian của các nhóm nội dung nổi bật", fontsize=14)
        plt.xlabel("Ngày bình luận")
        plt.ylabel("Số lượng bình luận")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            f"{OUTPUT_DIR}/05_line_content_trends.png",
            dpi=300,
            bbox_inches="tight"
        )
        plt.show()
    else:
        print("Không đủ nhóm nội dung để vẽ biểu đồ đường xu hướng chi tiết.")


# =========================
# 13. BIỂU ĐỒ TRÒN: Tỷ trọng các nhóm nội dung phản hồi
# =========================
pie_counts = df["content_group"].value_counts()

plt.figure(figsize=(8, 8))
plt.pie(
    pie_counts.values,
    labels=pie_counts.index,
    autopct="%1.1f%%",
    startangle=90
)
plt.title("Tỷ trọng các nhóm nội dung phản hồi về chiến dịch", fontsize=14)
plt.tight_layout()
plt.savefig(
    f"{OUTPUT_DIR}/06_pie_content_groups.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()


# =========================
# 14. XUẤT FILE PHỤ
# =========================
df.to_excel("data/fb_comments_with_content_group.xlsx", index=False)

summary = pd.DataFrame({
    "content_group": pie_counts.index,
    "comment_count": pie_counts.values,
    "percentage": (pie_counts.values / pie_counts.values.sum() * 100).round(2)
})

summary.to_excel("data/content_group_summary.xlsx", index=False)

print("\nHoàn tất vẽ biểu đồ.")
print(f"Các biểu đồ đã lưu trong thư mục: {OUTPUT_DIR}")
print("File dữ liệu có thêm nhóm nội dung: data/fb_comments_with_content_group.xlsx")
print("File thống kê nhóm nội dung: data/content_group_summary.xlsx")

