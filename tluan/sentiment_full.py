# Cài đặt thư viện
# Mac:
# python3 -m pip install pandas numpy emoji matplotlib wordcloud
# python3 -m pip install underthesea transformers scikit-learn openpyxl torch

# Windows:
# py -m pip install pandas numpy emoji matplotlib wordcloud
# py -m pip install underthesea transformers scikit-learn openpyxl torch


# ============================================================
# CẤU HÌNH DỮ LIỆU ĐẦU VÀO / ĐẦU RA
# ============================================================

# Đọc một lần 3 file data lấy từ 3 link Facebook
INPUT_FILES = [
    "data/link1.xlsx",
    "data/link2.xlsx",
    "data/link3.xlsx"
]

# Với code quy.py, cột bình luận thường là "Comment"
# Nếu file của bạn là "comment" viết thường thì đổi lại thành "comment"
TEXT_COLUMN = "Comment"

# File trung gian và file kết quả
MERGED_FILE = "data/fb_comments_merged.xlsx"
CLEANED_FILE = "data/fb_comments_cleaned.xlsx"
OUTPUT_FILE = "Result.xlsx"


# ============================================================
# 1. KHAI BÁO THƯ VIỆN
# ============================================================

import pandas as pd
import numpy as np
import re
import os
import emoji
import unicodedata
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud

# Thư viện xử lý NLP
from underthesea import word_tokenize
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation


# ============================================================
# 2. ĐỌC VÀ GỘP 3 FILE DATA
# ============================================================

print("Đang tải 3 file dữ liệu...")

all_data = []

for i, file_path in enumerate(INPUT_FILES, start=1):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    if file_path.endswith(".csv"):
        temp_df = pd.read_csv(file_path)
    else:
        temp_df = pd.read_excel(file_path)

    if TEXT_COLUMN not in temp_df.columns:
        raise ValueError(
            f"Lỗi: Không tìm thấy cột '{TEXT_COLUMN}' trong file {file_path}.\n"
            f"Các cột hiện có là: {list(temp_df.columns)}"
        )

    # Gắn nguồn để biết bình luận đến từ link nào
    temp_df["source_post"] = f"link{i}"

    all_data.append(temp_df)

# Gộp 3 file thành 1 DataFrame
df = pd.concat(all_data, ignore_index=True)

# Chuyển cột bình luận về dạng chuỗi
df[TEXT_COLUMN] = df[TEXT_COLUMN].fillna("").astype(str)

# Xóa dòng bình luận trống
df = df[df[TEXT_COLUMN].str.strip() != ""]

# Xóa bình luận trùng nội dung
df = df.drop_duplicates(subset=[TEXT_COLUMN])

# Reset lại số thứ tự dòng
df.reset_index(drop=True, inplace=True)

# Lưu file đã gộp
df.to_excel(MERGED_FILE, index=False)

print(f"Đã gộp dữ liệu từ 3 file vào: {MERGED_FILE}")
print(f"Tổng số bình luận sau khi gộp và xóa trùng: {len(df)}")


# ============================================================
# 3. TỪ ĐIỂN TỔNG QUÁT: TEENCODE & STOPWORDS
# ============================================================

# Khu vực bổ sung thêm teencode nếu không có trong teencode_dict.csv
slang_dict = {
    "ko": "không", "k": "không", "hok": "không", "kh": "không", "kg": "không",
    "hong": "không", "hông": "không", "khum": "không", "hem": "không",
    "mng": "mọi người", "mn": "mọi người", "b": "bạn", "t": "tôi", "mk": "mình",
    "dc": "được", "đc": "được", "dk": "được", "đk": "được",
    "sp": "sản phẩm", "spham": "sản phẩm",
    "vl": "rất", "vcl": "rất", "vch": "rất",
    "đr": "đúng rồi", "dr": "đúng rồi",
    "ib": "nhắn tin", "inbox": "nhắn tin",
    "dt": "điện thoại", "nt": "nhắn tin",
    "thik": "thích", "thich": "thích",
    "r": "rồi", "rùi": "rồi", "ròi": "rồi",
    "chx": "chưa", "cx": "cũng",
    "vs": "với", "nma": "nhưng mà",
    "oke": "ổn", "oki": "ổn", "okie": "ổn",
    "rv": "đánh giá", "fb": "phản hồi",
    "ship": "giao hàng", "freeship": "miễn phí giao hàng",
    "mgg": "mã giảm giá", "km": "khuyến mãi",
    "sz": "kích cỡ", "cl": "chất lượng",
    "fake": "giả", "fail": "thất vọng",
    "bug": "lỗi"
}

# Tự động nối thêm teencode từ file teencode_dict.csv nếu có
if os.path.exists("teencode_dict.csv"):
    teencode_df = pd.read_csv("teencode_dict.csv")
    csv_teencode = dict(zip(teencode_df.iloc[:, 0], teencode_df.iloc[:, 1]))
    slang_dict.update(csv_teencode)
    print("Đã đọc thêm teencode từ file teencode_dict.csv")
else:
    print("Không tìm thấy teencode_dict.csv, chỉ dùng từ điển mặc định trong code.")

stopwords = set([
    "là", "thì", "mà", "và", "có", "đã", "đang", "rồi", "một", "những", "các", "cho",
    "với", "khi", "đó", "này", "kia", "được", "không", "tôi", "bạn", "mọi", "người",
    "ơi", "à", "ạ", "ha", "nha", "nhé", "đi", "chứ", "vậy", "cũng", "rất", "luôn",
    "thôi", "nữa", "đây", "của", "mình", "cái", "như", "tui", "thấy", "ở", "trong", "để"
])


# ============================================================
# 4. LÀM SẠCH DỮ LIỆU
# ============================================================

# Chuẩn hóa ký tự để xử lý lặp chữ
def base_char(c):
    return unicodedata.normalize("NFD", c)[0]


# Các từ cố định không muốn bị rút gọn ký tự
whitelist_words = {
    "cocoon", "shopee", "google", "tiktok", "zoom",
    "facebook", "app", "feedback", "starbucks"
}


# Xử lý lặp ký tự trong 1 từ
def normalize_word(word):
    if word.lower() in whitelist_words:
        return word

    if len(word) < 3:
        return word

    result = [word[0]]

    for i in range(1, len(word)):
        if base_char(word[i]) != base_char(word[i - 1]):
            result.append(word[i])

    return "".join(result)


# Hàm làm sạch tổng quát
def clean_text_generic(text):
    text = str(text).lower()

    # Xóa link
    text = re.sub(r"http\S+|www\S+|https\S+", " ", text, flags=re.MULTILINE)

    # Xóa tag/mention
    text = re.sub(r"@\w+", " ", text)

    # Xóa emoji
    text = emoji.replace_emoji(text, replace="")

    # Xóa số
    text = re.sub(r"\d+", " ", text)

    # Xóa dấu câu và ký tự đặc biệt
    text = re.sub(r"[^\w\s]", " ", text)

    # Rút gọn ký tự lặp và chuyển đổi teencode
    words = []

    for w in text.split():
        w_norm = normalize_word(w)
        w_final = slang_dict.get(w_norm, w_norm)
        words.append(w_final)

    text = " ".join(words)

    return re.sub(r"\s+", " ", text).strip()


print("Đang làm sạch dữ liệu...")

df["clean_text"] = df[TEXT_COLUMN].apply(clean_text_generic)

# Bỏ các dòng bị trống sau khi làm sạch
df = df[df["clean_text"].str.strip() != ""]
df.reset_index(drop=True, inplace=True)

# Lưu file sau chuẩn hóa
df.to_excel(CLEANED_FILE, index=False)

print(f"Đã lưu dữ liệu sau chuẩn hóa tại: {CLEANED_FILE}")
print(f"Số bình luận còn lại sau khi làm sạch: {len(df)}")


# ============================================================
# 5. TÁCH TỪ VÀ XÓA STOPWORDS
# ============================================================

print("Đang tách từ và xóa stopwords...")

df["tokenized"] = df["clean_text"].apply(lambda x: word_tokenize(x, format="text"))


def remove_stopwords(text):
    return " ".join([w for w in text.split() if w not in stopwords])


df["filtered"] = df["tokenized"].apply(remove_stopwords)


# ============================================================
# 6. KHAI THÁC TỪ KHÓA: TF-IDF & LDA TOPICS
# ============================================================

print("\nĐang chạy TF-IDF và gom cụm chủ đề LDA...")

if len(df[df["filtered"].str.strip() != ""]) > 5:
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.9
    )

    X = vectorizer.fit_transform(df["filtered"])

    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = X.sum(axis=0).A1

    keywords = sorted(
        zip(feature_names, tfidf_scores),
        key=lambda x: x[1],
        reverse=True
    )

    # Lưu từ khóa TF-IDF ra file riêng
    keyword_df = pd.DataFrame(keywords, columns=["keyword", "tfidf_score"])
    keyword_df.to_excel("TFIDF_keywords.xlsx", index=False)

    # Topic Modeling: tìm 3 chủ đề chính
    lda = LatentDirichletAllocation(
        n_components=3,
        random_state=42
    )

    lda.fit(X)

    df["topic_group"] = lda.transform(X).argmax(axis=1)

    # Lưu từ khóa đại diện cho từng topic
    topic_rows = []

    for topic_idx, topic in enumerate(lda.components_):
        top_indices = topic.argsort()[-10:][::-1]
        top_words = [feature_names[i] for i in top_indices]

        topic_rows.append({
            "topic_group": topic_idx,
            "top_keywords": ", ".join(top_words)
        })

    topic_df = pd.DataFrame(topic_rows)
    topic_df.to_excel("LDA_topics.xlsx", index=False)

    print("Đã lưu TFIDF_keywords.xlsx và LDA_topics.xlsx")

else:
    print("Dữ liệu quá ít để chạy TF-IDF và LDA.")
    keywords = []
    df["topic_group"] = ""


# ============================================================
# 7. PHÂN TÍCH CẢM XÚC BẰNG PHOBERT
# ============================================================

print("\nĐang chạy phân tích cảm xúc bằng PhoBERT...")

sentiment_model = pipeline(
    "sentiment-analysis",
    model="wonrax/phobert-base-vietnamese-sentiment"
)

phobert_preds = []
phobert_scores = []

for text in df["clean_text"]:
    # Cắt văn bản để tránh lỗi quá token
    text_cut = text[:500] if len(text) > 500 else text

    try:
        result = sentiment_model(
            text_cut,
            truncation=True,
            max_length=256
        )[0]

        if result["label"] == "POS":
            label = "positive"
        elif result["label"] == "NEG":
            label = "negative"
        else:
            label = "neutral"

        phobert_preds.append(label)
        phobert_scores.append(result["score"])

    except Exception:
        phobert_preds.append("neutral")
        phobert_scores.append(0.0)

df["sentiment"] = phobert_preds
df["confidence"] = phobert_scores


# ============================================================
# 8. TRỰC QUAN HÓA
# ============================================================

print("\nĐang vẽ biểu đồ...")

# 8.1 WordCloud
text_all = " ".join(df["filtered"].dropna())

if text_all.strip():
    cloud = WordCloud(
        background_color="white",
        width=1200,
        height=600,
        max_words=100
    ).generate(text_all)

    plt.figure(figsize=(10, 5))
    plt.imshow(cloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"WordCloud - {TEXT_COLUMN}")
    plt.savefig("wordcloud.png", dpi=300, bbox_inches="tight")
    plt.show()

# 8.2 Biểu đồ cảm xúc
sentiment_counts = df["sentiment"].value_counts()

plt.figure(figsize=(6, 4))
plt.bar(
    sentiment_counts.index,
    sentiment_counts.values,
    color=["#4CAF50", "#F44336", "#9E9E9E"]
)
plt.title("Phân bố cảm xúc")
plt.ylabel("Số lượng")
plt.savefig("sentiment_distribution.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================================================
# 9. XUẤT DỮ LIỆU KẾT QUẢ
# ============================================================

df.to_excel(OUTPUT_FILE, index=False)

print(f"\nHoàn tất!")
print(f"File gộp dữ liệu: {MERGED_FILE}")
print(f"File sau chuẩn hóa: {CLEANED_FILE}")
print(f"File kết quả cuối: {OUTPUT_FILE}")
print("Biểu đồ đã lưu: wordcloud.png, sentiment_distribution.png")
print("File từ khóa/chủ đề đã lưu: TFIDF_keywords.xlsx, LDA_topics.xlsx")