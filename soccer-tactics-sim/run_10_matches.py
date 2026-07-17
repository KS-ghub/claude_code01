# -*- coding: utf-8 -*-
"""
45分ハーフ(2700ステップ)の試合を10試合連続で実行し、結果をまとめてテキスト出力するスクリプト。
match_result.txt / match_full_half.csv (run_match.py の出力)とは別ファイルに出力する。

使い方:
    python3 run_10_matches.py

出力:
    match_10games_result.txt … 10試合分のサマリー(各試合の戦術・スコア・ゴールログ、
                                 集計(総得点・平均得点・戦術別勝敗)をテキスト出力
"""
import time
from collections import Counter, defaultdict
from engine import MatchSim, TOTAL_STEPS_PER_HALF

N_MATCHES = 10
SEEDS = [2101 + i for i in range(N_MATCHES)]


def tactic_label(tactic):
    return "%s(%s)" % (tactic["name"], tactic["formation"])


def main():
    out = []
    out.append("==== 10試合 実行結果サマリー ====")

    match_results = []
    tactic_record = defaultdict(lambda: {"win": 0, "draw": 0, "lose": 0, "goals_for": 0, "goals_against": 0})
    total_goals = 0
    total_events = Counter()

    t0 = time.time()
    for i, seed in enumerate(SEEDS, start=1):
        sim = MatchSim(seed=seed)
        goal_log = []
        for step in range(1, TOTAL_STEPS_PER_HALF + 1):
            event = sim.run_step()
            total_events[event["event"]] += 1
            if event["event"] == "GOAL":
                goal_log.append((sim.t, event["detail"], dict(sim.score)))

        score_a, score_b = sim.score["A"], sim.score["B"]
        total_goals += score_a + score_b

        if score_a > score_b:
            result_label = "Aチーム勝利"
        elif score_a < score_b:
            result_label = "Bチーム勝利"
        else:
            result_label = "引き分け"

        tag_a = tactic_label(sim.tactics["A"])
        tag_b = tactic_label(sim.tactics["B"])

        rec_a = tactic_record[tag_a]
        rec_b = tactic_record[tag_b]
        rec_a["goals_for"] += score_a
        rec_a["goals_against"] += score_b
        rec_b["goals_for"] += score_b
        rec_b["goals_against"] += score_a
        if score_a > score_b:
            rec_a["win"] += 1
            rec_b["lose"] += 1
        elif score_a < score_b:
            rec_b["win"] += 1
            rec_a["lose"] += 1
        else:
            rec_a["draw"] += 1
            rec_b["draw"] += 1

        match_results.append({
            "index": i,
            "seed": seed,
            "tag_a": tag_a,
            "tag_b": tag_b,
            "score_a": score_a,
            "score_b": score_b,
            "result_label": result_label,
            "goal_log": goal_log,
        })
    elapsed = time.time() - t0

    out.append("試合数=%d 実行時間(実測秒)=%.2f" % (N_MATCHES, elapsed))
    out.append("")

    out.append("---- 各試合結果 ----")
    for m in match_results:
        out.append("第%d試合(seed=%d): %s vs %s → A%d-B%d (%s)" % (
            m["index"], m["seed"], m["tag_a"], m["tag_b"],
            m["score_a"], m["score_b"], m["result_label"]))
        if m["goal_log"]:
            for t, detail, score in m["goal_log"]:
                out.append("    t=%ds: %s score=%s" % (t, detail, score))
        else:
            out.append("    (ゴールなし)")
    out.append("")

    out.append("---- 集計: 総得点・平均得点 ----")
    out.append("10試合合計得点=%d 1試合平均得点=%.2f" % (total_goals, total_goals / N_MATCHES))
    out.append("")

    out.append("---- 集計: イベント種別カウント(10試合合計) ----")
    for k, v in total_events.most_common():
        out.append("%s: %d" % (k, v))
    out.append("")

    out.append("---- 集計: 戦術(フォーメーション)別成績 ----")
    out.append("%-24s %4s %4s %4s %8s %8s" % ("戦術", "勝", "分", "敗", "得点", "失点"))
    for tag, rec in sorted(tactic_record.items(), key=lambda x: -x[1]["win"]):
        out.append("%-24s %4d %4d %4d %8d %8d" % (
            tag, rec["win"], rec["draw"], rec["lose"], rec["goals_for"], rec["goals_against"]))

    text = "\n".join(out)
    with open("match_10games_result.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


main()
