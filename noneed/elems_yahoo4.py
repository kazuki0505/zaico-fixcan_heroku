# コメント消してきれいにした。


import requests, bs4
import csv
import time
import re
import shutil
import xlwings as xw
import pandas as pd
import threading
import numpy as np
import pandas as pd


def main(f, el):
    # このファイルから始める時、アクティブID出力を忘れることがあるため
    # atk = r"C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/AtackList_Buyer43.xlsx"
    # app = xw.App(visible=False)  # False)
    # wb2 = app.books.open(atk)
    # macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt_elem')  # 状態列が空白の行から全てのIDをテキストへ
    # macro()
    # shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo_elem.txt',
    #             'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo_elem.txt')
    # time.sleep(10)  # 時間置かないと、elems_yahooでTxtファイルがないと言われることがある
    # # wb2.save()
    # app.kill()

    # el_csv = r'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_yahoo_elements.csv'
    #    #         r'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/img_spread.csv']
    # # for csv in csv_list:
    #     # csv1 = "db_yahoo_elements.csv" とする、下のshutil では絶対パスにcsv1 と加えることになるよね
    # with open(el_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f:

    writer = csv.writer(f)
    with open('db_check_yahoo_elem.txt') as f: #
        page_id_list = [str(row) for row in f]
    # img_list = []
    # id_list = []
    # arr = np.empty([0, 2])
    arr = np.empty([0, 2])
    # print(arr)
    for page_id in page_id_list:#[347:352]:#[:10]:
        print(page_id)
        url = f'https://page.auctions.yahoo.co.jp/jp/auction/{page_id}'
        try:
            res = requests.get(url.strip())
            res.raise_for_status()
            soup = bs4.BeautifulSoup(res.text, "html.parser")

            # 説明文/description
            #scrape(soup, writer, url, arr) #, img_list, id_list, arr)
            elems = soup.select(
                '#adoc > div.ProductExplanation__body.highlightWordSearch > div.ProductExplanation__commentArea > div')
            elems_d = remove_space_htmlTag(str(elems))
            print(elems_d)

            #状態/condition
            elems1 = soup.select(
                '#adoc > div.ProductExplanation__body.highlightWordSearch > div.ProductExplanation__tableArea > table > tbody > tr:nth-child(2) > td > ul > li')  # [0].extract()
            # print(elems1)
            elems_c = remove_space_htmlTag(str(elems1))
            print(elems_c)

            # 画像
            elem_img = soup.select("div[class='ProductImage__inner'] img")
            for tmp in elem_img:
                # global src_fact
                src_fact = tmp.attrs["src"]  # attrsを用いてhtmlのsrc=の中身をsrc_factに格納していきました。
                # if src_fact == []:
                #     print("画像が見つかりません。。。")
                # else:
                page_id_for_scrape = url.split('/')[-1]
                # list = [elems_d, elems_c, page_id_for_scrape]
                # writer.writerow(list)
                # time.sleep(0.5)
                img_np = np.array([[page_id_for_scrape], [src_fact]]).T  # transpose()  # elem_img]) # src_list]
                arr = np.r_[arr, img_np]

        except requests.exceptions.HTTPError as err:
            print(err)
            elems_d = ''# httpエラーのIDが飛ばされていたので
            elems_c = ''
            src_fact = ''
            page_id_for_scrape = url.split('/')[-1]
            # list = [elems_d, elems_c, page_id_for_scrape]
            # writer.writerow(list)
            # time.sleep(0.5)
            img_np = np.array([[page_id_for_scrape], [src_fact]]).T  # transpose()  # elem_img]) # src_list]
            arr = np.r_[arr, img_np]
            time.sleep(1)

        # page_id_for_scrape = url.split('/')[-1]
        list = [elems_d, elems_c, page_id_for_scrape]
        writer.writerow(list)
    # print(arr)
    img_spread(arr, el)


def remove_space_htmlTag(s):
    p = re.compile(r"<[^>]*?>") # htmlTagを削除
    remove = p.sub("", s)
    space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    return space.replace('[', '').replace(']', '') # [] を置換


def img_spread(arr, el):  # (img_list):
    df = pd.DataFrame(arr)
    df.columns = ['ID', '画像'] # 列名指定
    def f(a): # 単なるGroupBy, apply ではなく、関数 f を組むことで、画像URLを一列に集約するだけでなく、各列に分割までできた  # https://ja.stackoverflow.com/questions/24845/python%E3%81%AEpandas%E3%81%A7-%E7%B8%A6%E6%8C%81%E3%81%A1%E3%81%AE%E3%83%87%E3%83%BC%E3%82%BF%E3%82%92%E6%A8%AA%E6%8C%81%E3%81%A1%E3%81%AB%E3%81%99%E3%82%8B%E3%82%88%E3%81%84%E6%96%B9%E6%B3%95%E3%82%92%E6%95%99%E3%81%88%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84
        a.index = [0 for i in range(len(a))]
        del a['ID'] # 列名指定
        out = a[0:1]
        for i in range(1, len(a)):
            out = out.join(a[i:i + 1], rsuffix='{0}'.format(i))
        return out
    grped = df.groupby(df['ID'], sort=False).apply(f) # おまけに、列名まで生成されてる!　ここで順を崩さないように
    # return grped
    print(grped) # https://stackoverflow.com/questions/48044542/groupby-preserve-order-among-groups-in-which-way
    # grped2 = grped.iloc[::-1] # 上下反転　
    # grped2.to_csv('merge_imgs2.csv') # これは列がバラバラのまま

    # elements.csvのID順は、ATKのそれと同じか？売り切れ品の要素も空白として記録してる？
    # cols = ['ゆ', 'の', 'ID']
    # id_df = pd.read_csv(el, # ここatk のID 列でもいい
    #                     header=None, names=cols).iloc[:, 2] # .reset_index() # , index='ID') # , columns=['ID'])
    # # id_df = pd.read_excel(atk, 'Sheet1', usecols=['ID_y'], skiprows=2, encoding='cp932')
    # print(id_df)
    # concat = pd.concat([id_df, grped], axis=1) # p.263 これ数値のみ？ 共通の越インデックスはあるが
    # id_df をつくりmergeさせるのは、grped のIDの並びがバラバラになっているのを、元のATK記載のIDリストの並びに戻すため
    # バラバラではなく、逆順になっていた
    # 2行分のズレが生じてるのは、このmergeによるものなのでは？では、マージではなく, 逆に並べる動作をすれば
    # merge = pd.merge(id_df, grped, on='ID', how='outer') # 外部結合なら、どちらかに無い値はNaNと表示される
    # print(merge)
    grped.to_csv('merge_imgs3.csv')

    update_atk(el, grped)


def update_atk(el, grouped):
    app = xw.App(visible=False)  # 新規アプリ実行環境を作成する
    wb1 = app.books.open(el)
    app.books.open("C:/Users/Kazuki Yuno/AppData/Roaming/Microsoft/Excel/XLSTART/PERSONAL.XLSB")
    # macro = app.macro('PERSONAL.XLSB!elementsfromBS4')
    # macro()
    wb1.save()

    atk = r"C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/AtackList_Buyer43.xlsx"
    wb2 = app.books.open(atk)
    # af_elems.autofill(atacklist)
    # def el2at(el, atk, grped):
        # 説明文、状態、画像、価格2種類、その他利益計算の列全て
    sht1 = wb1.sheets[0]  # (1)にしていたが
    sht2 = wb2.sheets[0]

    lastRow1 = sht1.range('C1').end(-4121).row # Aにしていたが、今回のHTTPエラー時は空白ができることで、最下行はID列＝Cで。
    # nextRow1 = lastRow1 + 1
    lastRow2 = sht2.range('AZ4').end(-4121).row  # ATK 状態列＝AZの最下行
    nextRow2 = lastRow2 + 1
    # 生成したCSVからタイトル、URL, 画像URLをATKへ、最下行の下の行から追加
    # col_list = ['G','I']
    # for col in col_list:
    # 説明と状態
    desc = sht1.range('A1:A{}'.format(str(lastRow1))).options(ndim=2).value
    sht2.range('J{}'.format(str(nextRow2))).value = desc
    condi = sht1.range('B1:B{}'.format(str(lastRow1))).options(ndim=2).value
    sht2.range('AZ{}'.format(str(nextRow2))).value = condi
    # col_list = ['R','S','T','U','V']
    # i = 2 # merge の３列目から
    # for col, i in zip(col_list, range(2, 7)): # これで、２のときはR, ３のときはS、となる # https://uxmilk.jp/13726
    # for col, i in zip(range(13, 18), range(2, 7)):
    # while i < 7:

    # 画像、通常版
    sht2.range('P{}'.format(nextRow2)).options(
        pd.DataFrame, expand='table', index=False, header=None).value = grouped.iloc[:, 1:8] # mergeの１－７列目に画像URLがある。8, 9 まであるアイテムも。
    # これまでのアイテムの画像データを一新＞ 4行目から
    # my_values = merge.iloc[:, 1:8]
    # sht2.range('P4').options(
    #     pd.DataFrame, expand='table', index=False, header=None).value = my_values  # index=False

    # el2at(wb1, wb2, grouped)

    # 次のPricesチェック(zaico.py )のため, output ID
    # zaico.py もつなげる ここはzaicoと繋がる必要はない。価格取得だけで良い
    # import された時はfixCancel動かさない、などの設定
    macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt')
    macro()
    shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo3.txt',
                'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo3.txt')
    wb2.save() # 読み取り専用の状態だと、保存できずエラーで終わる
    wb1.close()
    wb2.close()
    app.kill()

    # 仕入先をスクレイプするごとに価格チェックすることになるから、ここは繋げない。最後に一括で価格やればいい
    from sample_codes import zaico_yahoo as zyahoo  # if name == main は、
    pr_csv = 'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo4.csv'
    with open(pr_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f2:
        zyahoo.main(f2, pr_csv)


if __name__ == '__main__':
    el_csv = r'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_yahoo_elements.csv'
       #         r'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/img_spread.csv']
    # for csv in csv_list:
        # csv1 = "db_yahoo_elements.csv" とする、下のshutil では絶対パスにcsv1 と加えることになるよね
    with open(el_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f:
        main(f, el_csv)

