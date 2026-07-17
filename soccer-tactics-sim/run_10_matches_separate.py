# -*- coding: utf-8 -*-
"""
45分ハーフ(2700ステップ)の試合を10試合実行し、各試合ごとに別ファイルとして出力するスクリプト。
run_match.py の1試合分の出力(CSV+サマリーtxt)を、末尾に試合番号(1〜10)を付けて10組出力する。
run_match.py / run_10_matches.py の出力(match_result.txt, match_full_half.csv,
match_10games_result.txt)とはファイル名が重複しないため、上書きしない。

使い方:
    python3 run_10_matches_separate.py

出力(各試合ごとに1組、計10組=20ファイル):
    match_full_half_<N>.csv … N試合目の全ステップ・全選手のログ
    match_result_<N>.txt    … N試合目のサマリー(選択戦術、イベント件数、ゴールログ、
                                7地点のスナップショット等)
"""
import os
import time
from collections import Counter
from engine import MatchSim, TOTAL_STEPS_PER_HALF, ROWS, COLS

N_MATCHES = 10
SEEDS = [2101 + i for i in range(N_MATCHES)]


def run_one_match(match_no, seed):
    sim = MatchSim(seed=seed)
    csv_path = "match_full_half_%d.csv" % match_no
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
    out.append("==== 第%d試合 実行結果サマリー(seed=%d) ====" % (match_no, seed))
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
    result_path = "match_result_%d.txt" % match_no
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "match_no": match_no,
        "seed": seed,
        "score_a": sim.score["A"],
        "score_b": sim.score["B"],
        "tactic_a": sim.tactics["A"]["name"],
        "tactic_b": sim.tactics["B"]["name"],
        "csv_path": csv_path,
        "result_path": result_path,
        "bad_coords": bad,
    }


def main():
    summaries = []
    for i, seed in enumerate(SEEDS, start=1):
        summaries.append(run_one_match(i, seed))

    print("==== 10試合 個別ファイル出力 完了 ====")
    for s in summaries:
        print("第%d試合(seed=%d): %s vs %s → A%d-B%d  [%s / %s]  座標範囲外=%d" % (
            s["match_no"], s["seed"], s["tactic_a"], s["tactic_b"],
            s["score_a"], s["score_b"], s["result_path"], s["csv_path"], s["bad_coords"]))


main()
