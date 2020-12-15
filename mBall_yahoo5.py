#!/usr/bin/env python
# coding: utf-8

# <a href="https://colab.research.google.com/github/kazuki0505/zaico-fixcan_heroku/blob/master/mBall_yahoo5.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# # mBall_yahoo6 を作らず、5をコミットしてみ


# 4 は、SQL バージョン
##
# While i <151: つまり商品数１５１まで＝５０件/ページの３ページまでスクレイプする　
# mongoDB 無視
# これは、mBallの機能を担うコード。mBall_atk.pyも吸収してみた
# 　# mBall_yahooもmBall_atkも、画像１枚目を取得するかしないかの違いで、ほかは全く同じだから


import pandas as pd
# import numpy as np
# from openpyxl import load_workbook
import time
import re

import requests, bs4
# import lxml.html
# from pymongo import MongoClient
# import xlwings as xw
# import math
# from selenium import webdriver
# from selenium.common.exceptions import NoSuchElementException
# from xlwings.constants import AutoFillType
# import shutil
from datetime import datetime
from uuid import uuid4
from googletrans import Translator
import json
# import pandas as pd
# import pythoncom
# from pythoncom import com_error
# import win32com.client
# import win32com
# import sys
import psycopg2
from sqlalchemy import create_engine
import numpy as np

import os
current_dir = os.getcwd()


def main():
    # check_if_Excel_runs()
    # wb = r'C:\Users\Kazuki Yuno\Desktop\00.myself\04.Buyer\0.リサーチ\keyword\key_generator.xlsx'
# データベースの接続情報
#     connection_config = {
#         'user': 'kazuki005', # 'postgres',
#         'password': 'Larc-1225', # larc1225
#         'host': 'localhost', #'127.0.0.1'
#         'port': '5432',  # なくてもOK
#         'database': 'scraping' #'postgres'
#     }
#     global engine
#     engine = create_engine(
#         'postgresql://postgres:Larc-1225@localhost:5432/scraping'.format(**connection_config))
        # larc1225 postgres
        # 検索キーは、後の間を＋にする必要があるが、これエクセルの時点でやるか、ここでやるか> planner では空白で複合キーを生成するので、変更はここで

    # Heroku Postgresのコンフィグ
    connection_config = {
        'host': 'ec2-54-210-128-153.compute-1.amazonaws.com',
        'database': 'd5evq9s0k3ah3p',
        'user': 'tdmhdafruvebzx',
        'port': '5432',
        'password': '2b49dd7bf409cc17dfd288cf43faf04eef06e800e17fe2cab498191ac8b6373e'
    }
    global engine
    engine = create_engine(
        'postgres://tdmhdafruvebzx:2b49dd7bf409cc17dfd288cf43faf04eef06e800e17fe2cab498191ac8b6373e@ec2-54-210-128-153.compute-1.amazonaws.com:5432/d5evq9s0k3ah3p'.
            format(**connection_config))

    # con = psycopg2.connect

    market_df = pd.read_sql('market', con=engine, # SELECT文ではなく、テーブル名のみ
        columns=['categ num', 'main key', 'キーフレーズ'])\
        .dropna(subset=['キーフレーズ']) # キーフレーズ列のNan を消して表示

    categ_num_list = market_df.iloc[:, 0]#'categ num']
    mainKey_list = market_df.iloc[:, 1]#'main key'
    keyPhrase_list = market_df.iloc[:, 2] #['X-MEN 同人誌', 'batman 同人誌'] #.get_group('X-MEN 同人誌', 'batman 同人誌') # 検索キーを減らしたいなら、ここで
                                    # iloc、第一引数が行
    # app = xw.App(visible=True)  # False)
    # wb2 = app.books.open(atk)
    # sht2 = wb2.sheets[0]

    list_df = pd.DataFrame(columns=['タイトル', 'URL_y', 'ID',
                                    'Title', 'main key', 'Category'])
    # list_df
    # arr_title_url_id_ = np.empty([0, 3])
      #                                       0~ other japanese antique  14~ painting  18= prints
    #                                             ドラゴンボール 37  ラストは４５
            # これは不便、カテゴリ指定で検索ワードをグループ化しながら、毎日自動リサしてほしい
    # keyPhraase 番号振っても、途中からのリサにならない
    # ここ、keyPhraseだけ番号振ったらだめ、mainKryやcategは最初から記録してしまう>> 一括で番を振る
    # list(zip()) とすることで、一括して順番を指定できる　https://stackoverrun.com/ja/q/7531087
    for mainKey, categ_num, keyPhrase in list(zip(mainKey_list, categ_num_list, keyPhrase_list))[:2]: #[44:]: #[36:]: # [:2]
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
                itemid = extract_key(elem_url)
                itemid_list.append(itemid)
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
            break
        # 重複分はATKに追加しないようにする

        # title_list をATｋのタイトル列と比べ、もし重複していれば, title_listから重複分を削除. # ２つの円のベン図の半月 = df - merge(inner)
        # title_listとurl_list を接合 （titleだけ重複分を消しても、urlが残っているんじゃズレが生じるから
        df1 = pd.DataFrame({'タイトル': title_list, 'URL_y': url_list, 'ID': itemid_list}) #, columns=['SKU']) # 2つのリストを一つのDFに
        # pd.DataFrame({'Mean': mean, 'Median': med, 'SD': sd})
        # ここにsql_df 入れなくて良い？？ >> ループごとに、追加したてのタイトルも比較対象にしたいから、ここに入れて。違うキーで調べても、同じ品を取るケースに備えて
        # df1

        sql_df = pd.read_sql('atklist4', con=engine,
                             columns=['タイトル'])  # skiprows=2, encoding='cp932') #.columns = ['t\\itle']
        # for index, row in df.iterrows():
        #     if row # row['開始価格'] == row['開始価格2']
        #         df.drop(index, inplace=True)
        # sql_df

        on = ['タイトル']  # , 'url'] # https://stackoverflow.com/questions/48912242/how-to-drop-duplicates-from-one-data-frame-if-found-in-another-dataframe
        # merge = df1.merge(sql_df[on], on=on, how='left', indicator=True).\
        #     query('_merge == "left_only"').drop('_merge', 1) # 左＝df1にのみ存在する（(df2との重複を除く）タイトルにQueryしたあと、merge列を削除
        # # 既存のATKタイトルと、リサ結果のタイトルの重複は消えるが、結果タイトル(df1)内での重複は消えない
        # # ループごとにatk を保存し、df2読み込む毎に各ループ更新直後のリストを読み込めばいい
        # merge = merge.reset_index() #drop=True) # インデックスのずれにより空白行が生まれる問題が解決
        # merge
        merge = df1.merge(sql_df[on], on=on, how='left', indicator=True)
        merge = merge.query('_merge == "left_only"').drop('_merge', 1).reset_index()  # 左＝df1にのみ存在する（(df2との重複を除く）タイトルにQueryしたあと、merge列を削除
        print(merge)
        # merge.to_csv('merge.csv',
        #       header=None, index=None, sep=' ')
        # #### While try をコメントアウトしてるから後で戻して
        # #### リスト作成時、名前に連番が入ってしまうのを解決して
        # #### 18行にタイトルではない値が追加されてしまう＞iloc[i: i+1] の部分で、例えば17行まで来ると... ilocでインデックス17 =18行目（＝値なし）まで翻訳してリストにappendすることになる。 ＞＞ while len(merge) >= i: の = を外すことで解決。

        # タイトル整形、英訳前に>> HTML削除、不要文字置換
        # merge2 = remove_space_htmlTag(merge.iloc[:, 1])

        # タイトル翻訳
         # タイトル列に絞り、字数制限、余分の絵文字などを排除
        def left(text, n):
            return text[:n]
        merge_title = left(merge['タイトル'], 75).replace("e.g.", "").replace("™", "").\
            replace("♥", "").replace("½", "").replace("★", "").replace("&", "").\
            replace("◆", "").replace("■", "").replace("〇", "").replace("●", "").\
            replace("▽", "").replace("▼", "").replace("△", "").replace("▲", "").\
            replace("", "").replace("■", "").replace("■", "").replace("■", "") #.to_list()

        # merge_title = merge_title.reset_index()
        # print(merge_title)
        # ループで一行ずつ翻訳、Excelに入力＞ 一行ずつ翻訳、リストにしてSeries化
        translator = Translator()
        i = 0
        title_en_list = []
        #     print(len(merge))
        #     print(len(merge_title))
        while len(merge) > i: # 制限達したら、これパスしてXW転記もしないことにする。　一度エラー起きれば、リトライしてもずっとエラーだから、While要らない
            try:
                #一行ずつ翻訳
                merge_en = merge_title.iloc[i: i+1].\
                    apply(translator.translate, src='ja', dest='en').\
                    apply(getattr, args=('text',)).to_string(index=False) # values によってDtypeやNameといった情報が除外される
        #             上記の２行で、17行目の余分な値が発生している。Series[]
                # print(merge_en)  # 1つのSeries　になる
                title_en_list.append(merge_en)
                # df2.iloc[nextRow2, 5] = merge_en # 5列目, nextrowの行から
                # sht2.range('F{}'.format(nextRow2)).options(
                #     pd.Series, expand='table', index=False, header=None).value = merge_en
                i += 1

            except json.decoder.JSONDecodeError as e:
                print(str(e) + ' json Decoder Error 発生。本日の上限を達した模様。次へ') #リトライ...')
                break
                # time.sleep(1)
                # continue ここContinueのせいで、以降の作動にはいかず、次の検索フレーズループへ進む

        #         break
        #     print(len(title_en_list)) #やはり１８行カウントされるから黒
        #     merge_en

        # merge_title をSeries> リストに変換し、ループで一つずつ翻訳してtitle_en_list へAppend
        # iloc でSeriesを一つずつカットする上の方法は、インデックスまで取り込むためか、後にSeries化するとインデックスのための列が2列もできてしまう

        # for merge_en in merge_title: # Mergeの長さ16までループさせるのは、ここでも必要？
        #     try:
        #         merge_en.apply(translator.translate, src='ja', dest='en').apply(getattr, args=('text',))
        #         print(merge_en) # 1つのSeries になる
        #         title_en_list.append(merge_en)
            # except json.decoder.JSONDecodeError as e:
            #     print(str(e) + ' json Decoder Error 発生。本日の上限を達した模様。次へ') #リトライ...')
            #     break

        # ここでSQLテーブルのタイトル列へ自動で移動する
        title_en_list_sr = pd.Series(title_en_list, name='Title', index=None).reset_index(drop=True)#, inplace=True)#, index=None)#, name=None)
        # # merge_en.columns = 'Title'  # 列名をTitleにすることで、SQLのTitle列に追加される
        # # title_en_list_sr

        # # lastRow_title1 = sht2.range('H4').end(-4121).row  # ATK H=タイトル列
        # # break
        # # lastRow_title1 = df2.iloc[:, 7].tail(n) # H= 7
        # # nextRow = lastRow_title1 + 1
        #
        # # URLとタイトルのDF=mergeを、to_sql
        # # merge（URLとタイトルのdf） にmainkey, categ_numのdfを加え、SQL。
        main_categ_df = pd.DataFrame({'main key': mainKey, 'Category': categ_num},
                                     index=[0]) #, 1]) # index入れないとエラーになる　http://nishidy.hatenablog.com/entry/2016/03/10/015337
                                    # index=[0, 1] だと0行目と1行目が重複する
        # main_categ_df.to_csv('main_categ_df.csv',
        #       header=None, index=None, sep=' ')
        # 翻訳リミットが起きなかったループのみMergeと統合し、List_dfに蓄積していく

        # print(len(title_en_list_sr))
        # print(len(main_categ_df))
        # ### main_categのインデックスを空白から数字にすると、横連結すると起きた ValueError: Shape of passed values is... というのが解決した
        concat = pd.concat([merge, title_en_list_sr, main_categ_df], axis=1).\
            fillna(method='pad')
        # concat.to_csv('concat.csv',
        #       header=None, index=None, sep=' ')
        # concat = pd.concat([merge, main_categ_df], axis=1)
        # ### DF空箱にループ追加
        list_df = list_df.append(concat, ignore_index=True)
        # list_df.to_csv('list_df.csv',
        #       header=None, index=None, sep=' ')
        # #### main key, Categoryの列を、他列の行数まで同じ値で埋め合わせるためfillna(pad)を使えると思ったが、Numpyでは無理みたい。

        # ここで英訳リミットが来た時点のループでストップさせる処理
        # if e: # が起きたら
        #     break
        break

    # #### SKUを全ループ追加分を作成し、その列を横付け
    id_col = list_df['ID'] #.iloc[] # SKU
    # id_col.to_csv('id_col.csv',
    #           header=None, index=None, sep=' ')
    sku_list = []
    # def left(text, n):
    # 	return text[:n]
    def right(text, n): # https://qiita.com/ty21ky/items/111d8d636fe7f6e29621
        return text[-n:]
    for id in id_col:  # ランダムID + ID + 日付
        sku_list.append(right(str(uuid4()) + '-' + str(id) + datetime.now().strftime('-%Y%m-%d%H-%M%S'), 50))
    # SKUの列＝C
    # sht2.range('C{}'.format(str(nextRow_sku))).options(transpose=True).value = sku_list
    sr_sku = pd.Series(sku_list, name='SKU')
    # sr_sku
    global concat2
    concat2 = pd.concat([list_df, sr_sku], axis=1)
    # ここでSKU列に「SKU」と列名を与える。なぜ0~4はNaN？
    # concat2
    # 一行のエクセル関数DFを追加、下までフィル
    # global concat2
    # concat2 = pd.concat([concat, main_categ_df]).fillna(method='pad') #'ffill' と同等 # 空白を前の行で埋める https://riptutorial.com/ja/pandas/example/6188/%E4%B8%8D%E8%B6%B3%E3%81%97%E3%81%A6%E3%81%84%E3%82%8B%E5%80%A4%E3%82%92%E5%9F%8B%E3%82%81%E8%BE%BC%E3%82%80

    # ここでID出力。マクロ. Elems の場合は全てのIDを出力せず、追加されたIDを都度都度ファイルへ加えていく
    # このPyで追加したアイテムのIDだけでいい
    # macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt_elem') # 状態列が空白の行から全てのIDをテキストへ
    # macro()
    # shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo_elem.txt',
    #             'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo_elem.txt')
    elems_id_txt = f'{current_dir}\db_check_yahoo_elem.txt' # r'C:\zaico-fixcan_heroku\db_check_yahoo_elem.txt'
    # id_col.to_csv(elems_id_txt,
    #           header=None, index=None, sep=' ')#, mode='a') # mBall_elem_zaicoは、追加された分のIDの価格だけでいい
    id_col.to_sql('1.elem_id', con=engine, if_exists='append',  # or replace
                  index=False)

    # time.sleep(10) # 時間置かないと、elems_yahooでTxtファイルがないと言われることがある
    # wb2.save()
    # app.kill()

    # ### 価格・説明文・状態の要素取得、エクセル表計算を参考にした計算をSQLで

    # #### 税込 \d+ だと、数値int64でないといけないかも、11,620のように 間に,があるとマッチしないか

    from bs4 import BeautifulSoup,NavigableString
    #
    # html = """
    # <div class="product-price">
    #     <h3>
    #     £15.00
    #         <span class="price-standard">
    #             £35.00
    #         </span>
    #     </h3>
    # </div>
    # """
    # bs = BeautifulSoup(html,"xml")
    # result = bs.select_one("div",{"class":"product-price"})
    # print(type(result))
    #
    # fr = [element for element in result.h3 if isinstance(element, NavigableString)]
    # print(fr[0])

    # el_csv = f'{current_dir}\db_yahoo_elements.csv' # r'C:\zaico-fixcan_heroku/db_yahoo_elements.csv' #C:/Users/kazuki_juno/Desktop/00.Myself/04.Buyer/1.利益計算/db_yahoo_elements.csv'
    # with open(el_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f:
        # elyahoo.main(f, el_csv, concat2)
    el_main(id_col, concat2)


import csv # は要らない
def el_main(id_col, concat2): # el
    # writer = csv.writer(f)
    # with open(txt) as f: #
    #     page_id_list = [str(row) for row in f]
    # page_id_list = [str(row) for row in id_col]
    # img_list = []
    # id_list = []
    # arr = np.empty([0, 2])
    arr_descon = np.empty([0, 3]) # ここは３列か
    arr_img = np.empty([0, 2]) # 0, 2 だと２列分のみ＞ 
    arr_pr = np.empty([0, 2])
    # print(arr)
    for page_id in id_col: #[:5]: #[10:]:#[347:352]:#[:10]:
        print(page_id)
        url = f"https://page.auctions.yahoo.co.jp/jp/auction/{page_id}"
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
#                 print(src_fact)
                # if src_fact == []:
                #     print("画像が見つかりません。。。")
                # else:
                page_id_for_scrape = url.split('/')[-1]
                # elem_list = [elems_d, elems_c, page_id_for_scrape]

                # elem_list = pd.DataFrame(elem_list)
                # elem_list.to_sql('2.elems_dcid', con=engine, if_exists='append',  # or replace
                #     index=False)
                # writer.writerow(elem_list)
                time.sleep(0.2)
                
                img_np = np.array([[page_id_for_scrape], [src_fact]]).T  # transpose()  # elem_img]) # src_list]
                arr_img = np.r_[arr_img, img_np]

            # 価格
            # price = soup.select('dl > dd.Price__value')#[0]
            # price = soup.find("dd",{"class":"Price__value"})
            # print(price)
            # print(type(price))
            # print(price.p)# これだと1つ目のpタグしか取らない。一括で2つのpタグを取るにはループ可
            # print(price.div)# これでdiv内にあるpタグ2つを指定できた

            # https://stackoverflow.com/questions/52855089/beautifulsoup-find-exclude-nested-tag-from-block-of-interest
            # from bs4 import BeautifulSoup,NavigableString
            # price = soup.select("dd",{"class":"product-price"})
            # unwanted = [element for element in price.div if isinstance(element, NavigableString)]
            # タグp を指定することで、値下げ文を表示することができた、このQ&Aの事例は、指定することでそれ以外の小タグを除外するもの、今回は除外したいpタグを指定するか
            # で、Pタグ=値下げ文が無いIDがあるとエラーにならないよう、try except。
            # あとはこれをexclude
            # price.p にすると手前の一つしか指定できないから、price.divにすると、何も指定されない

            # print(unwanted)
            # unwanted = unwanted[0]
            # print(unwanted)
            # unwanted.extract()
            
            # unwanted_div = price.div # これでpタグ2つを消し、1円（税 0 円）と出た！！！！
            # これSelect にするとResultsetになり AttributeError: ResultSet object has no attribute 'div'
            # print(unwanted_div)
            # if unwanted_div == None: # pタグがないIDはunwanted がNoneとなるので、Noneはスルーするように
            #   pass
            # else:
            #   unwanted_div.extract()
            # print(price)

            all_fetched = [] # https://stackoverflow.com/questions/54259105/beautifulsoup4-find-all-non-nested-matches
            fetched = soup.find('dd', class_='Price__value')
            # print(str(1) + '\n'+ str(fetched))

            unwanted_div = fetched.div
            
            while fetched is not None:
              if unwanted_div == None: # pタグがないIDはunwanted がNoneとなるので、Noneはスルーするように
                pass
              else: # pタグ＝値引き文がある場合
                unwanted_div.extract()
                # print(str(2) + '\n'+ str(fetched))

              all_fetched.append(fetched)
              # print(str(3) + '\n'+ str(fetched))
              try:
                last = list(fetched.descendants)[-1]
                # print(str(4) + '\n'+ str(last))
              except IndexError:
                break
              fetched = last.findNext('dd', class_='Price__value') # Price__priceDown') #'Price__value')
              # print(str(5) + '\n'+ str(fetched))
            # print(all_fetched)

            # https://www.hellojava.com/a/59175.html
            # そのまま
            # divs = soup.find('div', {'class':'article_body'})
            # ops = [element for element in divs.div if isinstance(element, NavigableString)]
            # for op in ops:
            #   print(op.strip().replace('n', ''))
            # アレンジ
            # divs = soup.find('dl', {'class':'Price__body Price__body--none'})
            # ops = [element for element in divs.dd if isinstance(element, NavigableString)]
            # for op in ops:
            #   print(op.strip().replace('n', ''))


            # extract() を使う https://stackoverflow.com/questions/40760441/exclude-unwanted-tag-on-beautifulsoup-python
            # price = price.find('div') # unwanted=不必要
            # price.extract()
            
            #　2つ目の回答  ＞ 「,」 だけ出てくる
            # external_span = soup.find('span')
            # price = []
            # for x in price:
            #   if isinstance(x, bs4.element.NavigableString):
            #     price.append(x.strip())
            # print(" ".join(price))

            # 一番下の例＞ 何も表示されない
            # for i in price:
            #   if 'class' in i.attrs:
            #     if "Price__priceDown" in i.attrs['class']:
            #       price = i.text
            #       print(price + 'テスト')

            # https://stackoverflow.com/questions/58904013/extract-text-content-from-nested-html-while-excluding-some-specific-tags-scrapy
            # for tag in price.find('div', class_="Price__priceDown"): #['a', 'h1']): # give the list of tags you want to ignore here.
            #   tag.replace_with('')
            #   print(price)
            # priceというHTMLのリストを、findで取ることはできない

            # ここから
            price2 = remove_space_htmlTag_pr(str(all_fetched)) 
            # print(price2)
            # pr_list.append(elems_d)
            日件 = soup.select('.Count__number')
            # print(日件)
            日件2 = remove_space_htmlTag_pr(str(日件))
            # print(日件2)

            if '終了' in 日件2:  # 終了品は elems=価格 を空白に
                # print(日件2)
                price2 = ', '  # 空白のみだと、「, 」で分割する時エラー起きるから
                print(price2)  # + ' 終了')

            else:  # 出品中なら
                pr_title = soup.select('dt[class="Price__title"]')
                pr_title2 = remove_space_htmlTag_pr(str(pr_title))
                # print(pr_title2)
                if '現在価格' not in pr_title2:  # 現在価格が無い＝即決価格のみなら
                    price2 = ', ' + price2  # 価格の手前
                    print(price2)  # + ' 即決のみ')
                else:  # 現在価格あるなら
                    print(price2)  # + ' 現在') # ここは最初のprice2になる

        except requests.exceptions.HTTPError as err:
            print(err)
            elems_d = ''# httpエラーのIDが飛ばされていたので
            elems_c = ''
            src_fact = ''
            price2 = ''

        # try とexcept のスコープ両方に入れいてたが、zaicoは双方の後に、以下を入れてる
        page_id_for_scrape = url.split('/')[-1]

        # elem_list = [elems_d, elems_c, page_id_for_scrape]
        # writer.writerow(elem_list)
        # elem_list = pd.DataFrame(elem_list)
        # elem_list.to_sql('3.elems_dcid', con=engine, if_exists='append',  # or replace
        #             index=False) # 前回は同じCSVファイルに出してたから、同じSQLデータベースで良いはず

        dc_np = np.array([[page_id_for_scrape], [elems_d], [elems_c]]).T  # transpose()  # elem_img]) # src_list]
        arr_descon = np.r_[arr_descon, dc_np]
        
#         img_np = np.array([[page_id_for_scrape], [src_fact]]).T  # transpose()  # elem_img]) # src_list]
#         arr_img = np.r_[arr_img, img_np]
        
        pr_np = np.array([[page_id_for_scrape], [price2]]).T  # transpose()  # elem_img]) # src_list]
        arr_pr = np.r_[arr_pr, pr_np]
        
        time.sleep(1)
    
        # break

    # DF化
    # 説明、状態の DF化
    descon_df = pd.DataFrame(arr_descon, columns=['ID', '説明', '状態_y']).iloc[:, 1:3]#.column  # 0. 1行目のみ
    #     descon_df.column = ['説明', '状態']
    # descon_df

    # 画像
    img_df = pd.DataFrame(arr_img)
    print(img_df)
    # img_df.to_csv('df_img.csv')
    img_df.to_sql('4.img_df', con=engine, if_exists='append',  # or replace
                    index=False)
    # def img_spread(arr):  # (img_list):
    img_df = pd.DataFrame(arr_img, columns=['ID', '画像'])  # .iloc[:, 1:]
    img_df.columns = ['ID', '画像']  # 列名指定 # ここに価格２列を追加
    # img_df
    #     img_df.to_csv('df_img.csv')
    def f(a):  # 単なるGroupBy, apply ではなく、関数 f を組むことで、画像URLを一列に集約するだけでなく、各列に分割までできた  # https://ja.stackoverflow.com/questions/24845/python%E3%81%AEpandas%E3%81%A7-%E7%B8%A6%E6%8C%81%E3%81%A1%E3%81%AE%E3%83%87%E3%83%BC%E3%82%BF%E3%82%92%E6%A8%AA%E6%8C%81%E3%81%A1%E3%81%AB%E3%81%99%E3%82%8B%E3%82%88%E3%81%84%E6%96%B9%E6%B3%95%E3%82%92%E6%95%99%E3%81%88%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84
        a.index = [0 for i in range(len(a))]
        del a['ID']  # 列名指定
        out = a[0:1]
        for i in range(1, len(a)):
            out = out.join(a[i:i + 1], rsuffix='{0}'.format(i))
        return out
    global grped  # ここでiloc かける
    img_grped = img_df.groupby(img_df['ID'], sort=False).apply(f)
    # grped
    img_grped = img_grped.iloc[:, 1:8].reset_index(drop=True)  # , inplace=True) # おまけに、列名まで生成されてる!　ここで順を崩さないように
    # return grped
    # grped  # https://stackoverflow.com/questions/48044542/groupby-preserve-order-among-groups-in-which-way
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
    # img_grped.to_csv('merge_imgs3.csv')
    img_grped.to_sql('5.img_grped', con=engine, if_exists='append',  # or replace
                    index=False)
    # img_spread(arr_img)

    #  価格のDF化
    pr_df = pd.DataFrame(arr_pr, columns=['ID','価格2種'])
    # pr_df
    # #### https://stackoverflow.com/questions/57463127/splitting-a-column-in-dataframe-using-str-split-function
    # #### DFの列をSplitしながら生成された列の名を割り当てる方法がいくつか
    #     print(pr_df)
    pr_df[['現在価格', '即決価格']] = pr_df['価格2種'].str.split(', ', expand=True) #.rename({0: 'First_Name', 1: 'Second_Name'})], axis=1)
    pr_df

    pr_df2 = pr_df.iloc[:, [2, 3]]  # drop([1], axis=1)
    
    #     pr_df2.column = ['ID', '現在価格', '即決価格']
    #     ここコメントアウトする2つのうち一つエラー消える

    # pr_csv = f'{current_dir}\db_check_yahoo4.csv' #'C:\zaico-fixcan_heroku\db_check_yahoo4.csv' #'C:/Users/kazuki_juno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo4.csv'
    # pr_df2.to_csv(pr_csv, header=False, index=False)
    pr_df2.to_sql('6.pr_df2', con=engine, if_exists='append',  # or replace
                    index=False)

    concat3 = pd.concat([concat2, descon_df, img_grped, pr_df2], axis=1) #ここが問題
                         # 説明と状態、画像、価格
    # concat3.to_csv('concat3.csv')
    concat3.to_sql('7.concat3', con=engine, if_exists='append',  # or replace
                    index=False)
    # # sql から追加した分を読み取る？
    # # 価格を含めたDFを、後の現在価格の列を用いて計算するため、
    # sql_df = pd.read_sql()


    # 一行の数式を設定後、設定後の列をdf[]で表し、新たに数式を設定するのでOK か
    # 一度dfにしないといけなくなるから、df[]は要らない
    # 価格系、これはzaico_yahooへ移行
    # 現在価格 = concat3['現在価格']#.iloc[0]
    # 即決価格 = concat3['即決価格']#.iloc[0]
    # 相場価格 = IF(AX8=0, AV8*3, AX8*1.5) # AX 即決価格、AV= 現在価格 # 両者とも、Zaicoした後にわかること
    # 即決価格
    # 現在価格
    # concat3['相場価格'] = int(concat3['現在価格']) / int(concat3['即決価格'])
    # print(concat3['即決価格'].dtype)
    # print(即決価格.dtype)
    # #### 列ごとReplace, この際、strを入れることで正常に置換できた（なぜかは不明
    # 即決価格 = 即決価格.str.replace(' ', '').str.replace(' ', '').str.replace(',', '') #({' ': '', ',': ''}) #.astype('int64'))
    # print(即決価格)
    # #### astype(float64)は駄目だったので、to_numeric()で解決　
    # print(即決価格.astype('int64'))
    # print(pd.to_numeric(即決価格)) #astype('int64'))

    即決価格 = pd.to_numeric(concat3['即決価格'].str.replace(' ', '').str.replace(',', ''))
    # print(即決価格)
    # np.isnan も pd.isnull でも同じ
    # np.isnan(即決価格)
      # print('Yes!!
    # pd.isnull(即決価格)
    # if np.isnan(即決価格) == True:
    #   print('Yes!!')
    # 即決価格.str.isnumeric()#astype(str).str.isnumeric()

    現在価格 = pd.to_numeric(concat3['現在価格'].str.replace(' ', '').str.replace(',', ''))
    # print(現在価格)
    # concat3['相場価格'] = 現在価格 / 即決価格
    # 相場価格 = concat3['相場価格']
    # print(相場価格)
    # 即決価格.isnull()
    # テスト = 現在価格*3
    # print(テスト)
    # ### もし即決価格が数値なら現在価格を３倍に、もし数値でないなら1.5倍の相場価格にする
    import math
    # import numpy as np
    # x = float('nan')
    # concat3['相場価格'] = 現在価格* 3 if 即決価格.isnull() else 現在価格* 1.5
    # concat3['相場価格'] = 現在価格* 3 if np.isnan(即決価格)==True else 現在価格* 1.5
    # concat3['相場価格'] = concat3['現在価格']* 3 if np.isnan(concat3['即決価格']) else concat3['現在価格']* 1.5
    # concat3['相場価格'] = 現在価格* 3 if 即決価格.astype(str).str.isnumeric() else 現在価格* 1.5
    # 相場価格 = concat3['相場価格']
    # print(相場価格)
    # ####  ～ というエラー解決としてたどり着いた https://stackoverflow.com/questions/55090862/how-to-resolve-valueerror-the-truth-value-of-a-series-is-ambiguous-use-a-empty
    # def my_function(value):#, current):
    #     if np.isnan(value): # value.isnumeric()
    #         return 現在価格 * 3 # ここが掛け算できてない
    #         # 現在価格 * 3
    #     else:
    #     # elif value >= 10 or value < 19:
    #         return 現在価格 * 1.5
    #         #  現在価格 * 1.5
    # concat3['相場価格'] = 即決価格.apply(my_function) #, 即決価格)#, 現在価格)
    # 相場価格 = concat3['相場価格']
    # print(相場価格)
    # my_function には、現在価格を変数にするべきか、だとしたら引数がself と2つになり、Series.apply()は使えない
    # >> lambda
    # #### 引数が複数以上ある定義関数を扱う場合。map(定義関数, X, Y)　applyも同様
    # https://qiita.com/min9813/items/8a0f5d59f7ae6efa7072
    def func_soba(即決, 現在):
        if np.isnan(即決): # value.isnumeric() # 即決がないなら
            return 現在 * 3 # ここが掛け算できてない
            # ここはもっと設定を詳細に。1,000円以下は pass　1,000-2000は *5 倍とか
            # 現在のみ＞　パス　は避けたい
        else: # 即決価格があり、現在が無いなら or 現在があるなら
        # elif value >= 10 or value < 19:
            if np.isnan(現在):
                return 即決 * 1.5
            else:
                return 現在 * 3 # ここの数字は要検討
    # print(即決価格)
    concat3['相場価格'] = list(map(func_soba, 即決価格, 現在価格)) #, 現在価格)
    # apply ではなく map()にすると <map object at 0x1073d5588> となる。
    # これはMapイテレータというもので、リストにする必要がある＞＞ list()で囲む　https://note.nkmk.me/python-map-list-iterator/
    # 成功‼‼
    相場価格 = concat3['相場価格']
    # print(相場価格)
    # f = lambda x: 現在価格*3 if np.isnan(x) else 現在価格*1.5
    # concat3['相場価格'] = 即決価格.apply(f) #lambda n:
    # 相場価格 = concat3['相場価格']
    # print(相場価格)
    # #### 置換 ' 49,000'から 空白をなくす, かつ整数intにする. 列ごとする方法は？
    # 自己設定価格 = 0
    #   # 最高販売価格 = 0 if not str(max(相場価格, 自己設定価格)).isnumeric() else max(相場価格, 自己設定価格)
    # 最高販売価格 = 0 if np.isnan(str(max(相場価格, 自己設定価格))) else max(相場価格, 自己設定価格)
    # 最高販売価格
      # もし最大値が数値でないなら 0, 数値なら最大値
      #.isnumeric() # IFERROR(MAX(AD8,Q8,AF8),0) # AD相場価格 Q AF自己認定価格

    # もし最大値が数値でないなら 0, 数値なら最大値
    def func_max(相場, 自己設定, 現在, 即決):
      # if np.isnan(max(相場, 自己設定, 現在, 即決)): # 最高販売価格が０＞ NaNとして判断されてる。が、そもそも最大値が数値でないことのはありえない。０という数値がある限り、最大値がNaNになることはありえない
      #   return 0 # ここが掛け算できてない
      # else:
        return max(相場, 自己設定, 現在, 即決)

    concat3['自己設定価格'] = 0 # ここは一つ一つを設定することになるよね
    自己設定価格 = concat3['自己設定価格']
    # print(自己設定価格)
    concat3['最高販売価格'] = list(map(func_max, 相場価格, 自己設定価格, 現在価格, 即決価格))
    # concat3['最高販売価格'] = 0 if not str(max(相場価格, 自己設定価格)).isnumeric() else max(相場価格, 自己設定価格)
    最高販売価格 = concat3['最高販売価格']
    # 最高販売価格
    def func_仕入れ(即決, 相場):
      return min(即決, 相場)
    concat3['最安仕入価格'] = list(map(func_仕入れ, 即決価格, 相場価格)) # 以降は、他ECから取得するようになったら　,
                  # 落札相場価格,仕入れ値上限, 価格_r, 価格_a, 価格_m, 価格_o)
                      #AN, AW8,AX8,AY8,AR8,BC8,BF8)
    最安仕入価格 = concat3['最安仕入価格']
    # 最安仕入価格
    # これはURL列から抽出
    希望利益率 = 25
    # =ROUNDDOWN(AH8*0.861-(AH8*BS8/100)-BL8,1) # AH最高売値 BS希望利益率 BL送料
    仕入送料 = 1000 #
    # 重量、ounce, pound, kg は、elems_yahoo4で取得するから、恐らく後で移行する
    ounce = 0
    pound = 0
    kg = 0.7 # ある列の計算式
    # integrated = if(ounce>0, ounce*0.03, if(pound>0,pound*0.45, if(kg>0,kg)))
    integrated = ounce * 0.03 if ounce > 0 else pound * 0.45 if pound > 0 else kg # if kg > 0 # https://note.nkmk.me/python-if-conditional-expressions/
    # print(integrated)
    # integrated = if(ounce>0, ounce*0.03, if(pound>0,pound*0.45, if(kg>0,kg)))
    # if ounce > 0:
    #     integrated = ounce * 0.03
    # elif pound > 0:
    #     integrated = pound * 0.45
    # else kg > 0:
    #     integrated = kg
    # integ_col = df['integrated'] # 下記、df[integrated] 省略したい
    送料設定 = "0~0.3kg" if integrated<0.3 else "0.3~0.5kg" if integrated<0.5 else "0.5~0.8kg" if integrated<0.8 else    "0.8~1.0kg" if integrated<1 else "1.0~1.5kg" if integrated<1.5 else "1.5~2.0kg" if integrated<2 else        "2.0~2.5kg" if integrated<2.5 else "2.5~3.0kg" if integrated<3 else "3.5kg" if integrated<3.5 else        "4.0kg" if integrated<4 else "4.5kg" if integrated<4.5 else "5.0kg" if integrated<5 else        "5.5kg" if integrated < 5.5 else "6.0kg" if integrated < 6 else "7.0kg" if integrated< 7 else        "8.0kg" if integrated < 8 else "9.0kg" if integrated< 9 else '10.0kg以上' # Z = integrated
    # print(送料設定)
    # 送料設定_col = df['送料設定']
    送料 = 935 if 送料設定 == "0~0.3kg" else 1235 if 送料設定 == "0.3~0.5kg" else 1685 if 送料設定 == "0.5~0.8kg" else    1985 if 送料設定 == "0.8~1.0kg" else 2525 if 送料設定 == "1.0~1.5kg" else 3065 if 送料設定 == "1.5~2.0kg" else 5000
    # 後で 1985 if 送料設定 == "2.0~2.5kg" else 2525 if 送料設定 == "2.5~3.0kg" else 3065 if 送料設定 == "1.5~2.0kg" else\
    # print(送料)
    最高売値 = 最高販売価格 + 送料 + 仕入送料  # AG8+BL8+BI8
    # 最高売値
    粗利 = 最高売値 - 最安仕入価格  # AH8-AI8
    出品料 = 0 # なし
    # 最高売値col = df['最高売値']
    落札料 = 最高売値* 0.1
    Paypal = round(最高売値* 0.039, 1)
    支出合計 = round(sum(送料 + 出品料 + 落札料 + Paypal + 仕入送料), 1)
    仕入れ値上限 = round(最高売値 * 0.861 - (最高売値 * 希望利益率 / 100) - 送料, 1)
    営業利益 = 粗利 - 支出合計
    利益率 = round(最高売値 / 営業利益* 100, 1)
    販売額 = round((最安仕入価格 + 送料)/ (1- 希望利益率/100- 0.139), 1) #=ROUNDDOWN((AI4+BL4)/(1-BS4/100-0.139),1)
    希望営業利益 = 販売額 - 最安仕入価格 - 支出合計
    Positive = round((最安仕入価格 + 送料)/ (1- 0.4- 0.139),1) # 40%
    Middle = round((最安仕入価格 + 送料)/ (1- 0.25- 0.139),1) # 25%
    Negative = round((最安仕入価格 + 送料)/ (1- 0.08- 0.139),1) # 8
    # 横一列のDF　これをto_sql 直前に追加、最終行までフィル
    funcs_df = pd.DataFrame({'kg': kg, 'integrated': integrated, '相場価格': 相場価格,
                            '最高販売価格': 最高販売価格, '最高売値': 最高売値, '最安仕入価格': 最安仕入価格,
                            '粗利': 粗利, '希望利益率': 希望利益率, '仕入送料': 仕入送料, '送料設定': 送料設定,
                            '送料': 送料, '出品料': 出品料, '落札料': 落札料, 'Paypal': Paypal,
                            '支出合計': 支出合計, '仕入れ値上限': 仕入れ値上限, '営業利益': 営業利益,
                           '利益率': 利益率, '販売額': 販売額, '希望営業利益': 希望営業利益,
                           'Positive': Positive, 'Middle': Middle, 'Negative': Negative})
    # funcs_df.to_csv('funcs_df.csv')
    funcs_df.to_sql('8.funcs_df', con=engine, if_exists='append',  # or replace
                    index=False)
    # funcs_df
    concat_fin = pd.concat([concat3, funcs_df], axis=1).drop('index', axis=1)#.fillna(method='pad')
    print(concat_fin)
    # concat_fin.to_csv('concat_fin.csv')
    concat_fin.to_sql('atklist4', con=engine, if_exists='append',  # or replace
                    index=False)
    # el_main()


# update_atk(el, grped)
# mBall_elem_zaicoは、新たに追加されたID分の価格を取得できればいい

# img_spread()


# def remove_space_htmlTag(s):
#     p = re.compile(r"<[^>]*?>") # htmlTagを削除
#     remove = p.sub("", s)
#     space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
#     return space.replace('[', '').replace(']', '') # [] を置換
#
# def remove_space_htmlTag_pr(s):
#     p = re.compile(r"<[^>]*?>") # htmlTagを削除
#     remove = p.sub("", s)
#     space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
#     return space.replace('[', '').replace(']', '').replace('円（税 0 円） ', '')
#
#
#  # mergeのURL列から、新たにitemID 列を導き出す
# def extract_key(url): # URLからキー（URLの末尾のISBN）を抜き出す。
#     m = re.search(r'/([^/]+)$', url) # /([^/]+)$
#     return m.group(1)

#### 新しいVer

def remove_space_htmlTag(s):
    p = re.compile(r"<[^>]*?>")  # htmlTagを削除
    remove = p.sub("", s)
    space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    return space.replace('[', '').replace(']', '')  # [] を置換


def remove_space_htmlTag_pr(s):  # 価格用
    p = re.compile(r"<[^>]*?>")
    remove = p.sub("", s)
    remove = re.sub(r'\s+', ' ', remove).strip()  # .sub(r'(円（税込\d+円）', remove)
    p = re.compile(r'(円（税込 \d+,\d+ 円）)')  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    remove = p.sub("", remove)
    # space = re.sub(r'(円（税込\d+円）)', space)
    return remove.replace('[', '').replace(']', '').replace('円（税 0 円） ', '')


# mergeのURL列から、新たにitemID 列を導き出す
def extract_key(url):  # URLからキー（URLの末尾のISBN）を抜き出す。
    m = re.search(r'/([^/]+)$', url)  # /([^/]+)$
    return m.group(1)


if __name__ == '__main__':
    main()
