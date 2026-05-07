import time
import os
import quy

def main():
    links = [
        "https://www.facebook.com/share/p/1H1i7Zk5Pe/",
        "https://www.facebook.com/share/p/1LH34bGVfF/",
        "https://www.facebook.com/share/p/1HGonrUWcR/"
    ]
    out_files = [
        "data/link1.xlsx",
        "data/link2.xlsx",
        "data/link3.xlsx"
    ]
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    try:
        quy.browser = quy.create_browser()
        for i in range(3):
            link = links[i]
            out = out_files[i]
            quy.AUTOSAVE_FILE = out.replace(".xlsx", "_autosave.xlsx")
            quy.OUTPUT_FILE = out
            
            print(f"\n=========================================")
            print(f"Đang xử lý link {i+1}: {link}")
            print(f"Sẽ lưu vào: {out}")
            print(f"=========================================\n")
            
            quy.browser.get(link)
            time.sleep(6)
            
            if i == 0:
                print("Chờ 15 giây để bạn đăng nhập/xác minh nếu cần (chỉ cần làm 1 lần)...")
                time.sleep(15)
            else:
                print("Chờ 5 giây load trang...")
                time.sleep(5)
                
            for _ in range(3):
                quy.scroll_down(step=1400, pause=0.8)
                
            quy.switch_to_all_comments()
            final_data = quy.expand_all_fast(max_rounds=45, stable_limit=6)
            
            if not final_data:
                try:
                    final_data = quy.extract_comments()
                except Exception:
                    final_data = []
                    
            if final_data:
                quy.export_to_excel(final_data, out)
            else:
                print(f"Không lấy được dữ liệu cho link {i+1} (hoặc bài viết không có bình luận)")
                
    except Exception as e:
        print("Lỗi chung:", e)
    finally:
        try:
            if quy.browser is not None:
                quy.browser.quit()
        except Exception:
            pass
            
    print("\nĐã hoàn thành việc lấy dữ liệu cho cả 3 links.")

if __name__ == "__main__":
    main()
