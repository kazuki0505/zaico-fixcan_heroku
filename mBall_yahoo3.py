# While i <151: つまり商品数１５１まで＝５０件/ページの３ページまでスクレイプする　
# mongoDB 無視
# これは、mBallの機能を担うコード。mBall_atk.pyも吸収してみた
# 　# mBall_yahooもmBall_atkも、画像１枚目を取得するかしないかの違いで、ほかは全く同じだからね


import pandas as pd
import numpy as np
from openpyxl import load_workbook
import time
import re

import requests, bs4
import lxml.html
from pymongo import MongoClient
import xlwings as xw
import math
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from xlwings.constants import AutoFillType
import shutil
from datetime import datetime
from uuid import uuid4
from googletrans import Translator
import json
# import pandas as pd
import pythoncom
from pythoncom import com_error
import win32com.client
import win32com
import sys


def main():
    # check_if_Excel_runs()
    # wb = r'C:\Users\Kazuki Yuno\Desktop\00.myself\04.Buyer\0.リサーチ\keyword\key_generator.xlsx'
    atk = r"C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/AtackList_Buyer43.xlsx"
    # 検索キーは、後の間を＋にする必要があるが、これエクセルの時点でやるか、ここでやるか> planner では空白で複合キーを生成するので、変更はここで
    df = pd.read_excel(
        atk, 'market', skiprows=2, usecols=['categ num', 'main key', 'キーフレーズ'])\
        .dropna(subset=['キーフレーズ']) # キーフレーズ列のNan を消して表示
    categ_num_list = df.iloc[:, 0]#'categ num']
    mainKey_list = df.iloc[:, 1]#'main key'
    keyPhrase_list = df.iloc[:, 2] #['X-MEN 同人誌', 'batman 同人誌'] #.get_group('X-MEN 同人誌', 'batman 同人誌') # 検索キーを減らしたいなら、ここで
                                    # iloc、第一引数が行
    app = xw.App(visible=True)  # False)
    wb2 = app.books.open(atk)
    sht2 = wb2.sheets[0]
    #                                        0~ other japanese antique  14~ painting  18= prints
    #                                             ドラゴンボール 37  ラストは４５
            # これは不便、カテゴリ指定で検索ワードをグループ化しながら、毎日自動リサしてほしい
    # keyPhraase 番号振っても、途中からのリサにならない
    # ここ、keyPhraseだけ番号振ったらだめ、mainKryやcategは最初から記録してしまう>> 一括で番を振る
    # list(zip()) とすることで、一括して順番を指定できる　https://stackoverrun.com/ja/q/7531087
    for mainKey, categ_num, keyPhrase in list(zip(mainKey_list, categ_num_list, keyPhrase_list))[44:]: #[36:]: # [:2]
        print(mainKey, categ_num, keyPhrase)
        # url = 'https://auctions.yahoo.co.jp/search/search' # while 内に入れることで解決。ここだと、2ページ目の頭の品のページに行ってしまう
        url_list = []
        title_list = [] # 空のDFを2列分用意し、append する方法もあるはずだが、次回
        itemid_list = []
        # price_list = []
        i = 1
        while i < 61: # 151 20ずつ or 50ずつ繰り上がる
            url = 'https://auctions.yahoo.co.jp/search/search' # 正規表現による置換はやめた
            # カテゴリ別に、Param設定を買えられる。If "ドラゴンボール フィギュア" : 即決品のみ
            params = {'q': keyPhrase, 'va': keyPhrase, 'exflg': '1', 'b': i, 'n': '20', # 50, 100
                      'min': '4000', 'max': '51999', 'price_type': 'bidorbuyprice'}
            # 注意: 即決のみにするには、min かmaxを指定する必要がある
            # # 'istatus': '',
            res = requests.get(url, params=params)
            print(res.url)
            res.raise_for_status()
            soup = bs4.BeautifulSoup(res.text, "html.parser")
            #   url_list = []
            # scrape_list_page(soup, url_list, title_list)
            elems = soup.select("a[class='Product__titleLink']")
            for a in elems:  # '#listBook a[itemprop="url"]'):
            # print(a)
                elem_url = a.get('href')
                print(elem_url)
                url_list.append(elem_url)
                # time.sleep(1)
                # yield url
                # title
                # itemid = extract_key(a)
                # itemid_list.append(itemid)
            # title_list = []
            elems = soup.select("a[class='Product__titleLink']")
            # elems = soup.select("#allContents > div.l-wrapper.cf > div.l-contents > div.l-contentsBody > div > div.Result__body > div.Products.Products--grid > div > ul > li:nth-child(1) > div.Product__detail > h3 > a")
            for elem in elems:
            # print(elem)
                title = elem.get('title')
                # print(elem)
                title_list.append(title)
                print(title)
            # 価格
            # elems = soup.select("span[class='Product__priceValue.u-textRed']")

            # print('OK')
            i += 20
            time.sleep(3)

        # 重複分はATKに追加しないようにする
        # title_list をATｋのタイトル列と比べ、もし重複していれば, title_listから重複分を削除. # ２つの円のベン図の半月 = df - merge(inner)
        # title_listとurl_list を接合 （titleだけ重複分を消しても、urlが残っているんじゃズレが生じるから
        df1 = pd.DataFrame({'タイトル': title_list, 'url': url_list}) #, 'id': itemid_list}) #, columns=['SKU']) # 2つのリストを一つのDFに
        # pd.DataFrame({'Mean': mean, 'Median': med, 'SD': sd})
        df2 = pd.read_excel(atk, 'Sheet1',
                            usecols=['タイトル'], skiprows=2, encoding='cp932') #.columns = ['title']
        # for index, row in df.iterrows():
        #     if row # row['開始価格'] == row['開始価格2']
        #         df.drop(index, inplace=True)
        on = ['タイトル']  # , 'url'] # https://stackoverflow.com/questions/48912242/how-to-drop-duplicates-from-one-data-frame-if-found-in-another-dataframe
        merge = df1.merge(df2[on], on=on, how='left', indicator=True)\
            .query('_merge == "left_only"').drop('_merge', 1) # 左＝df1にのみ存在する（(df2との重複を除く）タイトルにQueryしたあと、merge列を削除
        print(merge)
        # 既存のATKタイトルと、リサ結果のタイトルの重複は消えるが、結果タイトル(df1)内での重複は消えない
        # ループごとにatk を保存し、df2読み込む毎に各ループ更新直後のリストを読み込めばいい

        # タイトル整形、英訳前に>> HTML削除、不要文字置換
        # merge2 = remove_space_htmlTag(merge.iloc[:, 1])

        # タイトル翻訳
        translator = Translator()
        i = 0
        while len(merge) >= i: # 制限達したら、これパスしてXW転記もしないことにする。　一度エラー起きれば、リトライしてもずっとエラーだから、While要らない
            try:
                lastRow_title2 = sht2.range('F4').end(-4121).row  # ATK H=タイトル列
                nextRow2 = lastRow_title2 + 1
                merge_en = merge['タイトル'].iloc[i: i+1].apply(translator.translate, src='ja', dest='en').apply(getattr, args=('text',))
                # print(merge_en) # 1つのSeries　になる
                # 不要文字を置換
                sht2.range('F{}'.format(nextRow2)).options(
                    pd.Series, expand='table', index=False, header=None).value = merge_en
                i += 1
            except json.decoder.JSONDecodeError as e:
                print(str(e) + ' json Decoder Error 発生。本日の上限を達した模様。次へ') #リトライ...')
                break
                # time.sleep(1)
                # continue ここContinueのせいで、以降の作動にはいかず、次の検索フレーズループへ進む
        # break
        lastRow_title1 = sht2.range('H4').end(-4121).row  # ATK H=タイトル列
        nextRow = lastRow_title1 + 1

        # URL
        sht2.range('AT{}'.format(nextRow)).options(
            pd.Series, expand='table', index=False, header=None).value = merge.iloc[:, 1] # url_list 　ここをDF.iloc　option dataframeのやつ
        # title
        sht2.range('H{}'.format(nextRow)).options(
            pd.Series, expand='table', index=False, header=None).value = merge.iloc[:, 0]  # title_list
        # sht2.range('F{}'.format(nextRow)).options(
        #     pd.Series, expand='table', index=False, header=None).value = merge_en

        # Category, mainKey
        lastRow_title2 = sht2.range('H4').end(-4121).row
        # mainKey
        sht2.range('B{}:B{}'.format(nextRow, lastRow_title2)).options(transpose=True).value = mainKey
        # print(mainKey)  # どのカテゴリかひと目で分かるようキーをB列に
        # カテゴリ番号
        sht2.range('A{}:A{}'.format(nextRow, lastRow_title2)).options(transpose=True).value = categ_num
        # print(categ_num) #A列に

        wb2.save() #ここで保存することで, df2 はループごとにATKを読み込み、重複対象も前ループのリサ結果が対象になる
        # break # 2回繰り返し、url_list に２回めの取得結果を上書きしているのか、積み重ねているのか調べる

    # 重複除去>> 必要なし
    app.books.open("C:/Users/Kazuki Yuno/AppData/Roaming/Microsoft/Excel/XLSTART/PERSONAL.XLSB")
    # macro = app.macro('PERSONAL.XLSB!removeDup_singleCol')
    # macro()

    # 他の関数列オートフィル
    lastRow_sku = sht2.range('C4').end(-4121).row  # ここHにすると転記後の行だからズレが生じる。D も同じことが言えるか ＞言えない。この時点で数値が決まってるからOK
    # ここは、此のファイルで何も表記されない（最初の）列を選ぶ。
    lastRow_title3 = sht2.range('H4').end(-4121).row  # タイトル列
    def autofill_atk():
        col_list = ['D', 'E', 'G', 'Y', 'Z', 'AD', 'AG', 'AH', 'AI', 'AJ', 'AU', 'AY', 'BI', 'BK', 'BL', 'BM', 'BN',
                    'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 'BX']
        for col in col_list:  # DEG がタイトル関連、YZが重量、　ADが見込売値, AU~AYがヤフオク、 BK以降は利益計算
            try:
                sht2.range('{}{}'.format(col, lastRow_sku)).api.AutoFill(
                    sht2.range("{}{}:{}{}".format(col, lastRow_sku, col, lastRow_title3)).api,
                    AutoFillType.xlFillDefault)
                time.sleep(0.5)
            except com_error as e:
                print(str(e) + ' が発生。ループから抜ける')
                break # ループ抜ける
    autofill_atk()

    # SKU
    # lastRow_sku = sht2.range('C4').end(-4121).row
    nextRow_sku = lastRow_sku + 1
    # lastRow_url = sht2.range('AT4').end(-4121).row  # ATK AT＝URL列（オートフィル後）の最下行
    id_col = sht2.range('AU{}:AU{}'.format(nextRow_sku, lastRow_title3)).value
    sku_list = []
    # def left(text, n):
    # 	return text[:n]
    def right(text, n): # https://qiita.com/ty21ky/items/111d8d636fe7f6e29621
        return text[-n:]
    for id in id_col:  # ランダムID + ID + 日付
        sku_list.append(right(str(uuid4()) + '-' + str(id) + datetime.now().strftime('-%Y%m-%d%H-%M%S'), 50))
    # SKUの列＝C
    sht2.range('C{}'.format(str(nextRow_sku))).options(transpose=True).value = sku_list

    # ここでID出力。マクロ. Elems の場合は全てのIDを出力せず、追加されたIDを都度都度ファイルへ加えていく
    # このPyで追加したアイテムのIDだけでいい
    macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt_elem') # 状態列が空白の行から全てのIDをテキストへ
    macro()
    shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo_elem.txt',
                'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo_elem.txt')
    time.sleep(10) # 時間置かないと、elems_yahooでTxtファイルがないと言われることがある
    wb2.save()
    app.kill()

    #
    from sample_codes import elems_yahoo4 as elyahoo
    el_csv = r'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_yahoo_elements.csv'
    with open(el_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f:
        elyahoo.main(f, el_csv)


def remove_space_htmlTag(s):
    p = re.compile(r"<[^>]*?>")  # htmlTagを削除
    remove = p.sub("", s)
    space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    return space.replace('★', '').replace(']', '').replace('円（税 0 円） ', '')
    # re.subで記号も一括に削除できないか


def extract_key(url):
    """
    URLからキー（URLの末尾のISBN）を抜き出す。
    """
    m = re.search(r'/([^/]+)$', url)
    return m.group(1)

#
# def normalize_spaces(s):
#     """
#     連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
#     """
#     return re.sub(r'\s+', ' ', s).strip()
#

def check_if_Excel_runs():
    try:
        win32com.client.GetActiveObject("Excel.Application")
        # If there is NO error at this stage, Excel is already running
        print('Excel is running, please close first')
        xw.Book.close() # 全てのブックを消去
        xw.App.kill()
        sys.exit() # これは
    except:
        print('Excel is NOT running, this is good!')
    return


if __name__ == '__main__':
    main()



