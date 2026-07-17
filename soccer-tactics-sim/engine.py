# -*- coding: utf-8 -*-
"""
サッカー戦術シミュレーション エンジン本体

仕様:
- コート: 縦105マス x 横65マス（1マス=1m換算）
- 時間: 1秒刻み、45分ハーフ = 2700ステップ
- 1ステップの最大移動: 選手のspeed能力に応じて1〜5マス(m)
- 体力ゲージ: 現行仕様では無効化（純粋戦術検証のため）
- チーム戦術: tactics.py の5プリセットから各チームが試合開始時に自動抽選(MatchSim.__init__)。
  フォーメーション(4-4-2/4-3-3)も各プリセットに紐付いており、戦術と同時に決まる。
- ボールロジック(パス/インターセプト/シュート): ball_logic.py に分離
- ポジショニング(デフォルト位置・ボール追随・戦術反映): formation.py に分離
- 選手データ・能力配分: players.py に分離
"""
import csv
import math
import os
import random

from players import build_team
from formation import dynamic_target, ROWS, COLS
from ball_logic import resolve_ball_action, offside_line_row
from tactics import TACTIC_PRESETS

CELL_H_M = 1.0
CELL_W_M = 1.0
STEP_SEC = 1
TOTAL_STEPS_PER_HALF = 45 * 60 // STEP_SEC  # 45分 / 1秒 = 2700

# ボールアクション(パス/シュート判定)を毎ステップ試みると、旧仕様(3秒刻み)に比べ
# 同じ実時間でのターンオーバー確率が累積的に跳ね上がってしまう(3倍の頻度で判定されるため)。
# ポジション更新は毎秒行いつつ、ボールアクションの意思決定頻度は旧仕様と同程度(平均3秒に1回)を
# 維持するため、この確率でのみ resolve_ball_action を実行する。
BASE_ACTION_INTERVAL_SEC = 3.0
ACTION_PROB_PER_STEP = min(1.0, STEP_SEC / BASE_ACTION_INTERVAL_SEC)

# 距離換算係数(ball_logic.SCALEと同じ考え方): 旧グリッド(1マス≒5m)→新グリッド(1マス=1m)
GRID_SCALE = 5.0
# ボール保持者が前進する際の目標地点への追加前進オフセット(旧仕様: 2セル≒10m)
HOLDER_FORWARD_BONUS = round(2 * GRID_SCALE)

DIRS8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def dir8(dr, dc):
    if dr == 0 and dc == 0:
        return "-"
    ang = math.degrees(math.atan2(dc, dr))
    ang = (ang + 360.0) % 360.0
    idx = int(((ang + 22.5) % 360.0) // 45)
    return DIRS8[idx]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def move_toward(pos, target, max_step):
    r, c = pos
    tr, tc = target
    dr = clamp(tr - r, -max_step, max_step)
    dc = clamp(tc - c, -max_step, max_step)
    return (clamp(r + dr, 1, ROWS), clamp(c + dc, 1, COLS))


def dist_m(prev, cur):
    dr = (cur[0] - prev[0]) * CELL_H_M
    dc = (cur[1] - prev[1]) * CELL_W_M
    return math.hypot(dr, dc)


def max_cells_for(speed_stat):
    """能力(speed)に応じた1秒あたりの最大移動マス数(=m)。上限5マス(5m/秒)。"""
    if speed_stat >= 24:
        return 5
    if speed_stat >= 20:
        return 4
    if speed_stat >= 17:
        return 3
    if speed_stat >= 13:
        return 2
    return 1


class MatchSim(object):
    def __init__(self, seed=42):
        self.t = 0
        self.rows = []       # CSV出力用バッファ
        self.events = []     # イベント履歴 [(time_sec, event_dict), ...]
        self.rng = random.Random(seed)
        self.score = {"A": 0, "B": 0}
        self.kickoff_team = "A"
        # 各チームの戦術を試合開始時に自動抽選(独立抽選なので同一プリセットになる場合もある)。
        # フォーメーション(tactic["formation"])もここで決まるため、チーム編成より先に行う。
        self.tactics = {
            "A": self.rng.choice(TACTIC_PRESETS),
            "B": self.rng.choice(TACTIC_PRESETS),
        }
        self.team_a = build_team("A", self.tactics["A"]["formation"])
        self.team_b = build_team("B", self.tactics["B"]["formation"])
        self.ball_holder = ("A", 10)  # キックオフ: Aチーム FW1(背番号10)がボール保持

    def all_players(self):
        for p in self.team_a.values():
            yield p
        for p in self.team_b.values():
            yield p

    def get(self, team, num):
        return (self.team_a if team == "A" else self.team_b)[num]

    def ball_pos(self):
        t, n = self.ball_holder
        p = self.get(t, n)
        return (p["row"], p["col"])

    def reset_kickoff(self, kickoff_team):
        """ゴール後、両チームを初期フォーメーションに戻しキックオフする（戦術・フォーメーションは維持）"""
        self.team_a = build_team("A", self.tactics["A"]["formation"])
        self.team_b = build_team("B", self.tactics["B"]["formation"])
        if kickoff_team == "A":
            self.ball_holder = ("A", 10)
        else:
            self.ball_holder = ("B", 10)

    def run_step(self):
        """1ステップ(1秒)分の処理。戻り値はそのステップで発生したイベント(dict)。

        処理順序:
          1. ボールアクション解決(パス/インターセプト/シュート) — 一定確率(ACTION_PROB_PER_STEP)でのみ判定。
             判定しないステップはボール保持者がそのまま保持して前進する(CARRY)。
          2. ゴール発生時はスコア加算・キックオフへリセット
          3. 全選手のポジション更新(デフォルト位置+戦術補正 + ボール追随、保持者は前進補正)
          4. CSVログ行の生成
        """
        self.t += STEP_SEC
        ball_pos_before = self.ball_pos()
        acting_team, acting_num = self.ball_holder  # このステップでアクションした選手(CSVのevent記録用)

        if self.rng.random() < ACTION_PROB_PER_STEP:
            event = resolve_ball_action(self, self.rng)
        else:
            holder_team, holder_num = self.ball_holder
            event = {
                "event": "CARRY",
                "detail": "%s%02d がボールを保持して前進" % (holder_team, holder_num),
            }
        self.events.append((self.t, event))

        if event["event"] == "GOAL":
            scoring_team = event["scoring_team"]
            self.score[scoring_team] += 1
            conceding_team = "B" if scoring_team == "A" else "A"
            self.reset_kickoff(conceding_team)
            ball_pos_before = self.ball_pos()

        holder_team, holder_num = self.ball_holder

        # 攻撃側の(保持者以外の)選手はオフサイドラインの手前で止まって駆け引きする。
        # 相手最終ライン(守備側で2番目にゴールに近い選手)をチームごとに算出しておく。
        offside_lines = {
            "A": offside_line_row(list(self.team_b.items()), 1, rows=ROWS),
            "B": offside_line_row(list(self.team_a.items()), -1, rows=ROWS),
        }

        for team_label, team_dict in [("A", self.team_a), ("B", self.team_b)]:
            phase = "attack" if team_label == holder_team else "defense"
            tactic = self.tactics[team_label]
            formation = tactic["formation"]
            attack_dir = 1 if team_label == "A" else -1
            for num, p in team_dict.items():
                prev = (p["row"], p["col"])
                target = dynamic_target(p["pos_key"], team_label, phase, ball_pos_before, tactic, formation=formation)

                if team_label == holder_team and num == holder_num:
                    target = (clamp(target[0] + attack_dir * HOLDER_FORWARD_BONUS, 1, ROWS), target[1])
                elif team_label == holder_team:
                    # 保持者以外の攻撃側選手はオフサイドラインを越えない位置で止まる
                    # (裏へ抜けるのはスルーパス(THROUGH_OK)が通った瞬間のみ)
                    line = offside_lines[team_label]
                    if (target[0] - line) * attack_dir > 0:
                        target = (clamp(line, 1, ROWS), target[1])

                max_cells = max_cells_for(p["stats"]["speed"])
                new_pos = move_toward(prev, target, max_cells)
                dist = dist_m(prev, new_pos)
                speed_mps = dist / STEP_SEC
                d = dir8(new_pos[0] - prev[0], new_pos[1] - prev[1])

                p["row"], p["col"] = new_pos
                p["_last_speed"] = round(speed_mps, 2)
                p["_last_dir"] = d

        for team_label, team_dict in [("A", self.team_a), ("B", self.team_b)]:
            for num, p in team_dict.items():
                self.rows.append({
                    "time_sec": self.t,
                    "team": team_label,
                    "number": num,
                    "pos_key": p["pos_key"],
                    "row": p["row"],
                    "col": p["col"],
                    "speed_mps": p["_last_speed"],
                    "direction": p["_last_dir"],
                    "has_ball": (team_label, num) == self.ball_holder,
                    "event": event["event"] if (team_label, num) == (acting_team, acting_num) else "",
                    "score_a": self.score["A"],
                    "score_b": self.score["B"],
                })
        return event

    def write_csv(self, path):
        fieldnames = ["time_sec", "team", "number", "pos_key", "row", "col",
                      "speed_mps", "direction", "has_ball", "event", "score_a", "score_b"]
        write_header = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                w.writeheader()
            for r in self.rows:
                w.writerow(r)
        self.rows = []

    def ascii_grid(self):
        """現在の全選手配置とボール位置(*印)をテキストのアスキー図として返す"""
        grid = [["." for _ in range(COLS)] for _ in range(ROWS)]
        for p in self.all_players():
            r = p["row"] - 1
            c = p["col"] - 1
            label = "%s%02d" % (p["team"], p["number"])
            grid[r][c] = label

        bt, bn = self.ball_holder
        bp = self.get(bt, bn)
        ball_marker = (bp["row"] - 1, bp["col"] - 1)

        lines = []
        for r in range(ROWS - 1, -1, -1):
            row_cells = []
            for c in range(COLS):
                v = grid[r][c]
                if v != ".":
                    mark = "*" if (r, c) == ball_marker else " "
                    row_cells.append("%s%s" % (v, mark))
                else:
                    row_cells.append(" . ")
            line = "row%03d | " % (r + 1) + " ".join("%3s" % cell for cell in row_cells)
            lines.append(line)
        return "\n".join(lines)
