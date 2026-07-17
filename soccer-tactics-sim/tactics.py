# -*- coding: utf-8 -*-
"""
チーム戦術プリセット定義

各チームは試合開始時(MatchSim.__init__)にこの中から1つを自動的にランダム選択する
(両チーム独立抽選のため、同じプリセットになることもある)。

4軸（まずはこの4つに絞って調整する）:
- line_height   : 守備時のライン基準位置を何m押し上げる(+)/下げる(-)か。
                   formation.get_default() で DEFENSE寄りのポジションほど強く反映される。
                   ハイプレス(+) / リトリート・引いて守る(-)。
- width         : 横方向の広がり倍率。1.0が標準。大きいほどワイドに広がり、小さいほど中央に絞る。
                   formation.get_default() で中央列(CENTER_COL)からのオフセットに掛ける。
- pass_risk     : パス選択のリスク許容度。1.0が標準。
                   大きいほど距離ペナルティを軽視して前進的なパスを選びやすくなり、
                   シュートも積極的に狙うようになる(ball_logic.choose_pass_target /
                   resolve_ball_actionのshoot_try_prob補正で使用)。
- press_intensity: 相手ボール保持時のインターセプト積極性。1.0が標準。
                   大きいほど有効距離・成功率が上がる(ball_logic.intercept_probabilityで使用)。

formation: players.FORMATIONS / formation.FORMATION_TABLES のキー("442"/"433"/"352")。
           フォーメーション自体も戦術の個性の一部として各プリセットに固定で紐付けている
           (5つ目の抽選軸にはせず、既存4軸との組み合わせを崩さないようにするため)。
           4-3-3は「ハイプレス」に(前線からの規制と好相性)、3-5-2は「リトリート堅守」に
           (3バック+5枚の中盤で守備の厚みを確保しつつ、ウイングバックが攻撃時は高い位置まで
           駆け上がる)割り当てている。

false_nine: Trueのとき攻撃時にFW1が中盤へ降り、MF_CM1が入れ替わりで前線へ飛び出す
            「偽9番」のポジション流動化を行う(formation.get_defaultで反映)。
            デゼルビ/グアルディオラ系のポゼッション戦術の代名詞的な仕組み。
fb_role:    サイドバック(DF_LB/DF_RB)の攻撃時の役割。
            "overlap"=高い位置に張り出して相手を引っ張る(アウベス型)、
            "inverted"=内側のハーフスペースへ絞ってビルドアップに参加する(偽SB)、
            "normal"=補正なし。3-5-2にはDF_LB/RBがいないため効果なし。
"""

TACTIC_PRESETS = [
    {
        "name": "ハイプレス",
        "formation": "433",
        "line_height": 8,
        "width": 1.0,
        "pass_risk": 1.2,
        "press_intensity": 1.3,
        "false_nine": False,
        "fb_role": "normal",
    },
    {
        "name": "リトリート堅守",
        "formation": "352",
        # 調整履歴: 当初(line_height=-8, width=0.9, pass_risk=0.8, press_intensity=0.8)は
        # 10試合で0勝15敗という壊れた結果になっていた。診断の結果、パラメータそのものより
        # フォーメーション側の不具合(FW1/FW2の間隔が広すぎてゴールエリアを外しやすい、
        # ウイングバックのLINE_HEIGHT_SENSITIVITYが高すぎて低いline_heightと組み合わさると
        # 攻撃時も深く引き戻されクロスが1本も成功しない)が主因と判明し、formation.pyを修正済み。
        # その上で、line_height/width/pass_risk/press_intensityも次の値に調整し、
        # 全プリセット総当たりで7勝5分20敗(勝率22%)まで改善したことを確認した
        # (元は0勝、依然として最も守備的=得点の伸びにくいプリセットではある)。
        "line_height": -4,
        "width": 1.0,
        "pass_risk": 1.0,
        "press_intensity": 1.2,
        "false_nine": False,
        "fb_role": "normal",  # 3-5-2にはDF_LB/RBがいないため実質効果なし
    },
    {
        "name": "サイド攻撃",
        "formation": "442",
        "line_height": 0,
        "width": 1.3,
        "pass_risk": 1.1,
        "press_intensity": 1.0,
        "false_nine": False,
        "fb_role": "overlap",  # SBが高く張り出して相手を引っ張る(アウベス型)
    },
    {
        "name": "ポゼッション安全策",
        "formation": "442",
        "line_height": 3,
        "width": 0.9,
        "pass_risk": 0.7,
        "press_intensity": 1.0,
        "false_nine": True,    # 偽9番: FW1が降りて数的優位を作る(デゼルビ/ペップ式)
        "fb_role": "inverted",  # SBが内側に絞ってビルドアップ参加(偽SB)
    },
    {
        "name": "バランス型",
        "formation": "442",
        "line_height": 0,
        "width": 1.0,
        "pass_risk": 1.0,
        "press_intensity": 1.0,
        "false_nine": False,
        "fb_role": "normal",
    },
]
