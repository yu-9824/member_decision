import random

import pandas as pd
import os

import datetime
from icalendar import Calendar, Event
import pytz


def main(random_state = None, debug = False, path_input = None, dir_output = None):
    # ランダム要素のseed値を設定
    random.seed(random_state)

    # ファイル名の取得
    if debug:
        path_dir = os.path.join(os.path.dirname(__file__), 'example')
        fnames = [fname for fname in os.listdir(path_dir) if '予定表' in fname]
        path_input = os.path.join(path_dir, fnames[0])
    else:
        path_input = input('input file path = ') if path_input is None else path_input
    fname = os.path.basename(path_input)
    key = ' - '
    yyyymm = fname[fname.find(key)+len(key):fname.find(' 予定表')]

    # ダウンロードしたcsvファイルから読み込む
    df_input = pd.read_csv(path_input, header = 1)

    # 二つの表の区切り目を取得
    index_Unnamed = [i for i, col in enumerate(df_input.columns) if 'Unnamed: ' in col]

    # 二つの表に分ける
    df_kagisime_input = df_input.iloc[:, index_Unnamed[0]+1:index_Unnamed[1]]
    df_gomisute_input = df_input.iloc[:, index_Unnamed[1]+1:index_Unnamed[2] if len(index_Unnamed) > 2 else None]

    # カラム名を整頓
    df_gomisute_input.columns = map(lambda x:x.replace('.1', ''), df_gomisute_input.columns)

    # メンバーリストとDataFrameを取得
    members = []
    dfs = []
    for args in [[df_kagisime_input, 2, '鍵閉め'], [df_gomisute_input, 4, 'ゴミ捨て']]:
        pm = params(*args)
        members.append(pm.members)
        dfs.append(get_decided_member(**pm.kwargs))
    df_kagisime_output, df_gomisute_output = dfs

    # outputするフォルダを指定
    if debug:
        dir_output = path_dir
    else:
        dir_output = input('output directory path = ') if dir_output is None else dir_output

    # 出力用ファイルの作成，出力
    df_output = pd.concat([df_kagisime_output, df_gomisute_output], axis = 1)
    df_output.to_csv(os.path.join(dir_output, yyyymm + ' 配置.csv'), encoding = 'utf_8_sig')

    # .icsファイルを各メンバーごとに作成
    {make_ical(df_output, dir_output, yyyymm, member) for member in members[1]} # ゴミ捨てに登録されている全員のicsファイルを作成

def make_ical(df, dir_output, filename, member):
    # カレンダーオブジェクトの生成
    cal = Calendar()

    # カレンダーに必須の項目
    cal.add('prodid', 'yu-9824')
    cal.add('version', '2.0')

    # タイムゾーン
    tokyo = pytz.timezone('Asia/Tokyo')

    for name, series in df.iteritems():
        series_ = series[series.str.contains(member)]
        if name == '鍵閉め':
            start_td = datetime.timedelta(hours = 17, minutes = 45)   # 17時間45分
        elif name == 'ゴミ捨て':
            start_td = datetime.timedelta(hours = 14)   # 14時間
        else:
            continue
        need_td = datetime.timedelta(hours = 1)

        for date, cell in zip(series_.index, series_):
            # 予定の開始時間と終了時間を変数として得る．
            start_time = datetime.datetime.strptime(date, '%Y/%m/%d') + start_td
            end_time = start_time + need_td

            # Eventオブジェクトの生成
            event = Event()

            # 必要情報
            event.add('summary', name)  # 予定名
            event.add('dtstart', tokyo.localize(start_time))
            event.add('dtend', tokyo.localize(end_time))
            event.add('description', cell)  # 誰とやるかを説明欄に記述
            event.add('created', tokyo.localize(datetime.datetime.now()))    # いつ作ったのか．

            # カレンダーに追加
            cal.add_component(event)

    # カレンダーのファイルへの書き出し
    with open(os.path.join(dir_output, filename + member + '.ics'), mode = 'wb') as f:
        f.write(cal.to_ical())


def get_decided_member(members, days, active_days, need, NG, label):
    # よく使うので変数として定義
    n_members = len(members)
    n_active = len(active_days)

    # 何日担当するかのリスト（人は決まっていない）
    lst_how_many = [(n_active * need + n) // n_members for n in range(n_members)]

    # 何日担当するかのリスト（人も決定）
    dict_how_many = dict(zip(members, random.sample(lst_how_many, n_members)))

    while True:
        # 候補日程の生成
        arange = [day for day in active_days] * need
        decided_members = {day:[] for day in days}

        # mem: メンバー名， n: そのメンバーが担当する回数
        for mem, n in dict_how_many.items():
            # setで集合にする際にrandom要素が発生してしまい，random.seedを指定しても意味がなくなってしまうため，sortedする．
            cand_days = sorted([day for day in set(arange) if day not in NG[mem]])
            
            # 選ばなきゃいけない日数と同じかそれより多く候補日程が残っていることを確認
            if len(cand_days) >= n:
                sampled = set(random.sample(cand_days, n))
            else:
                break   # while Trueからやり直し．

            # きちんとn個選べているならば
            if n == len(sampled):
                for day in sampled:
                    arange.remove(day)
                    decided_members[day].append(mem)
            else:
                break   # for mem, n in d.items()をbreak
        else:
            break   # while Trueをbreak (正常終了)

    decided_members = {k:[', '.join(v)] if len(v) != 0 else [''] for k, v in decided_members.items()}

    # 名前の入ったリスト→文字列， 名前の入っていないリスト = not active day = 'x'と書き入れる
    df_decided_members = pd.DataFrame.from_dict(decided_members, orient = 'index', columns = [label])
    print(df_decided_members)
    return df_decided_members




class params:
    def __init__(self, df, need, label):
        # 入力された変数をクラス変数化
        self.df = df
        self.need = need

        # 日付をkeyに．
        self.df.set_index('日付', inplace = True)

        # 曜日は今のところ不要なので取り除く．
        self.df.drop('曜日', axis = 1, inplace = True)

        # メンバーのリストを取得
        self.members = list(self.df.columns)

        # 予定がない→空白に変更
        self.df.fillna('', inplace = True)

        # 全員が予定がある or 休日 or 遂行人数を確保できない場合がFalseになるbooleanを得る
        self.not_active_boolean = (self.df != '').sum(axis = 1) + self.need > len(self.members)
        self.active_boolean = ~self.not_active_boolean

        # それをやらなきゃいけないdf (~はbooleanを反転させる．)
        self.df_active = self.df[self.active_boolean]
        self.active_days_number = len(self.df_active)   # やらなきゃいけない日数

        # activeな日
        self.active_days = list(self.df_active.index)

        self.NG = {mem:list(self.df_active.query(mem + ' != ""').index) for mem in self.members}

        # get_decided_member（）に与える変数全てを含んだ辞書を返す．
        self.kwargs = {'members' : self.members, 'active_days' : self.active_days, 'need' : self.need, 'NG' : self.NG, 'days' : list(self.df.index), 'label': label}





if __name__ == '__main__':
    # デバッグ用
    from pdb import set_trace

    main(random_state = None, debug = True)
