# -*- coding: utf-8 -*-
"""
フォーメーションごとのデフォルト攻撃位置・守備位置の定義（Aチーム基準。row1=自陣, row=ROWSが敵陣）
Bチームはmirrorで自動生成（row反転）。

コート仕様: 縦105マス x 横65マス (1マス=1m)。
旧仕様(縦20x横15マス)で調整済みだった配置バランスを崩さないよう、
旧グリッド座標を ROW_SCALE / COL_SCALE で新グリッドへ比例変換して定義している
（横方向は中央列(CENTER_COL)基準のオフセットを変換することで、
 左右対称性とゴールエリア中央(ball_logic.CENTER_COLと同じ33列目)を厳密に一致させている）。

【フォーメーション対応】
FORMATION_TABLES に "442"(4-4-2), "433"(4-3-3), "352"(3-5-2) のキーで、フォーメーションごとの
- attack  : 自チームがボール保持時の基準ポジション
- defense : 相手がボール保持時の基準ポジション
- line_follow: ボールrowへの追随係数
- col_pull: ボールcolへの引き寄せ係数
- line_height_sensitivity: 戦術のline_heightに対する感度
を保持する。tactics.py の各プリセットが "formation" キーでどちらを使うか指定し、
engine.py が dynamic_target() 呼び出し時に該当フォーメーションを渡す。

新しいフォーメーションを追加する場合は、ポジションキーの先頭を必ず "DF_" / "MF_" / "FW_" / "GK"
のいずれかにすること(ball_logic.py側のstartswith判定・サイド判定が前提としている)。

【チーム戦術(tactic)による基準ポジションの補正】
tactics.py で定義する4軸のうち、line_height（守備ラインの高さ）とwidth（横の広がり）は
このモジュールの get_default() で基準ポジションに反映する。
pass_risk / press_intensity は ball_logic.py 側で使用する。
"""

# ---- 新グリッド仕様 ----
ROWS, COLS = 105, 65
CENTER_COL = (COLS + 1) // 2  # 33（ball_logic.CENTER_COLと一致させること）

# ---- 旧グリッド(20x15)からの変換用パラメータ ----
_OLD_ROWS, _OLD_COLS = 20, 15
_OLD_CENTER_COL = (_OLD_COLS + 1) // 2  # 8
ROW_SCALE = ROWS / _OLD_ROWS      # 5.25
COL_SCALE = COLS / _OLD_COLS      # 4.333...


def scale_old_pos(pos):
    """旧グリッド(20x15)座標を新グリッド(105x65)座標へ、中央列基準で比例変換する"""
    r, c = pos
    new_r = round(r * ROW_SCALE)
    new_c = CENTER_COL + round((c - _OLD_CENTER_COL) * COL_SCALE)
    new_r = max(1, min(ROWS, new_r))
    new_c = max(1, min(COLS, new_c))
    return (new_r, new_c)


def mirror_pos(pos, rows=ROWS):
    r, c = pos
    return (rows + 1 - r, c)


# ============================================================
# 4-4-2 (旧グリッド座標で定義し、新グリッドへ変換する)
# ============================================================
_OLD_ATTACK_442 = {
    "GK":     (2, 8),
    "DF_LB":  (6, 3),  "DF_CB1": (6, 7),  "DF_CB2": (6, 9),  "DF_RB": (6, 13),
    "MF_LM":  (11, 3), "MF_CM1": (11, 7), "MF_CM2": (11, 9), "MF_RM": (11, 13),
    "FW1":    (15, 7), "FW2":    (15, 9),
}

_OLD_DEFENSE_442 = {
    "GK":     (2, 8),
    "DF_LB":  (5, 3),  "DF_CB1": (5, 7),  "DF_CB2": (5, 9),  "DF_RB": (5, 13),
    "MF_LM":  (9, 3),  "MF_CM1": (9, 7),  "MF_CM2": (9, 9),  "MF_RM": (9, 13),
    "FW1":    (11, 7), "FW2":    (11, 9),
}

LINE_FOLLOW_442 = {
    "GK": 0.05,
    "DF_LB": 0.25, "DF_CB1": 0.25, "DF_CB2": 0.25, "DF_RB": 0.25,
    "MF_LM": 0.4, "MF_CM1": 0.4, "MF_CM2": 0.4, "MF_RM": 0.4,
    "FW1": 0.3, "FW2": 0.3,
}

COL_PULL_442 = {
    "GK": 0.1,
    "DF_LB": 0.3, "DF_CB1": 0.2, "DF_CB2": 0.2, "DF_RB": 0.3,
    "MF_LM": 0.4, "MF_CM1": 0.3, "MF_CM2": 0.3, "MF_RM": 0.4,
    "FW1": 0.3, "FW2": 0.3,
}

LINE_HEIGHT_SENS_442 = {
    "GK": 0.1,
    "DF_LB": 1.0, "DF_CB1": 1.0, "DF_CB2": 1.0, "DF_RB": 1.0,
    "MF_LM": 0.6, "MF_CM1": 0.6, "MF_CM2": 0.6, "MF_RM": 0.6,
    "FW1": 0.3, "FW2": 0.3,
}

# ============================================================
# 4-3-3 (旧グリッド座標で定義し、新グリッドへ変換する)
# DF4枚は4-4-2と共通。中盤はアンカー(MF_DM)+インサイドハーフ2枚、
# 前線はワイドな両ウイング(FW_LW/FW_RW)+中央FW1の3トップ。
# ============================================================
_OLD_ATTACK_433 = {
    "GK":     (2, 8),
    "DF_LB":  (6, 3),  "DF_CB1": (6, 7),  "DF_CB2": (6, 9),  "DF_RB": (6, 13),
    "MF_DM":  (10, 8), "MF_CM1": (12, 6), "MF_CM2": (12, 10),
    "FW_LW":  (15, 3), "FW1":    (16, 8), "FW_RW":  (15, 13),
}

_OLD_DEFENSE_433 = {
    "GK":     (2, 8),
    "DF_LB":  (5, 3), "DF_CB1": (5, 7), "DF_CB2": (5, 9), "DF_RB": (5, 13),
    "MF_DM":  (8, 8), "MF_CM1": (9, 6), "MF_CM2": (9, 10),
    "FW_LW":  (11, 4), "FW1":   (11, 8), "FW_RW":  (11, 13),
}

LINE_FOLLOW_433 = {
    "GK": 0.05,
    "DF_LB": 0.25, "DF_CB1": 0.25, "DF_CB2": 0.25, "DF_RB": 0.25,
    "MF_DM": 0.3, "MF_CM1": 0.4, "MF_CM2": 0.4,
    "FW_LW": 0.3, "FW1": 0.3, "FW_RW": 0.3,
}

COL_PULL_433 = {
    "GK": 0.1,
    "DF_LB": 0.3, "DF_CB1": 0.2, "DF_CB2": 0.2, "DF_RB": 0.3,
    "MF_DM": 0.25, "MF_CM1": 0.3, "MF_CM2": 0.3,
    "FW_LW": 0.35, "FW1": 0.3, "FW_RW": 0.35,
}

LINE_HEIGHT_SENS_433 = {
    "GK": 0.1,
    "DF_LB": 1.0, "DF_CB1": 1.0, "DF_CB2": 1.0, "DF_RB": 1.0,
    "MF_DM": 0.5, "MF_CM1": 0.6, "MF_CM2": 0.6,
    "FW_LW": 0.3, "FW1": 0.3, "FW_RW": 0.3,
}

# ============================================================
# 3-5-2 (旧グリッド座標で定義し、新グリッドへ変換する)
# 3バック(DF_CB1〜3)+両ウイングバック(MF_LWB/RWB)+アンカー(MF_DM)+
# インサイドハーフ2枚(MF_CM1/CM2)の中盤5枚+2トップ(FW1/FW2)。
# ウイングバックは守備時は5バック的に絞り、攻撃時は大きく高い位置まで駆け上がる
# (LINE_HEIGHT_SENSITIVITYを高めに設定し、ハイラインとの連動を強くしている)。
# ============================================================
_OLD_ATTACK_352 = {
    "GK":     (2, 8),
    "DF_CB1": (6, 6),  "DF_CB2": (6, 8),  "DF_CB3": (6, 10),
    "MF_LWB": (10, 2), "MF_RWB": (10, 14),
    "MF_DM":  (10, 8), "MF_CM1": (12, 6), "MF_CM2": (12, 10),
    # FW1/FW2は中央寄りに配置(4-4-2のFW1/FW2と同じ間隔=col7,9)。
    # 以前はcol6,10(中央±2)にしていたが、これだと新グリッド換算後にゴールエリア(中央±3列)から
    # 大きく外れた位置からシュートすることが多くなり、シュートの8割以上が枠外になる不具合があった。
    "FW1":    (15, 7), "FW2":    (15, 9),
}

_OLD_DEFENSE_352 = {
    "GK":     (2, 8),
    "DF_CB1": (5, 6), "DF_CB2": (5, 8), "DF_CB3": (5, 10),
    "MF_LWB": (7, 3), "MF_RWB": (7, 13),
    "MF_DM":  (8, 8), "MF_CM1": (9, 6), "MF_CM2": (9, 10),
    "FW1":    (11, 7), "FW2":   (11, 9),
}

LINE_FOLLOW_352 = {
    "GK": 0.05,
    "DF_CB1": 0.25, "DF_CB2": 0.25, "DF_CB3": 0.25,
    "MF_LWB": 0.35, "MF_RWB": 0.35,
    "MF_DM": 0.3, "MF_CM1": 0.4, "MF_CM2": 0.4,
    "FW1": 0.3, "FW2": 0.3,
}

COL_PULL_352 = {
    "GK": 0.1,
    "DF_CB1": 0.2, "DF_CB2": 0.2, "DF_CB3": 0.2,
    "MF_LWB": 0.3, "MF_RWB": 0.3,
    "MF_DM": 0.25, "MF_CM1": 0.3, "MF_CM2": 0.3,
    "FW1": 0.3, "FW2": 0.3,
}

LINE_HEIGHT_SENS_352 = {
    "GK": 0.1,
    "DF_CB1": 1.0, "DF_CB2": 1.0, "DF_CB3": 1.0,
    # ウイングバックの感度は低めにしている。感度を高くすると、リトリート堅守(line_height=-8)の
    # ような低いラインの戦術と組み合わせたときに攻撃時も深く引き戻されすぎてしまい、
    # サイドを駆け上がってクロスを供給する役割を全く果たせなくなる不具合があった。
    # ライン高さより「攻撃/守備フェーズ」と「ボール追随」で位置を決める比重を大きくしている。
    "MF_LWB": 0.35, "MF_RWB": 0.35,
    "MF_DM": 0.5, "MF_CM1": 0.6, "MF_CM2": 0.6,
    "FW1": 0.3, "FW2": 0.3,
}

FORMATION_TABLES = {
    "442": {
        "attack": {k: scale_old_pos(v) for k, v in _OLD_ATTACK_442.items()},
        "defense": {k: scale_old_pos(v) for k, v in _OLD_DEFENSE_442.items()},
        "line_follow": LINE_FOLLOW_442,
        "col_pull": COL_PULL_442,
        "line_height_sensitivity": LINE_HEIGHT_SENS_442,
    },
    "433": {
        "attack": {k: scale_old_pos(v) for k, v in _OLD_ATTACK_433.items()},
        "defense": {k: scale_old_pos(v) for k, v in _OLD_DEFENSE_433.items()},
        "line_follow": LINE_FOLLOW_433,
        "col_pull": COL_PULL_433,
        "line_height_sensitivity": LINE_HEIGHT_SENS_433,
    },
    "352": {
        "attack": {k: scale_old_pos(v) for k, v in _OLD_ATTACK_352.items()},
        "defense": {k: scale_old_pos(v) for k, v in _OLD_DEFENSE_352.items()},
        "line_follow": LINE_FOLLOW_352,
        "col_pull": COL_PULL_352,
        "line_height_sensitivity": LINE_HEIGHT_SENS_352,
    },
}


# 偽9番(false nine): 攻撃時にFW1が中盤へ降り、代わりにMF_CM1が前線へ飛び出す
# ポジション流動化。相手CBに「ついていくか持ち場を守るか」の判断を強いる
# デゼルビ/グアルディオラ系の代名詞的な仕組み。tactics.pyの"false_nine"フラグで有効化。
FALSE_NINE_DROP = 14   # FW1が降りる距離(m)
FALSE_NINE_PUSH = 12   # 入れ替わりにMF_CM1が前線へ出る距離(m)

# サイドバックの役割(fb_role): "overlap"=高い位置に張り出して相手を引っ張る(アウベス型)、
# "inverted"=内側(ハーフスペース)へ絞ってビルドアップに参加する(偽SB)、"normal"=補正なし。
# 攻撃時のDF_LB/DF_RBにのみ適用(3-5-2のウイングバックは元々役割が定義済みのため対象外)。
FB_OVERLAP_PUSH_ROW = 15   # overlap時に押し上げる距離(m)
FB_OVERLAP_PUSH_COL = 8    # overlap時にさらに外へ張り出す距離(m)
FB_INVERT_PUSH_ROW = 6     # inverted時にやや前へ出る距離(m)
FB_INVERT_HALFSPACE_COL = 12  # inverted時の中央からの距離(ハーフスペース帯の中央)


def get_default(pos_key, phase, team, tactic=None, formation="442"):
    """phase: 'attack' or 'defense'. team: 'A' or 'B'.
    tactic: tactics.py のプリセットdict（Noneなら補正なし＝中立）。
    formation: FORMATION_TABLESのキー("442"/"433"/"352")。
    """
    table = FORMATION_TABLES[formation]["attack" if phase == "attack" else "defense"]
    base_r, base_c = table[pos_key]

    # ---- 攻撃時のポジション流動化(A基準座標のまま補正し、その後ミラーする) ----
    if tactic and phase == "attack":
        if tactic.get("false_nine"):
            if pos_key == "FW1":
                base_r -= FALSE_NINE_DROP    # 偽9番: 中盤へ降りる
            elif pos_key == "MF_CM1":
                base_r += FALSE_NINE_PUSH    # 入れ替わりで前線へ飛び出す
        fb_role = tactic.get("fb_role", "normal")
        if pos_key in ("DF_LB", "DF_RB") and fb_role != "normal":
            if fb_role == "overlap":
                base_r += FB_OVERLAP_PUSH_ROW
                base_c += FB_OVERLAP_PUSH_COL if pos_key == "DF_RB" else -FB_OVERLAP_PUSH_COL
            elif fb_role == "inverted":
                base_r += FB_INVERT_PUSH_ROW
                base_c = CENTER_COL + (FB_INVERT_HALFSPACE_COL if pos_key == "DF_RB"
                                       else -FB_INVERT_HALFSPACE_COL)

    attack_dir = 1 if team == "A" else -1
    if team == "B":
        base_r, base_c = mirror_pos((base_r, base_c))

    line_height = tactic["line_height"] if tactic else 0.0
    width = tactic["width"] if tactic else 1.0
    sensitivity = FORMATION_TABLES[formation]["line_height_sensitivity"][pos_key]

    row = base_r + attack_dir * line_height * sensitivity
    col = CENTER_COL + (base_c - CENTER_COL) * width

    row = max(1, min(ROWS, round(row)))
    col = max(1, min(COLS, round(col)))
    return (row, col)


def dynamic_target(pos_key, team, phase, ball_pos, tactic=None, formation="442"):
    """デフォルト位置(戦術補正込み) + ボール位置への追随オフセットを加味した目標マスを返す"""
    base_r, base_c = get_default(pos_key, phase, team, tactic, formation)
    br, bc = ball_pos
    line_f = FORMATION_TABLES[formation]["line_follow"][pos_key]
    col_f = FORMATION_TABLES[formation]["col_pull"][pos_key]

    row_target = base_r + (br - base_r) * line_f
    col_target = base_c + (bc - base_c) * col_f

    row_target = max(1, min(ROWS, round(row_target)))
    col_target = max(1, min(COLS, round(col_target)))
    return (row_target, col_target)
