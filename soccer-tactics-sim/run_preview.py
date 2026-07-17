# -*- coding: utf-8 -*-
"""
短時間プレビュー用スクリプト（動作確認・改造時のクイックチェックに使用）
デフォルトで36ステップ(36秒、1秒刻み)だけ実行し、各ステップのイベントとアスキー図を表示する。

使い方:
    python3 run_preview.py            # 36ステップ
    python3 run_preview.py 30         # 30ステップ実行したい場合
"""
import sys
from engine import MatchSim


def main():
    n_steps = 36
    if len(sys.argv) > 1:
        n_steps = int(sys.argv[1])

    sim = MatchSim(seed=7)
    print("チームA戦術=%s %s" % (sim.tactics["A"]["name"], sim.tactics["A"]))
    print("チームB戦術=%s %s" % (sim.tactics["B"]["name"], sim.tactics["B"]))
    print("")
    for _ in range(n_steps):
        event = sim.run_step()
        print("===== t=%ds (event: %s) scoreA=%d scoreB=%d =====" % (
            sim.t, event["event"], sim.score["A"], sim.score["B"]))
        print(event["detail"])
        print(sim.ascii_grid())
        print("")


main()
