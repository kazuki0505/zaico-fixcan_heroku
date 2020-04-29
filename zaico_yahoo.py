import requests, bs4
import csv
import time
import shutil
import win32com.client
import sys, os
import xlwings as xw
from pymongo import MongoClient
from selenium.common.exceptions import WebDriverException
import re
import pandas as pd
import numpy as np


def main(f, pr):
    # writer = csv.writer(f)
    with open('db_check_yahoo3.txt') as f:
        page_id_list = [str(row) for row in f]
    # pr_list = []
    arr = np.empty([0, 2])
    for page_id in page_id_list:#[529:535]:
        print(page_id)
        # scrape(, writer, pr_list, arr)
        url = f'https://page.auctions.yahoo.co.jp/jp/auction/{page_id}'
        try:  # https://stackoverflow.com/questions/16511337/correct-way-to-try-except-using-python-requests-module
            res = requests.get(url.strip())
            res.raise_for_status()  # Responseオブジェクトが持つステータスコードが200番台以外だったら、例外を起こす、つまりエラーメッセージを吐き出してスクリプトを停止
            soup = bs4.BeautifulSoup(res.text, "html.parser")
            price = soup.select('dl > dd.Price__value')
            price2 = remove_space_htmlTag(str(price))
            # print(price2)
            # pr_list.append(elems_d)
            日件 = soup.select('.Count__number')
            日件2 = remove_space_htmlTag(str(日件))
            # print(日件2)
            if '終了' in 日件2: # 終了品は elems=価格 を空白に
                # print(日件2)
                price2 = ', ' # 空白のみだと、「, 」で分割する時エラー起きる
                print(price2)# + ' 終了')
            else: # 出品中なら
                pr_title = soup.select('dt[class="Price__title"]')
                pr_title2 = remove_space_htmlTag(str(pr_title))
                # print(pr_title2)
                if '現在価格' not in pr_title2: # 現在価格が無い＝即決価格のみなら
                    price2 = ', ' + price2 # 価格の手前
                    print(price2) # + ' 即決のみ')
                else: # 現在価格あるなら
                    print(price2) # + ' 現在') # ここは最初のprice2になる

        except requests.exceptions.HTTPError as err:
            print(err)
            price2 = ''# エラー時に、空白を入れることで、そのIDがスキップされるのを防ぐ
            time.sleep(1)

        page_id_for_scrape = url.split('/')[-1]
        # list = [page_id_for_scrape, price2]
        # writer.writerow(list)
        pr_np = np.array([[page_id_for_scrape], [price2]]).T  # transpose()  # elem_img]) # src_list]
        arr = np.r_[arr, pr_np]
        time.sleep(0.5)

    # seri = pd.Series(pr_list)
    # df = seri.str.split(', ', expand=True)  # https://note.nkmk.me/python-pandas-split-extract/
    # print(df)
    df = pd.DataFrame(arr)
    print(df)
    df2 = pd.concat([df, df.iloc[:, 1].str.split(
        ', ', expand=True)], axis=1).iloc[:, [0, 2, 3]]  # drop([1], axis=1)
    print(df2)  # 0, 2, 3 列目のみ表示
    df2.to_csv(pr, header=False, index=False) #header=True, encoding='cp932') #'utf-8-sig') # バックアップとして
    to_atk(df2)
    # update_atk(pr)
    #aa

def remove_space_htmlTag(s):
    p = re.compile(r"<[^>]*?>") # htmlTagを削除
    remove = p.sub("", s)
    space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    return space.replace('[', '').replace(']', '').replace('円（税 0 円） ', '')


def to_atk(df):
    app = xw.App(visible=False)  # False)
    atk = r"C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/AtackList_Buyer43.xlsx"
    wb2 = app.books.open(atk)
    sht2 = wb2.sheets[0]

    a_list = ['AV', 'AX']
    for a, i in zip(a_list, range(1, 3)):
        # print(a, i)
        sht2.range('{}4'.format(a)).options(
            pd.Series, expand='table', index=False, header=None).value = df.iloc[:, i]  # url_list 　ここをDF.iloc　option dataframeのやつ
    # sht2.range('AT{}'.format(nextRow)).options(
    #       pd.Series, expand='table', index=False, header=None).value = merge.iloc[:, 1] # url_list 　ここをDF.iloc　option dataframeのやつ
    wb2.save() # 上書き保存

    # フィルタかけた後の価格を、Fix対象にし、 >> Sheet1でquery かけてるから不要
    # app.books.open("C:/Users/Kazuki Yuno/AppData/Roaming/Microsoft/Excel/XLSTART/PERSONAL.XLSB")
    # macro = app.macro('PERSONAL.XLSB!AutoFilterAdvanced_RedNumber_tenki2')
    # macro()
    # while True:
    #     try: # ATK転記がうまく保存されていないとき、Selenによるブラウザを閉じると、WebDriverExceptionエラー。それExceptで
    from modules_scraping import fixcancel_auc4 as fixcan
    fixcan.main(atk)

    macro = app.macro('PERSONAL.XLSB!noNeedRow_delete_price')
    macro()
    macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt')
    macro()
    shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo3.txt',
                'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo3.txt')
    # macro = app.macro('PERSONAL.XLSB!AutoFilterAdvanced_RedNumber_tenki2')
    # macro()
        # except WebDriverException:
        #     print('WebDriverException, retrying...')
    # wb1.close()
    wb2.save()
    wb2.close()
    app.kill()
# pr_csv = 'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo4.csv'
# # update_at(pr_csv)



if __name__ == '__main__':
    # pr_csv = 'db_check_yahoo4.csv
    pr_csv = 'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo4.csv'
    with open(pr_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f:
        # sample_codes でWin32 使えないなら、利益計算ディレに移動
        main(f, pr_csv)

# これ後者はファイルのパスにすることで、上書きされるように。ディレのパスだと"Already exists"となりエラーに
