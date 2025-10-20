from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import re

# 設置 Chrome 選項以規避反爬蟲
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 隱藏自動化標誌
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.7258.155 Safari/537.36")

# 初始化 WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # 訪問目標網站
    url = 'https://www.wantgoo.com/stock/major-investors/net-buy-sell-rank'
    driver.get(url)

    # 等待表格行載入（最多等待 15 秒）
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )

    # 取得頁面內容
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 找到所有表格
    tables = soup.find_all('table')  # 獲取所有 <table> 標籤
    if len(tables) < 2:
        print("找不到第二個表格（淨賣超），請檢查網頁結構")
        print(soup.prettify())
        driver.quit()
        exit()

    # 選擇第二個表格（假設為淨賣超）
    table = tables[1]  # 索引 1 對應第二個表格（淨賣超）

    # 提取表頭
    headers = []
    thead = table.find('thead')
    if thead:
        for th in thead.find_all('th'):
            headers.append(th.text.strip())
        # 修改表頭：將第一欄替換為"股票代號"，移除原第一欄（排序）
        headers = ["股票代號"] + headers[1:] if headers else ["股票代號"]
    else:
        print("無法找到表頭，請檢查表格結構")
        headers = ["股票代號"]

    # 提取資料行
    rows = []
    tbody = table.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            cells = tr.find_all('td')
            if cells:
                # 提取股票名稱欄的超連結
                stock_cell = cells[1]  # 假設股票名稱在第二欄（索引 1）
                stock_link = stock_cell.find('a')
                stock_code = ""
                if stock_link and stock_link.get('href'):
                    # 檢查是否為 ETF 超連結（包含 /stock/etf/）
                    if '/stock/etf/' in stock_link.get('href'):
                        continue  # 跳過 ETF 行
                    # 提取非 ETF 股票代號（例如 /stock/6792 -> 6792）
                    match = re.search(r'/stock/(\d+)', stock_link.get('href'))
                    stock_code = match.group(1) if match else stock_cell.text.strip()
                else:
                    stock_code = stock_cell.text.strip()  # 回退到文字內容

                # 構建新行：股票代號 + 其他欄位（排除原第一欄）
                row = [stock_code] + [td.text.strip() for td in cells[1:]]
                rows.append(row)
    else:
        print("無法找到表格主體，請檢查表格結構")

    # 存成 CSV
    if headers and rows:
        with open('major_investors_net_sell_rank.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print("資料已存成 major_investors_net_sell_rank.csv")
    else:
        print("無資料可儲存，請檢查表格內容")

except Exception as e:
    print(f"發生錯誤: {e}")
    print(soup.prettify())

finally:
    # 關閉瀏覽器
    driver.quit()
