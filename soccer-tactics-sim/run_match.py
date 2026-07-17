# -*- coding: utf-8 -*-
"""
45分ハーフ(2700ステップ, 1秒刻み)のフル実行スクリプト

使い方:
    python3 run_match.py

出力:
    match_full_half.csv    … 全ステップ・全選手のログ(時刻, チーム, 背番号, 座標, 速度, 方向, ボール保持, イベント, スコア)
    match_result.txt       … サマリー(選択戦術、イベント件数、ゴールログ、7地点のスナップショット等)をテキスト出力
"""
import os
import time
from collections import Counter
from engine import MatchSim, TOTAL_STEPS_PER_HALF, ROWS, COLS


def main():
    sim = MatchSim(seed=2026)
    csv_path = "match_full_half.csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)

    event_counter = Counter()
    goal_log = []
    snapshot_steps = set([1, 450, 900, 1350, 1800, 2250, 2700])
    snapshots = {}

    t0 = time.time()
    for step in range(1, TOTAL_STEPS_PER_HALF + 1):
        event = sim.run_step()
        event_counter[event["event"]] += 1
        if event["event"] == "GOAL":
            goal_log.append((sim.t, event["detail"], dict(sim.score)))
        if step % 50 == 0:
            sim.write_csv(csv_path)
        if step in snapshot_steps:
            snapshots[step] = (sim.t, sim.ascii_grid(), dict(sim.score), event)
    sim.write_csv(csv_path)
    elapsed = time.time() - t0

    out = []
    out.append("==== 実行結果サマリー ====")
    out.append("コート=縦%dマス x 横%dマス(1マス=1m) 秒刻み=1秒" % (ROWS, COLS))
    out.append("チームA戦術=%s %s" % (sim.tactics["A"]["name"], sim.tactics["A"]))
    out.append("チームB戦術=%s %s" % (sim.tactics["B"]["name"], sim.tactics["B"]))
    out.append("総ステップ数=%d 試合内時間(秒)=%d 試合内時間(分)=%.1f" % (
        TOTAL_STEPS_PER_HALF, sim.t, sim.t / 60.0))
    out.append("実行時間(実測秒)=%.2f" % elapsed)
    out.append("最終スコア A=%d B=%d" % (sim.score["A"], sim.score["B"]))
    out.append("")
    out.append("---- イベント種別カウント ----")
    for k, v in event_counter.most_common():
        out.append("%s: %d" % (k, v))
    out.append("")
    out.append("---- ゴールログ ----")
    if goal_log:
        for t, detail, score in goal_log:
            out.append("t=%ds: %s score=%s" % (t, detail, score))
    else:
        out.append("(ゴールなし)")

    out.append("")
    out.append("---- CSV行数確認 ----")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        n_lines = sum(1 for _ in f)
    expected = TOTAL_STEPS_PER_HALF * 22 + 1
    out.append("csv総行数=%d 期待値=%d 一致=%s" % (n_lines, expected, n_lines == expected))

    out.append("")
    out.append("---- スナップショット(アスキー図) ----")
    for step in sorted(snapshots.keys()):
        t, grid, score, ev = snapshots[step]
        out.append("=== step=%d t=%ds scoreA=%d scoreB=%d last_event=%s ===" % (
            step, t, score["A"], score["B"], ev["event"]))
        out.append(grid)
        out.append("")

    bad = 0
    for p in sim.all_players():
        if not (1 <= p["row"] <= ROWS and 1 <= p["col"] <= COLS):
            bad += 1
    out.append("座標範囲外の選手数=%d" % bad)

    text = "\n".join(out)
    with open("match_result.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


main()
