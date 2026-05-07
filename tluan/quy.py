from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    ElementClickInterceptedException,
    InvalidSessionIdException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime, timedelta
import pandas as pd
import time
import re
import os

# =========================
# THAY LINK BÀI POST Ở ĐÂY
# =========================
POST_URL = "https://www.facebook.com/starbucksvietnam/posts/pfbid05npm3jLFiqipESwVM4VCVrG5FpXRm19zXJbfGyFisQwDMCF85TisZVY5Aq9ncVXnl?__cft__[0]=AZYBRCKQJ0R8tmbKiKFPkywJpZexUWXrHoJ3waPi2BBDSegfnnEMBNxoUJ4-tXceMQWMzGTLstCoviP4wUdts4ve9xbH_fPSJrbVYxMfwsyEc12M8pRj_6zgxlmeY18we1GRm0Ve8QMSxcuiNaWoNjzEQrM3MrVoZjzGgzyQoG0C_A&__tn__=%2CO%2CP-R"
OUTPUT_FILE = "fb_results_full.xlsx"
AUTOSAVE_FILE = "fb_results_autosave.xlsx"

browser = None


# =========================
# 1. SETUP
# =========================
def create_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    drv.maximize_window()
    return drv


# =========================
# 2. HELPER
# =========================
def safe_click(el):
    global browser
    try:
        browser.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.15)
        browser.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        try:
            el.click()
            return True
        except Exception:
            return False


def normalize_text(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.strip().lower())


def scroll_down(step=2200, pause=0.8):
    global browser
    browser.execute_script(f"window.scrollBy(0, {step});")
    time.sleep(pause)


def page_height():
    global browser
    return browser.execute_script("return document.body.scrollHeight")


def count_loaded_comment_blocks():
    global browser
    xpaths = [
        "//div[@class='x1r8uery x1iyjqo2 x6ikm8r x10wlt62 xv54qhq']",
        "//div[@aria-label='Comment']",
        "//div[@role='article']",
    ]
    total = 0
    seen_ids = set()

    for xp in xpaths:
        try:
            elements = browser.find_elements(By.XPATH, xp)
            for el in elements:
                try:
                    if el.id not in seen_ids:
                        seen_ids.add(el.id)
                        total += 1
                except Exception:
                    continue
        except Exception:
            continue

    return total


def find_clickable_text_elements(text_list):
    global browser
    xpath_conditions = [f"contains(., \"{t}\")" for t in text_list]
    xpath = f"//*[{ ' or '.join(xpath_conditions) }]"
    return browser.find_elements(By.XPATH, xpath)


def click_fresh_buttons(text_list, clicked_cache, max_clicks=120):
    clicked = 0
    elements = find_clickable_text_elements(text_list)

    for el in elements:
        if clicked >= max_clicks:
            break

        try:
            if not el.is_displayed():
                continue

            text = normalize_text(el.text)
            if not text:
                continue

            loc = el.location_once_scrolled_into_view
            key = (text, round(loc.get("x", 0)), round(loc.get("y", 0)))

            if key in clicked_cache:
                continue

            ok = safe_click(el)
            if ok:
                clicked_cache.add(key)
                clicked += 1
                time.sleep(0.1)

        except (StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException):
            continue
        except Exception:
            continue

    return clicked


# =========================
# 3. CHUYỂN SANG ALL COMMENTS
# =========================
def switch_to_all_comments():
    try:
        opened = False
        for _ in range(5):
            buttons = find_clickable_text_elements(["Most relevant", "Phù hợp nhất"])
            for btn in buttons:
                try:
                    if btn.is_displayed() and safe_click(btn):
                        opened = True
                        time.sleep(1)
                        break
                except Exception:
                    continue
            if opened:
                break

        if not opened:
            print("Không mở được menu sort comment.")
            return

        switched = False
        for _ in range(5):
            buttons = find_clickable_text_elements(["All comments", "Tất cả bình luận", "Tất cả"])
            for btn in buttons:
                try:
                    if btn.is_displayed() and safe_click(btn):
                        switched = True
                        time.sleep(1)
                        break
                except Exception:
                    continue
            if switched:
                break

        if switched:
            print("Đã chuyển sang All comments")
        else:
            print("Không chuyển được sang All comments")

    except Exception as e:
        print("Lỗi switch_to_all_comments:", e)


# =========================
# 4. XỬ LÝ THỜI GIAN
# =========================
def is_like_line(text):
    if not text:
        return False
    s = text.strip().replace(",", "").replace(".", "").replace(" ", "")
    return s.isdigit()


def is_time_line(text):
    if not text:
        return False

    s = text.strip().lower()
    patterns = [
        r"^\d+\s*(m|min|minute|minutes)$",
        r"^\d+\s*(h|hr|hour|hours)$",
        r"^\d+\s*(d|day|days)$",
        r"^\d+\s*(w|week|weeks)$",
        r"^\d+\s*(phút|giờ|ngày|tuần)$",
        r"^just now$",
        r"^vừa xong$",
        r"^yesterday$",
        r"^hôm qua$",
    ]
    return any(re.match(p, s) for p in patterns)


def parse_facebook_time(time_str):
    now = datetime.now()

    if not time_str:
        return ""

    s = time_str.strip().lower()

    try:
        if s in ["just now", "vừa xong"]:
            return now.strftime("%Y-%m-%d %H:%M:%S")

        if s in ["yesterday", "hôm qua"]:
            return (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        m = re.match(
            r"^(\d+)\s*(m|min|minute|minutes|h|hr|hour|hours|d|day|days|w|week|weeks|phút|giờ|ngày|tuần)$",
            s
        )
        if not m:
            return time_str

        number = int(m.group(1))
        unit = m.group(2)

        if unit in ["m", "min", "minute", "minutes", "phút"]:
            dt = now - timedelta(minutes=number)
        elif unit in ["h", "hr", "hour", "hours", "giờ"]:
            dt = now - timedelta(hours=number)
        elif unit in ["d", "day", "days", "ngày"]:
            dt = now - timedelta(days=number)
        else:
            dt = now - timedelta(weeks=number)

        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return time_str


# =========================
# 5. TÁCH COMMENT
# =========================
def extract_comments():
    global browser

    xpaths = [
        "//div[@class='x1r8uery x1iyjqo2 x6ikm8r x10wlt62 xv54qhq']",
        "//div[@aria-label='Comment']",
        "//div[@role='article']",
    ]

    all_blocks = []
    seen_ids = set()

    for xp in xpaths:
        try:
            elements = browser.find_elements(By.XPATH, xp)
            for el in elements:
                try:
                    web_id = el.id
                    if web_id not in seen_ids:
                        seen_ids.add(web_id)
                        all_blocks.append(el)
                except Exception:
                    continue
        except Exception:
            continue

    data = []
    dedupe = set()

    for block in all_blocks:
        try:
            text = block.text.strip()
            if not text:
                continue

            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if len(lines) < 2:
                continue

            author = lines[0]
            body_lines = lines[1:]

            likes = ""
            created_time = ""

            if body_lines and is_like_line(body_lines[-1]):
                likes = body_lines[-1]
                body_lines = body_lines[:-1]

            if body_lines and is_time_line(body_lines[-1]):
                created_time = parse_facebook_time(body_lines[-1])
                body_lines = body_lines[:-1]

            comment_text = "\n".join(body_lines).strip()

            if not comment_text:
                continue

            if len(author) > 120:
                continue

            key = (author, comment_text, created_time, likes)
            if key in dedupe:
                continue
            dedupe.add(key)

            data.append([author, comment_text, created_time, likes])

        except StaleElementReferenceException:
            continue
        except Exception:
            continue

    return data


# =========================
# 6. XUẤT EXCEL
# =========================
def export_to_excel(data, output_file):
    df = pd.DataFrame(data, columns=["Author", "Comment", "Created_time", "Likes"])
    df.to_excel(output_file, index=False)
    print(f"Đã xuất file Excel: {output_file}")
    print(f"Tổng số dòng đã lưu: {len(df)}")


# =========================
# 7. LOAD COMMENT / REPLY
# =========================
def expand_all_fast(max_rounds=45, stable_limit=6):
    more_comments_texts = [
        "View more comments",
        "See more comments",
        "Load more comments",
        "View previous comments",
        "Xem thêm bình luận",
        "Xem bình luận trước đó"
    ]

    more_replies_texts = [
        "View more replies",
        "See more replies",
        "View more reply",
        "Xem thêm phản hồi",
        "Xem thêm câu trả lời",
        "phản hồi",
        "repl"
    ]

    see_more_texts = [
        "See more",
        "Xem thêm"
    ]

    clicked_cache_comments = set()
    clicked_cache_replies = set()
    clicked_cache_see_more = set()

    no_growth_rounds = 0
    last_height = 0
    last_block_count = 0
    best_data = []

    for round_no in range(1, max_rounds + 1):
        try:
            current_block_count_before = count_loaded_comment_blocks()

            c1 = click_fresh_buttons(more_comments_texts, clicked_cache_comments, max_clicks=40)
            c2 = click_fresh_buttons(more_replies_texts, clicked_cache_replies, max_clicks=80)
            c3 = click_fresh_buttons(see_more_texts, clicked_cache_see_more, max_clicks=80)

            old_height = page_height()
            scroll_down(step=2200, pause=0.8)
            new_height = page_height()

            current_block_count_after = count_loaded_comment_blocks()

            print(
                f"===== ROUND {round_no} ===== | "
                f"comments={c1} | replies={c2} | see_more={c3} | "
                f"blocks_before={current_block_count_before} | "
                f"blocks_after={current_block_count_after}"
            )

            # autosave mỗi round
            current_data = extract_comments()
            if len(current_data) >= len(best_data):
                best_data = current_data
                export_to_excel(best_data, AUTOSAVE_FILE)

            grew = (
                c1 > 0
                or c2 > 0
                or c3 > 0
                or new_height > last_height
                or current_block_count_after > last_block_count
            )

            if grew:
                no_growth_rounds = 0
            else:
                no_growth_rounds += 1

            last_height = new_height
            last_block_count = current_block_count_after

            if no_growth_rounds >= stable_limit:
                print("Không còn tăng dữ liệu mới. Dừng load sớm.")
                break

        except (InvalidSessionIdException, WebDriverException) as e:
            print("Session Chrome bị mất giữa chừng:", e)
            break

    return best_data


# =========================
# 8. MAIN
# =========================
def main():
    global browser
    final_data = []

    try:
        browser = create_browser()
        browser.get(POST_URL)
        time.sleep(6)

        print("Chờ 10 giây để bạn đăng nhập/xác minh nếu cần...")
        time.sleep(10)

        for _ in range(3):
            scroll_down(step=1400, pause=0.8)

        switch_to_all_comments()
        final_data = expand_all_fast(max_rounds=45, stable_limit=6)

        # nếu vì lý do nào đó expand chưa trả data thì lấy lại lần cuối
        if not final_data:
            try:
                final_data = extract_comments()
            except Exception:
                final_data = []

    except KeyboardInterrupt:
        print("Bạn đã dừng chương trình bằng tay.")
        try:
            final_data = extract_comments()
        except Exception:
            pass

    except Exception as e:
        print("Lỗi trong quá trình chạy:", e)
        try:
            final_data = extract_comments()
        except Exception:
            pass

    finally:
        # ưu tiên lưu file cuối
        if final_data:
            export_to_excel(final_data, OUTPUT_FILE)
        elif os.path.exists(AUTOSAVE_FILE):
            print(f"Không lấy thêm được dữ liệu cuối, nhưng đã có file tạm: {AUTOSAVE_FILE}")
        else:
            print("Chưa có dữ liệu để xuất Excel.")

        try:
            if browser is not None:
                browser.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()