# -*- coding: utf-8 -*-
"""
選手データ定義
- 各チーム11人、能力合計1000点
- 5項目: kick(キック力), speed(スピード), accuracy(正確性), vision(視野), tactic(戦術理解)
  各選手の「総合力(overall)」をポジション別に配分し、そこからポジション別の重み(WEIGHTS)を
  かけて5項目のサブスコアを算出する。各項目は総合力にだいたい比例する設計。

【フォーメーション対応】
FORMATIONS に "442"(4-4-2), "433"(4-3-3), "352"(3-5-2) のキーで、フォーメーションごとの
ポジション一覧・能力配分(合計1000点)・重み・背番号・キックオフ配置を保持する。
build_team(team_label, formation_key) で該当フォーメーションの選手一式を生成する。

キックオフ配置は、formation.pyのATTACK_DEFAULT(攻撃時の展開済み基準位置)より
コンパクトな「キックオフ時の待機隊形」を旧グリッド座標で個別に定義し、
formation.scale_old_pos()で新グリッド(105x65)へ変換している。

新しいフォーメーションを追加する場合、ポジションキーの先頭は必ず "DF_" / "MF_" / "FW_" / "GK"
のいずれかにすること(ball_logic.py側のstartswith判定・サイド判定が前提としている)。
背番号10は両チームともキックオフ時のボール保持者(中央のFW)に割り当てること(engine.py側の前提)。
"""
from formation import scale_old_pos, mirror_pos, ROWS as PITCH_ROWS

# ============================================================
# 4-4-2
# ============================================================
POSITIONS_442 = [
    "GK",
    "DF_LB", "DF_CB1", "DF_CB2", "DF_RB",
    "MF_LM", "MF_CM1", "MF_CM2", "MF_RM",
    "FW1", "FW2",
]

BASE_OVERALL_442 = {
    "GK": 70,
    "DF_LB": 88, "DF_CB1": 92, "DF_CB2": 92, "DF_RB": 88,
    "MF_LM": 90, "MF_CM1": 98, "MF_CM2": 98, "MF_RM": 90,
    "FW1": 102, "FW2": 92,
}
assert sum(BASE_OVERALL_442.values()) == 1000, sum(BASE_OVERALL_442.values())

WEIGHTS_442 = {
    "GK":     {"kick": 0.8, "speed": 0.8, "accuracy": 1.3, "vision": 1.1, "tactic": 1.0},
    "DF_LB":  {"kick": 0.9, "speed": 1.1, "accuracy": 1.0, "vision": 1.0, "tactic": 1.0},
    "DF_CB1": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    "DF_CB2": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    "DF_RB":  {"kick": 0.9, "speed": 1.1, "accuracy": 1.0, "vision": 1.0, "tactic": 1.0},
    "MF_LM":  {"kick": 1.0, "speed": 1.1, "accuracy": 1.0, "vision": 1.1, "tactic": 0.8},
    "MF_CM1": {"kick": 1.0, "speed": 0.9, "accuracy": 1.1, "vision": 1.2, "tactic": 0.8},
    "MF_CM2": {"kick": 1.0, "speed": 0.9, "accuracy": 1.1, "vision": 1.2, "tactic": 0.8},
    "MF_RM":  {"kick": 1.0, "speed": 1.1, "accuracy": 1.0, "vision": 1.1, "tactic": 0.8},
    "FW1":    {"kick": 1.3, "speed": 1.2, "accuracy": 0.9, "vision": 0.8, "tactic": 0.8},
    "FW2":    {"kick": 1.3, "speed": 1.2, "accuracy": 0.9, "vision": 0.8, "tactic": 0.8},
}

NUMBER_MAP_442 = {
    "GK": 1,
    "DF_LB": 2, "DF_CB1": 3, "DF_CB2": 4, "DF_RB": 5,
    "MF_LM": 6, "MF_CM1": 7, "MF_CM2": 8, "MF_RM": 9,
    "FW1": 10, "FW2": 11,
}

# キックオフ時の待機隊形（旧グリッド20x15基準の座標）
_OLD_A_INIT_POS_442 = {
    "GK": (2, 8),
    "DF_LB": (5, 3), "DF_CB1": (5, 7), "DF_CB2": (5, 9), "DF_RB": (5, 13),
    "MF_LM": (9, 3), "MF_CM1": (9, 7), "MF_CM2": (9, 9), "MF_RM": (9, 13),
    "FW1": (10, 7), "FW2": (10, 9),  # キックオフでFW1(背番号10)がボール保持
}

# ============================================================
# 4-3-3
# DF4枚はそのまま流用。中盤はアンカー(MF_DM)+インサイドハーフ2枚(MF_CM1/CM2)、
# 前線はワイドな両ウイング(FW_LW/FW_RW)+中央FW1の3トップ。
# ============================================================
POSITIONS_433 = [
    "GK",
    "DF_LB", "DF_CB1", "DF_CB2", "DF_RB",
    "MF_DM", "MF_CM1", "MF_CM2",
    "FW_LW", "FW1", "FW_RW",
]

BASE_OVERALL_433 = {
    "GK": 70,
    "DF_LB": 88, "DF_CB1": 92, "DF_CB2": 92, "DF_RB": 88,
    "MF_DM": 100, "MF_CM1": 110, "MF_CM2": 110,
    "FW_LW": 80, "FW1": 90, "FW_RW": 80,
}
assert sum(BASE_OVERALL_433.values()) == 1000, sum(BASE_OVERALL_433.values())

WEIGHTS_433 = {
    "GK":     {"kick": 0.8, "speed": 0.8, "accuracy": 1.3, "vision": 1.1, "tactic": 1.0},
    "DF_LB":  {"kick": 0.9, "speed": 1.1, "accuracy": 1.0, "vision": 1.0, "tactic": 1.0},
    "DF_CB1": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    "DF_CB2": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    "DF_RB":  {"kick": 0.9, "speed": 1.1, "accuracy": 1.0, "vision": 1.0, "tactic": 1.0},
    # アンカー: キック・スピードは控えめ、視野・戦術理解が高い守備的MF
    "MF_DM":  {"kick": 0.9, "speed": 0.9, "accuracy": 1.0, "vision": 1.1, "tactic": 1.3},
    "MF_CM1": {"kick": 1.0, "speed": 0.9, "accuracy": 1.1, "vision": 1.2, "tactic": 0.8},
    "MF_CM2": {"kick": 1.0, "speed": 0.9, "accuracy": 1.1, "vision": 1.2, "tactic": 0.8},
    # ウイング: スピード・キック力重視、視野もクロスのため一定水準
    "FW_LW":  {"kick": 1.1, "speed": 1.3, "accuracy": 0.9, "vision": 1.0, "tactic": 0.7},
    "FW1":    {"kick": 1.3, "speed": 1.2, "accuracy": 0.9, "vision": 0.8, "tactic": 0.8},
    "FW_RW":  {"kick": 1.1, "speed": 1.3, "accuracy": 0.9, "vision": 1.0, "tactic": 0.7},
}

NUMBER_MAP_433 = {
    "GK": 1,
    "DF_LB": 2, "DF_CB1": 3, "DF_CB2": 4, "DF_RB": 5,
    "MF_DM": 6, "MF_CM1": 7, "MF_CM2": 8,
    "FW_LW": 9, "FW1": 10, "FW_RW": 11,
}

_OLD_A_INIT_POS_433 = {
    "GK": (2, 8),
    "DF_LB": (5, 3), "DF_CB1": (5, 7), "DF_CB2": (5, 9), "DF_RB": (5, 13),
    "MF_DM": (8, 8), "MF_CM1": (9, 6), "MF_CM2": (9, 10),
    "FW_LW": (10, 4), "FW1": (10, 8), "FW_RW": (10, 12),  # キックオフでFW1(背番号10)がボール保持
}

# ============================================================
# 3-5-2
# 3バック(DF_CB1〜3)+両ウイングバック(MF_LWB/RWB)+アンカー(MF_DM)+
# インサイドハーフ2枚(MF_CM1/CM2)の中盤5枚+2トップ(FW1/FW2)。
# ============================================================
POSITIONS_352 = [
    "GK",
    "DF_CB1", "DF_CB2", "DF_CB3",
    "MF_LWB", "MF_RWB", "MF_DM", "MF_CM1", "MF_CM2",
    "FW1", "FW2",
]

BASE_OVERALL_352 = {
    "GK": 70,
    "DF_CB1": 95, "DF_CB2": 95, "DF_CB3": 95,
    "MF_LWB": 85, "MF_RWB": 85, "MF_DM": 95, "MF_CM1": 100, "MF_CM2": 100,
    "FW1": 90, "FW2": 90,
}
assert sum(BASE_OVERALL_352.values()) == 1000, sum(BASE_OVERALL_352.values())

WEIGHTS_352 = {
    "GK":     {"kick": 0.8, "speed": 0.8, "accuracy": 1.3, "vision": 1.1, "tactic": 1.0},
    # 3バックのCB: ビルドアップの起点になるため視野・戦術理解も一定水準
    "DF_CB1": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    "DF_CB2": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    "DF_CB3": {"kick": 0.9, "speed": 0.8, "accuracy": 1.1, "vision": 1.0, "tactic": 1.2},
    # ウイングバック: サイドを1人で往復するためスピード重視
    "MF_LWB": {"kick": 1.0, "speed": 1.3, "accuracy": 0.9, "vision": 1.0, "tactic": 0.8},
    "MF_RWB": {"kick": 1.0, "speed": 1.3, "accuracy": 0.9, "vision": 1.0, "tactic": 0.8},
    # アンカー: キック・スピードは控えめ、視野・戦術理解が高い守備的MF
    "MF_DM":  {"kick": 0.9, "speed": 0.9, "accuracy": 1.0, "vision": 1.1, "tactic": 1.3},
    "MF_CM1": {"kick": 1.0, "speed": 0.9, "accuracy": 1.1, "vision": 1.2, "tactic": 0.8},
    "MF_CM2": {"kick": 1.0, "speed": 0.9, "accuracy": 1.1, "vision": 1.2, "tactic": 0.8},
    "FW1":    {"kick": 1.3, "speed": 1.2, "accuracy": 0.9, "vision": 0.8, "tactic": 0.8},
    "FW2":    {"kick": 1.3, "speed": 1.2, "accuracy": 0.9, "vision": 0.8, "tactic": 0.8},
}

NUMBER_MAP_352 = {
    "GK": 1,
    "DF_CB1": 2, "DF_CB2": 3, "DF_CB3": 4,
    "MF_LWB": 5, "MF_RWB": 6, "MF_DM": 7, "MF_CM1": 8, "MF_CM2": 9,
    "FW1": 10, "FW2": 11,
}

_OLD_A_INIT_POS_352 = {
    "GK": (2, 8),
    "DF_CB1": (5, 6), "DF_CB2": (5, 8), "DF_CB3": (5, 10),
    "MF_LWB": (7, 3), "MF_RWB": (7, 13),
    "MF_DM": (8, 8), "MF_CM1": (9, 6), "MF_CM2": (9, 10),
    "FW1": (10, 7), "FW2": (10, 9),  # キックオフでFW1(背番号10)がボール保持
}

FORMATIONS = {
    "442": {
        "positions": POSITIONS_442,
        "base_overall": BASE_OVERALL_442,
        "weights": WEIGHTS_442,
        "number_map": NUMBER_MAP_442,
        "old_init_pos": _OLD_A_INIT_POS_442,
    },
    "433": {
        "positions": POSITIONS_433,
        "base_overall": BASE_OVERALL_433,
        "weights": WEIGHTS_433,
        "number_map": NUMBER_MAP_433,
        "old_init_pos": _OLD_A_INIT_POS_433,
    },
    "352": {
        "positions": POSITIONS_352,
        "base_overall": BASE_OVERALL_352,
        "weights": WEIGHTS_352,
        "number_map": NUMBER_MAP_352,
        "old_init_pos": _OLD_A_INIT_POS_352,
    },
}


def get_init_positions(formation_key, team_label):
    f = FORMATIONS[formation_key]
    a_pos = {k: scale_old_pos(v) for k, v in f["old_init_pos"].items()}
    if team_label == "A":
        return a_pos
    return {k: mirror_pos(v, rows=PITCH_ROWS) for k, v in a_pos.items()}


def build_team(team_label, formation_key):
    f = FORMATIONS[formation_key]
    init_pos = get_init_positions(formation_key, team_label)
    players = {}
    for pos_key in f["positions"]:
        overall = f["base_overall"][pos_key]
        w = f["weights"][pos_key]
        avg_w = sum(w.values()) / 5.0
        stats = {item: round(overall * (val / avg_w) / 5, 1) for item, val in w.items()}
        num = f["number_map"][pos_key]
        players[num] = {
            "team": team_label,
            "number": num,
            "pos_key": pos_key,
            "overall": overall,
            "stats": stats,
            "row": init_pos[pos_key][0],
            "col": init_pos[pos_key][1],
            "stamina": 100.0,  # 現行仕様では未使用（体力ロジックは無効化済み）
        }
    return players


if __name__ == "__main__":
    for formation_key in FORMATIONS:
        team_a = build_team("A", formation_key)
        team_b = build_team("B", formation_key)
        print("==== %s ====" % formation_key)
        for num, p in team_a.items():
            print(p["team"], p["number"], p["pos_key"], p["overall"], p["row"], p["col"], p["stats"])
        print("---")
        for num, p in team_b.items():
            print(p["team"], p["number"], p["pos_key"], p["overall"], p["row"], p["col"], p["stats"])
