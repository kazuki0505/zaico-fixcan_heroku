# 4 は、SQL バージョン
### ####

# While i <151: つまり商品数１５１まで＝５０件/ページの３ページまでスクレイプする　
# mongoDB 無視
# これは、mBallの機能を担うコード。mBall_atk.pyも吸収してみた
# 　# mBall_yahooもmBall_atkも、画像１枚目を取得するかしないかの違いで、ほかは全く同じだから


import pandas as pd
import numpy as np
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
# # import pandas as pd
# import pythoncom
# from pythoncom import com_error
# import win32com.client
# import win32com
# import sys
import psycopg2
from sqlalchemy import create_engine



def main():
    # check_if_Excel_runs()
    # wb = r'C:\Users\Kazuki Yuno\Desktop\00.myself\04.Buyer\0.リサーチ\keyword\key_generator.xlsx'

    # データベースの接続情報
    connection_config = {
        'user': 'postgres',
        'password': 'larc1225',
        'host': 'localhost',
        'port': '5432',  # なくてもOK
        'database': 'scraping'
    }
    global engine
    engine = create_engine(
        'postgresql://postgres:larc1225@localhost:5432/scraping'.format(**connection_config))

    # 検索キーは、後の間を＋にする必要があるが、これエクセルの時点でやるか、ここでやるか> planner では空白で複合キーを生成するので、変更はここで

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
    arr_title_url_id_ = np.empty([0, 3])

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
        df1 = pd.DataFrame({'タイトル': title_list, 'url': url_list, 'ID': itemid_list}) #, columns=['SKU']) # 2つのリストを一つのDFに
        # pd.DataFrame({'Mean': mean, 'Median': med, 'SD': sd})
        # ここにsql_df 入れなくて良い？？ >> ループごとに、追加したてのタイトルも比較対象にしたいから、ここに入れて。違うキーで調べても、同じ品を取るケースに備えて
        sql_df = pd.read_sql('atklist2', con=engine,
                             columns=['タイトル'])  # skiprows=2, encoding='cp932') #.columns = ['title']
        # for index, row in df.iterrows():
        #     if row # row['開始価格'] == row['開始価格2']
        #         df.drop(index, inplace=True)
        on = ['タイトル']  # , 'url'] # https://stackoverflow.com/questions/48912242/how-to-drop-duplicates-from-one-data-frame-if-found-in-another-dataframe
        merge = df1.merge(sql_df[on], on=on, how='left', indicator=True)\
            .query('_merge == "left_only"').drop('_merge', 1) # 左＝df1にのみ存在する（(df2との重複を除く）タイトルにQueryしたあと、merge列を削除
        print(merge) # タイトルと url
        # 既存のATKタイトルと、リサ結果のタイトルの重複は消えるが、結果タイトル(df1)内での重複は消えない
        # ループごとにatk を保存し、df2読み込む毎に各ループ更新直後のリストを読み込めばいい



        # タイトル整形、英訳前に>> HTML削除、不要文字置換
        # merge2 = remove_space_htmlTag(merge.iloc[:, 1])

        # タイトル翻訳
        # ループで一行ずつ翻訳、Excelに入力＞ 一行ずつ翻訳、リストにしてSeries化
        translator = Translator()
        i = 0
        title_en_list = []
        while len(merge) >= i: # 制限達したら、これパスしてXW転記もしないことにする。　一度エラー起きれば、リトライしてもずっとエラーだから、While要らない
            try:
                # lastRow_title2 = sht2.range('F4').end(-4121).row  # ATK H=タイトル列
                # # lastRow_title2 = df2.iloc[:, 5].tail(n) # F= ５番目= 英訳の列  # tail(n)で、最下行を求める
                # nextRow2 = lastRow_title2 + 1

                # 文字列制限＋記号の置換をしてから、翻訳。
                def left(text, n):
                    return text[:n]
                merge_title = left(merge['タイトル'], 75).replace("e.g.", "").replace("™", "").replace("♥", "").replace("½", "").\
                replace("★", "").replace("&", "").replace("◆", "").replace("■", "")

                merge_en = merge_title.iloc[i: i+1].apply( #一行ずつ翻訳
                    translator.translate, src='ja', dest='en').apply(getattr, args=('text',))
                # print(merge_en) # 1つのSeries　になる
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
            break
        # ここでSQLテーブルのタイトル列へ自動で移動する
        title_en_list_sr = pd.Series(title_en_list, name='Title')
        # merge_en.columns = 'Title'  # 列名をTitleにすることで、SQLのTitle列に追加される


        # break
        # lastRow_title1 = sht2.range('H4').end(-4121).row  # ATK H=タイトル列
        # lastRow_title1 = df2.iloc[:, 7].tail(n) # H= 7
        # nextRow = lastRow_title1 + 1

        # URLとタイトルのDF=mergeを、to_sql
        # merge（URLとタイトルのdf） にmainkey, categ_numのdfを加え、SQL。
        main_categ_df = pd.DataFrame({'main key': mainKey, 'Category': categ_num},
                                     index=['', '']) # index入れないとエラーになる　http://nishidy.hatenablog.com/entry/2016/03/10/015337

        # リストも加えられる？ df を対象にできる？df のmergeによって、タイトルの重複を避けられるから、DFでやりたい
        all_np = np.array([[merge], [title_en_list_sr],
                           [main_categ_df]]).T
        print(all_np)
        all_np.fillna(method='pad')  # transpose()  # elem_img]) # src_list]
        # 行数合わないなら、np.arrayにfillna

        arr_title_url_id_ = np.r_[arr_title_url_id_, all_np]
        break
        # URL
        # df2.iloc[nextRow, 46] = merge.iloc[:, 1]
        # sht2.range('AT{}'.format(nextRow)).options(
        #     pd.Series, expand='table', index=False, header=None).value = merge.iloc[:, 1] # url_list 　ここをDF.iloc　option dataframeのやつ
        # タイトル
        # df2.iloc[nextRow, 7] = merge.iloc[:, 0]
        # sht2.range('H{}'.format(nextRow)).options(
        #     pd.Series, expand='table', index=False, header=None).value = merge.iloc[:, 0]  # title_list

        # sht2.range('F{}'.format(nextRow)).options(
        #     pd.Series, expand='table', index=False, header=None).value = merge_en

        # lastRow_title2 = df2.iloc[:, 7].tail(n)  # H= 7
        # lastRow_title2 = sht2.range('H4').end(-4121).row

        # mainKeyとcateg_numを、タイトル列の最下行(lastRow_title2)まで埋める＞SQLで行番号を判別、選択できるか
        # 新たに加えたタイトル列と同じ数だけその２列を埋める。これ他のエクセル関数入った列のオートフィル処理の箇所にも使う
        # mainKey
        # df2.iloc[nextRow: lastRow_title2, 1] = mainKey
        # sht2.range('B{}:B{}'.format(nextRow, lastRow_title2)).options(transpose=True).value = mainKey
        # # print(mainKey)  # どのカテゴリかひと目で分かるようキーをB列に
        # # カテゴリ番号
        # # df2.iloc[nextRow: lastRow_title2, 0] = categ_num
        # sht2.range('A{}:A{}'.format(nextRow, lastRow_title2)).options(transpose=True).value = categ_num
        # print(categ_num) #A列に

        # wb2.save() #ここで保存することで, df2 はループごとにATKを読み込み、重複対象も前ループのリサ結果が対象になる
        # break # 2回繰り返し、url_list に２回めの取得結果を上書きしているのか、積み重ねているのか調べる

    # ここで、全ループ取得分のDFを作る。
    all_df = pd.DataFrame(arr_title_url_id_)

    # 重複除去>> 必要なし
    # app.books.open("C:/Users/Kazuki Yuno/AppData/Roaming/Microsoft/Excel/XLSTART/PERSONAL.XLSB")
    # macro = app.macro('PERSONAL.XLSB!removeDup_singleCol')
    # macro()

    #
    # 他の関数列オートフィル　SQLで最下行まで
    # エクセル関数は、SQL内で新たに作るのか、PandasやPyで新たに作るのか、を決めた後にオートフィル
    # エクセルのオートフィルは、Pandasでは一行のみ完成すれば、あとはそれを全行埋める
    # fillna(method='')で前の行と同じ値にすれば良い？
    # 列間の計算をさせる


    # lastRow_sku = sht2.range('C4').end(-4121).row  # ここHにすると転記後の行だからズレが生じる。D も同じことが言えるか ＞言えない。この時点で数値が決まってるからOK
    # # ここは、此のファイルで何も表記されない（最初の）列を選ぶ。
    # lastRow_title3 = sht2.range('H4').end(-4121).row  # タイトル列
    # def autofill_atk():
    #     col_list = ['D', 'E', 'G', 'Y', 'Z', 'AD', 'AG', 'AH', 'AI', 'AJ', 'AU', 'AY', 'BI', 'BK', 'BL', 'BM', 'BN',
    #                 'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 'BX']
    #     for col in col_list:  # DEG がタイトル関連、YZが重量、　ADが見込売値, AU~AYがヤフオク、 BK以降は利益計算
    #         try:
    #             sht2.range('{}{}'.format(col, lastRow_sku)).api.AutoFill(
    #                 sht2.range("{}{}:{}{}".format(col, lastRow_sku, col, lastRow_title3)).api,
    #                 AutoFillType.xlFillDefault)
    #             time.sleep(0.5)
    #         except com_error as e:
    #             print(str(e) + ' が発生。ループから抜ける')
    #             break # ループ抜ける
    # autofill_atk()
        #

    # SKU　　id の列をタイトル列の最終行まで抜き取り、それを一行ずつSKU生成の材料に使う
    # lastRow_sku = sht2.range('C4').end(-4121).row
    # nextRow_sku = lastRow_sku + 1
    # lastRow_url = sht2.range('AT4').end(-4121).row  # ATK AT＝URL列（オートフィル後）の最下行
    # id_col = sht2.range('AU{}:AU{}'.format(nextRow_sku, lastRow_title3)).value
    # df2（atklist）のid列を、エクセルでいうnextRow_skuの行から取得 #
    id_col = all_df['ID'] #.iloc[] # SKU
    sku_list = []
    # def left(text, n):
    # 	return text[:n]
    def right(text, n): # https://qiita.com/ty21ky/items/111d8d636fe7f6e29621
        return text[-n:]
    for id in id_col:  # ランダムID + ID + 日付
        sku_list.append(right(str(uuid4()) + '-' + str(id) + datetime.now().strftime('-%Y%m-%d%H-%M%S'), 50))
    # SKUの列＝C
    # sht2.range('C{}'.format(str(nextRow_sku))).options(transpose=True).value = sku_list
    sr_sku = pd.Series(sku_list)

    # merge, オーtフィルする列、sku_list, 全てDFにまとめ、一発で・to_sql
    # concatすることで、mergeの行数の分、df3の行数も増やしたい
    # これで一番最後にsr_titleをconcatしたいのだが、なんせ翻訳が制限で途中で中止される。
    # 他の列と行数が変わってしまう。その翻訳できなかった差分は、とりあえず何かしら値を入れたら良い。> fillna()
    # titleは fillna(0)で、df3 は前の行の値（mainkey）だから fillna(method='pad') ＞これ同時にできる？
    # concat = pd.concat([merge, sr_title, sr_sku]).fillna(0) # title列、未翻訳＝空白の行を0で埋める。https://deepage.net/features/pandas-manipulate-na.html#%E5%9F%BA%E6%9C%AC%E7%9A%84%E3%81%AA%E4%BD%BF%E3%81%84%E6%96%B9-1
    # 下にして
    global concat
    concat = pd.concat([all_df, sr_sku])
    # 一行のエクセル関数DFを追加、下までフィル
    # global concat2
    # concat2 = pd.concat([concat, main_categ_df]).fillna(method='pad') #'ffill' と同等 # 空白を前の行で埋める https://riptutorial.com/ja/pandas/example/6188/%E4%B8%8D%E8%B6%B3%E3%81%97%E3%81%A6%E3%81%84%E3%82%8B%E5%80%A4%E3%82%92%E5%9F%8B%E3%82%81%E8%BE%BC%E3%82%80

    # ここでID出力。マクロ. Elems の場合は全てのIDを出力せず、追加されたIDを都度都度ファイルへ加えていく
    # このPyで追加したアイテムのIDだけでいい
    # macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt_elem') # 状態列が空白の行から全てのIDをテキストへ
    # macro()
    # shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo_elem.txt',
    #             'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo_elem.txt')
    elems_id_txt = r'C:/Windows/System32/ScrapingTool_Init/sample_codes/zaico-fixcan/db_check_yahoo_elem.txt'
    id_col.to_csv(elems_id_txt,
              header=None, index=None, sep=' ', mode='a') # mBall_elem_zaicoは、追加された分のIDの価格だけでいい

    # time.sleep(10) # 時間置かないと、elems_yahooでTxtファイルがないと言われることがある
    # wb2.save()
    # app.kill()
    #
    # from sample_codes import elems_yahoo4 as elyahoo
    el_csv = r'C:/Users/kazuki_juno/Desktop/00.Myself/04.Buyer/1.利益計算/db_yahoo_elements.csv'
    with open(el_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f:
        # elyahoo.main(f, el_csv, concat2)
        el_main(f, el_csv, elems_id_txt)



import csv # は要らない
def el_main(f, el, txt):
    writer = csv.writer(f)
    with open(txt) as f: #
        page_id_list = [str(row) for row in f]
    # img_list = []
    # id_list = []
    # arr = np.empty([0, 2])
    arr_descon = np.empty([0, 3]) # ここは３列か
    arr_img = np.empty([0, 2])
    arr_pr = np.empty([0, 2])
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
                list = [elems_d, elems_c, page_id_for_scrape]
                writer.writerow(list)
                time.sleep(0.5)
                # img_np = np.array([[page_id_for_scrape], [src_fact]]).T  # transpose()  # elem_img]) # src_list]
                # arr = np.r_[arr, img_np]

            # 価格
            price = soup.select('dl > dd.Price__value')
            price2 = remove_space_htmlTag_pr(str(price))
            # print(price2)
            # pr_list.append(elems_d)
            日件 = soup.select('.Count__number')
            日件2 = remove_space_htmlTag_pr(str(日件))
            # print(日件2)
            if '終了' in 日件2:  # 終了品は elems=価格 を空白に
                # print(日件2)
                price2 = ', '  # 空白のみだと、「, 」で分割する時エラー起きる
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

        list = [elems_d, elems_c, page_id_for_scrape]
        writer.writerow(list)

        dc_np = np.array([[page_id_for_scrape], [elems_d], [elems_c]]).T  # transpose()  # elem_img]) # src_list]
        arr_descon = np.r_[arr_descon, dc_np]
        img_np = np.array([[page_id_for_scrape], [src_fact]]).T  # transpose()  # elem_img]) # src_list]
        arr_img = np.r_[arr_img, img_np]
        pr_np = np.array([[page_id_for_scrape], [price2]]).T  # transpose()  # elem_img]) # src_list]
        arr_pr = np.r_[arr_pr, pr_np]
        time.sleep(1)
        break
# DF化
    # 説明、状態の DF化
    descon_df = pd.DataFrame(arr_descon).iloc[:, :2] # 0. 1行目のみ
    # 画像のDF化
    img_spread(arr_img)
    #  価格のDF化
    pr_df = pd.DataFrame(arr_pr)
    print(pr_df)
    pr_df2 = pd.concat([pr_df, pr_df.iloc[:, 1].str.split(
        ', ', expand=True)], axis=1).iloc[:, [0, 2, 3]]  # drop([1], axis=1)
    pr_df2.column = ['現在価格', '即決価格']
    print(pr_df2)  # 0, 2, 3 列目のみ表示
    pr_csv = 'C:/Users/kazuki_juno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo4.csv'
    pr_df2.to_csv(pr_csv, header=False, index=False)

    concat2 = pd.concat([concat, descon_df, grped, pr_df2])
                         # 説明と状態、画像、価格

    # # sql から追加した分を読み取る？
    # # 価格を含めたDFを、後の現在価格の列を用いて計算するため、
    # sql_df = pd.read_sql()

    # 一行の数式を設定後、設定後の列をdf[]で表し、新たに数式を設定するのでOK か
    # 一度dfにしないといけなくなるから、df[]は要らない
    # 価格系、これはzaico_yahooへ移行
    現在価格 = concat2['現在価格']
    即決価格 = concat2['即決価格']
    # 相場価格 = IF(AX8=0, AV8*3, AX8*1.5) # AX 即決価格、AV= 現在価格 # 両者とも、Zaicoした後にわかること。
    相場価格 =  現在価格* 3 if 即決価格 == 0 else 即決価格* 1.5
    自己設定価格 = 0
    最高販売価格 = 0 if not str(max(相場価格, 自己設定価格)).isnumeric() else max(相場価格, 自己設定価格)
    # もし最大値が数値でないなら 0, 数値なら最大値
    #.isnumeric() # IFERROR(MAX(AD8,Q8,AF8),0) # AD相場価格 Q AF自己認定価格

    最安仕入価格 = min(即決価格) # 以降は、他ECから取得するようになったら　,
                    # 落札相場価格,仕入れ値上限, 価格_r, 価格_a, 価格_m, 価格_o)
                        #AN, AW8,AX8,AY8,AR8,BC8,BF8)
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
    # integrated = if(ounce>0, ounce*0.03, if(pound>0,pound*0.45, if(kg>0,kg)))
    # if ounce > 0:
    #     integrated = ounce * 0.03
    # elif pound > 0:
    #     integrated = pound * 0.45
    # else kg > 0:
    #     integrated = kg
    # integ_col = df['integrated'] # 下記、df[integrated] 省略したい
    送料設定 = "0~0.3kg" if integrated<0.3 else "0.3~0.5kg" if integrated<0.5 else "0.5~0.8kg" if integrated<0.8 else\
        "0.8~1.0kg" if integrated<1 else "1.0~1.5kg" if integrated<1.5 else "1.5~2.0kg" if integrated<2 else\
            "2.0~2.5kg" if integrated<2.5 else "2.5~3.0kg" if integrated<3 else "3.5kg" if integrated<3.5 else\
            "4.0kg" if integrated<4 else "4.5kg" if integrated<4.5 else "5.0kg" if integrated<5 else\
            "5.5kg" if integrated < 5.5 else "6.0kg" if integrated < 6 else "7.0kg" if integrated< 7 else\
            "8.0kg" if integrated < 8 else "9.0kg" if integrated< 9 else '10.0kg以上' # Z = integrated
    # 送料設定_col = df['送料設定']
    送料 = 935 if 送料設定 == "0~0.3kg" else 1235 if 送料設定 == "0.3~0.5kg" else 1685 if 送料設定 == "0.5~0.8kg" else\
        1985 if 送料設定 == "0.8~1.0kg" else 2525 if 送料設定 == "1.0~1.5kg" else 3065 if 送料設定 == "1.5~2.0kg" else 5000
    # 後で 1985 if 送料設定 == "2.0~2.5kg" else 2525 if 送料設定 == "2.5~3.0kg" else 3065 if 送料設定 == "1.5~2.0kg" else\

    最高売値 = 最高販売価格 + 送料 + 仕入送料  # AG8+BL8+BI8
    粗利 = 最高売値 - 最安仕入価格  # AH8-AI8
    出品料 = 0 # なし
    # 最高売値col = df['最高売値']
    落札料 = 最高売値* 0.1
    Paypal = round(最高売値* 0.039, 1)
    支出合計 = sum(送料 + 出品料 + 落札料 + Paypal + 仕入送料)

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

    concat3 = pd.concat([concat2, funcs_df]).fillna(method='pad')
    concat3.to_sql('atklist2', con=engine, if_exists='append',  # or replace
                   index=False)


def img_spread(arr):  # (img_list):
    df = pd.DataFrame(arr)
    df.columns = ['ID', '画像'] # 列名指定 # ここに価格２列を追加
    def f(a): # 単なるGroupBy, apply ではなく、関数 f を組むことで、画像URLを一列に集約するだけでなく、各列に分割までできた  # https://ja.stackoverflow.com/questions/24845/python%E3%81%AEpandas%E3%81%A7-%E7%B8%A6%E6%8C%81%E3%81%A1%E3%81%AE%E3%83%87%E3%83%BC%E3%82%BF%E3%82%92%E6%A8%AA%E6%8C%81%E3%81%A1%E3%81%AB%E3%81%99%E3%82%8B%E3%82%88%E3%81%84%E6%96%B9%E6%B3%95%E3%82%92%E6%95%99%E3%81%88%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84
        a.index = [0 for i in range(len(a))]
        del a['ID'] # 列名指定
        out = a[0:1]
        for i in range(1, len(a)):
            out = out.join(a[i:i + 1], rsuffix='{0}'.format(i))
        return out
    global grped # ここでiloc かける
    grped = df.groupby(df['ID'], sort=False).apply(f).iloc[:, 1:8] # おまけに、列名まで生成されてる!　ここで順を崩さないように
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
    # update_atk(el, grped)
    # mBall_elem_zaicoは、新たに追加されたID分の価格を取得できればいい

# def update_atk(el, grouped):
#     app = xw.App(visible=False)  # 新規アプリ実行環境を作成する
#     wb1 = app.books.open(el)
#     app.books.open("C:/Users/Kazuki Yuno/AppData/Roaming/Microsoft/Excel/XLSTART/PERSONAL.XLSB")
#     # macro = app.macro('PERSONAL.XLSB!elementsfromBS4')
#     # macro()
#     wb1.save()
#
#     atk = r"C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/AtackList_Buyer43.xlsx"
#     wb2 = app.books.open(atk)
#     # af_elems.autofill(atacklist)
#     # def el2at(el, atk, grped):
#         # 説明文、状態、画像、価格2種類、その他利益計算の列全て
#     sht1 = wb1.sheets[0]  # (1)にしていたが
#     sht2 = wb2.sheets[0]
#
#     lastRow1 = sht1.range('C1').end(-4121).row # Aにしていたが、今回のHTTPエラー時は空白ができることで、最下行はID列＝Cで。
#     # nextRow1 = lastRow1 + 1
#     lastRow2 = sht2.range('AZ4').end(-4121).row  # ATK 状態列＝AZの最下行
#     nextRow2 = lastRow2 + 1
#     # 生成したCSVからタイトル、URL, 画像URLをATKへ、最下行の下の行から追加
#     # col_list = ['G','I']
#     # for col in col_list:
#     # 説明と状態
#     desc = sht1.range('A1:A{}'.format(str(lastRow1))).options(ndim=2).value
#     sht2.range('J{}'.format(str(nextRow2))).value = desc
#     condi = sht1.range('B1:B{}'.format(str(lastRow1))).options(ndim=2).value
#     sht2.range('AZ{}'.format(str(nextRow2))).value = condi
#     # col_list = ['R','S','T','U','V']
#     # i = 2 # merge の３列目から
#     # for col, i in zip(col_list, range(2, 7)): # これで、２のときはR, ３のときはS、となる # https://uxmilk.jp/13726
#     # for col, i in zip(range(13, 18), range(2, 7)):
#     # while i < 7:
#
#     # 画像、通常版
#     sht2.range('P{}'.format(nextRow2)).options(
#         pd.DataFrame, expand='table', index=False, header=None).value = grouped.iloc[:, 1:8] # mergeの１－７列目に画像URLがある。8, 9 まであるアイテムも。
    # これまでのアイテムの画像データを一新＞ 4行目から
    # my_values = merge.iloc[:, 1:8]
    # sht2.range('P4').options(
    #     pd.DataFrame, expand='table', index=False, header=None).value = my_values  # index=False

    # el2at(wb1, wb2, grouped)

    # 次のPricesチェック(zaico.py )のため, output ID
    # zaico.py もつなげる ここはzaicoと繋がる必要はない。価格取得だけで良い
    # import された時はfixCancel動かさない、などの設定
    # 全ての行のIDを出力
    #
    # macro = app.macro('PERSONAL.XLSB!OutputActiveID_Txt')
    # macro()
    # shutil.move('C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo3.txt',
    #             'C:/Windows/System32/ScrapingTool_Init/sample_codes/db_check_yahoo3.txt')
    # wb2.save() # 読み取り専用の状態だと、保存できずエラーで終わる
    # wb1.close()
    # wb2.close()
    # app.kill()

    # 仕入先をスクレイプするごとに価格チェックすることになるから、ここは繋げない。最後に一括で価格やればいい

    # from sample_codes import zaico_yahoo as zyahoo  # if name == main は、
    # pr_csv = 'C:/Users/Kazuki Yuno/Desktop/00.Myself/04.Buyer/1.利益計算/db_check_yahoo4.csv'
    # with open(pr_csv, 'w', encoding='utf-8-sig', newline='', errors='ignore') as f2:
    #     zyahoo.main(f2, pr_csv)
    #     # pr_main(f2, pr_csv)

def remove_space_htmlTag(s):
    p = re.compile(r"<[^>]*?>") # htmlTagを削除
    remove = p.sub("", s)
    space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    return space.replace('[', '').replace(']', '') # [] を置換

def remove_space_htmlTag_pr(s):
    p = re.compile(r"<[^>]*?>") # htmlTagを削除
    remove = p.sub("", s)
    space = re.sub(r'\s+', ' ', remove).strip()  # 連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
    return space.replace('[', '').replace(']', '').replace('円（税 0 円） ', '')


 # mergeのURL列から、新たにitemID 列を導き出す
def extract_key(url): # URLからキー（URLの末尾のISBN）を抜き出す。
    m = re.search(r'/([^/]+)$', url) # /([^/]+)$
    return m.group(1)


# def normalize_spaces(s):
#     """
#     連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する。
#     """
#     return re.sub(r'\s+', ' ', s).strip()
#

# def check_if_Excel_runs():
    # try:
    #     win32com.client.GetActiveObject("Excel.Application")
    #     # If there is NO error at this stage, Excel is already running
    #     print('Excel is running, please close first')
    #     xw.Book.close() # 全てのブックを消去
    #     xw.App.kill()
    #     sys.exit() # これは
    # except:
    #     print('Excel is NOT running, this is good!')
    # return


if __name__ == '__main__':
    main()



