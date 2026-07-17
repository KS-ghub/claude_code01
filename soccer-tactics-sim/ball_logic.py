# -*- coding: utf-8 -*-
"""
パスロジック / ボールロスト（攻守切り替え）/ シュート・ゴール判定
体力は考慮しない（純粋戦術検証のため能力値のみで判定）

【グリッド変更(1マス=1m)に伴う距離換算について】
旧仕様は1マス≒5m(縦105m/20マス, 横68m/15マス)換算で調整された値だった。
新仕様は1マス=1mのため、距離に関する定数はすべて SCALE=5 を用いてメートル換算し、
距離に掛かる係数は SCALE で割ることで、同じスコア感覚・確率感覚を概ね保つようにしている。
(あくまで近似。実際のバランスは試合ログを見ながら追加調整が必要)

【チーム戦術(tactics.py)の反映】
- pass_risk: choose_pass_target()の距離ペナルティ・前進ボーナスに反映。シュート積極性、
  バックパス頻度にも反映。
- press_intensity: intercept_probability()のインターセプト有効距離・確率、GKの飛び出し範囲に反映。
- line_height: バックパス頻度、GKの飛び出し範囲に反映(formation.py側のポジショニングにも反映)。
(width は formation.py 側で反映)

【設計メモ】
- パス候補選択(choose_pass_target): 視野(vision)に応じた射程内から、前進度と距離でスコアリング。
  ・同じ相手への連続パスにペナルティ(REPEAT_PENALTY)
  ・DF同士の横パスにペナルティ(DF_TO_DF_PENALTY) … 自陣での往復(膠着)を避けるため
  ・MF/FWへの前進的パスにボーナス(FORWARD_BONUS)
  ・上位候補(PASS_CANDIDATE_TOP_K)から重み付きランダム抽選(常に同じ相手に固定しない)
- インターセプト判定: 最寄りの守備者との距離に応じて確率算出。上限はINTERCEPT_PROB_CAP。
- シュート判定: ボール保持者が「中央寄り」でシュートゾーン(SHOOT_ZONE_DEPTH)内に入ると
  一定確率(SHOOT_TRY_PROB)でシュートを選択。着弾列(col)を正確性と乱数から算出し、
  ゴールエリア(中央±GOAL_ZONE_HALF_WIDTH列)の範囲内なら成功率判定(キック力・正確性と
  GKの能力・距離から算定)へ進み、範囲外なら枠外(自動失敗)。
  ゴール成立時はイベント"GOAL"を返し、engine側でスコア加算とキックオフリセットを行う。
- クロス判定: ボール保持者が「サイド(|col-中央| >= WIDE_COL_THRESHOLD)」かつ深い位置
  (SHOOT_ZONE_DEPTH内)にいる場合、シュートの代わりに一定確率(CROSS_TRY_PROB)でクロスを試みる。
  ボックス内(中央±BOX_HALF_WIDTH かつ深い位置)に走り込んでいる味方を探し、いれば成功率判定へ。
  成功すればその味方にボールが渡り(＝ボックス内からシュートゾーンでの次アクションに繋がる)、
  失敗/インターセプトなら攻守交代。ボックス内に味方がいなければ通常のパス選択にフォールバックする。
  サイド攻撃(width重視)の戦術が得点機会に繋がるようにするための経路。
- カットバック判定: ボール保持者が中央寄りでシュートゾーン内にいる場合、シュートの前に
  一定確率(CUTBACK_TRY_PROB)でボックス内に走り込んでいる味方(MFを優先)への折り返しを検討する。
  対象がいれば成功率判定(パスと同じ計算式を流用)へ進み、成功すればその味方にボールが渡る。
  対象がいない/確率が外れた場合は通常通りシュートを試みる。
- ミドルシュート判定: MFがシュートゾーンには届かないがアタッキングサード内(MID_SHOOT_ZONE_DEPTH)に
  いる場合、低確率(MID_SHOT_TRY_PROB)・低成功率でロングシュートを試みる。着弾列判定・
  ゴールエリア判定の仕組みはシュートと共通(compute_shot_column/is_goal_column)だが、
  着弾のブレが大きく(MID_SHOT_COL_SPREAD_MULT)、成功率も距離ペナルティ込みで低く抑えている
  (mid_shot_success_probability)。FW以外の得点パターンを増やすための経路。
- バックパス判定: DFがボールを持った際、一定確率でGKへ戻すことを検討する
  (backpass_try_probability)。通常のパススコアリング(前進度重視)にGKを乗せると
  後方へのパスとして常に低評価になり実質選ばれないため、独立した分岐として実装している。
  確率は戦術のpass_risk(低いほど戻しやすい)とline_height(低い＝リトリートほど戻しやすい)で
  補正され、リトリート堅守とハイプレスでビルドアップの様子が明確に変わるようにしている。
  成功/失敗/インターセプトの判定は通常のパスと同じ計算式を流用する。
- GKの飛び出し(クロスキャッチ)判定: クロスの送り先が決まった後、通常のインターセプト判定の前に
  守備側GKが飛び出してキャッチできるか判定する(gk_claim_probability)。GKからクロス着弾点までの
  距離、GK自身の能力(正確性)、守備側チームの戦術(press_intensity/line_height、値が高いほど
  積極的に飛び出す＝スイーパーキーパー的)を反映する。キャッチに失敗した場合は特別な処理はせず、
  通常のクロス解決(インターセプト→成功/失敗判定)にそのままフォールバックする。
- ゾーン分類(col_zone): 列位置を「中央 / ハーフスペース / サイド」の3帯に分類する。
  敵陣ハーフスペースの受け手へのパスにはHALFSPACE_BONUSを与え、ポジショナルプレーの
  「ハーフスペース支配」を再現する。スルーパスの典型レーンとしても使う。
- GKビルドアップ配球(choose_gk_distribution): GK保持時は前進度ではなく「フリー度」
  (受け手の最寄りの相手までの距離)で配球先を選ぶ。相手プレスが片側に寄れば逆の空いた
  CB/SB/アンカーへ自然に散らされる(デゼルビの「引きつけてから逃がす」ビルドアップ)。
- サイドチェンジ(「2進んで1戻る」): 同サイドで前進できないアクションがSWITCH_AFTER_STUCK回
  続いたら、逆サイドの受け手へのパスにSWITCH_BONUSを与えて相手ブロックを左右に揺さぶる。
  状態はsim._side_state(チームごと)に保持し、sim._last_switch_sideで分析用に公開する。
- スルーパス(裏抜けラン): 敵陣に入った保持者が、最終ラインの手前で駆け引きしているFWの
  「裏のスペース」へパスを通す(choose_through_target)。成功すれば受け手がライン裏へ
  実際に移動した状態でボールを持つ(THROUGH_OK)。飛び出しが早すぎるとオフサイド。
- オフサイド判定(is_offside): パスの瞬間の受け手が「敵陣内」「最終ライン(守備側で2番目に
  ゴールに近い選手)より前」「ボールより前」をすべて満たすとオフサイド。通常パス/クロス/
  カットバック/スルーパスすべてに適用。相手ボール(最寄りの守備者のFK相当)で再開する。
  これによりline_height(ハイライン)は「裏を取られるリスク」と「相手をオフサイドに
  引っかける武器」の現実的なトレードオフを持つ。

【既知の改善余地（引き継ぎ時の検討ポイント）】
1. シュート成功率が0.6でほぼ天井に張り付きやすい(shoot_success_probabilityのbase値が大きい)。
   ゴールが飛び出しすぎる場合はbaseの係数やSHOOT_TRY_PROBを下げて調整する。
2. 得点がFW(背番号10・11)に偏る傾向は、カットバック・ミドルシュートの追加で緩和を図った。
   実際の得点者分布は試合ログで継続的に確認し、必要ならCUTBACK_MF_BONUSやMID_SHOT_TRY_PROBを
   調整する。
3. RECENT_MEMORYやDF_TO_DF_PENALTY等の定数はヒューリスティックな調整値。
   大量ステップでのプレースタイル統計を取り、チューニングする余地がある。
4. チームごとの戦術差は tactics.py の4軸(line_height/width/pass_risk/press_intensity)で
   表現しているが、さらに軸を増やしたい場合はここと formation.py を拡張する。
"""
import math

RECENT_MEMORY = 6
INTERCEPT_PROB_CAP = 0.55
PASS_CANDIDATE_TOP_K = 3
REPEAT_PENALTY = 4.0
DF_TO_DF_PENALTY = 2.0
FORWARD_BONUS = 1.0

# 旧グリッド(1マス≒5m)→新グリッド(1マス=1m)の距離換算係数
SCALE = 5.0

PROGRESS_COEF = 2.0 / SCALE          # 旧: progress * 2.0
DIST_COEF = 0.5 / SCALE              # 旧: d * 0.5
PASS_MIN_DIST = 1.0 * SCALE          # 旧: d >= 1.0 (セル)
PASS_DIST_PENALTY_COEF = 0.03 / SCALE  # 旧: target_dist * 0.03
INTERCEPT_DIST_CAP = 2.5 * SCALE     # 旧: 2.5セル
SHOOT_DIST_COEF = 0.01 / SCALE       # 旧: dist * 0.01
SHOOT_ZONE_DEPTH = round(4 * SCALE)  # 旧: 4セル(相手ゴールラインから何m以内をシュートゾーンとするか)

SHOOT_TRY_PROB = 0.5  # シュートゾーン内でシュートを試みる基礎確率(戦術のpass_riskで補正)

# ゴールエリア: 横中央から左右3マス(計7m幅)。ピッチ全体の列数はformation.COLSと一致させること。
PITCH_COLS = 65
CENTER_COL = (PITCH_COLS + 1) // 2  # 33（formation.CENTER_COLと一致）
GOAL_ZONE_HALF_WIDTH = 3

# クロス関連: ボックス(中央±BOX_HALF_WIDTH かつ深さSHOOT_ZONE_DEPTH以内)と
# サイド(中央からの距離がWIDE_COL_THRESHOLD以上)の定義。
# BOX_HALF_WIDTH=19は実際のペナルティエリア幅(約40m/68m幅ピッチ)に近い比率を新グリッドに換算した値。
BOX_HALF_WIDTH = 19
WIDE_COL_THRESHOLD = 19
CROSS_TRY_PROB = 0.5      # サイドの深い位置でクロスを試みる基礎確率(戦術のpass_riskで補正)
CROSS_MAX_RANGE = SCALE * 6.0   # クロスの最大到達距離(m)
CROSS_DIST_PENALTY_COEF = PASS_DIST_PENALTY_COEF * 1.2  # クロスは通常のパスよりやや距離の影響を受けやすい
# サイドの選手がクロスを試みられる深さ(相手ゴールラインから何m以内か)。
# 実際のクロスはシュートゾーン(SHOOT_ZONE_DEPTH=20)より手前の「アタッキングサード」全体から
# 起こりうるため、SHOOT_ZONE_DEPTHより緩めの深さを設定する。
CROSS_ZONE_DEPTH = 35
# クロスの受け手(FW等)が「ボックスに走り込んでいる」と判定する深さ。
# FWは自身がボール保持者でない限りSHOOT_ZONE_DEPTH(20)まで上がってくることは少ないため、
# SHOOT_ZONE_DEPTHより緩め・CROSS_ZONE_DEPTHより厳しめの深さを設定する。
BOX_DEPTH = 30
# サイドのポジション(FB/ワイドMF/ウイング等)へのパスに、戦術のwidthに応じたボーナスを与える。
# widthが大きい(サイド攻撃志向)ほどサイドへ展開しやすく、狭い(width<1.0)ほどサイドを避ける。
# ポジションキーの末尾サフィックスで判定するため、新しいフォーメーション(例: FW_LW/FW_RW)を
# 追加してもここを書き換えずに対応できる。
WIDE_POS_SUFFIXES = ("LB", "RB", "LM", "RM", "LW", "RW", "LWB", "RWB")
WIDE_BONUS_COEF = 2.0


def is_wide_position(pos_key):
    suffix = pos_key.rsplit("_", 1)[-1]
    return suffix in WIDE_POS_SUFFIXES

# カットバック関連: シュートゾーン内でボールを持った際、シュートの前に
# ボックス内へ走り込んでいる味方(MF優先)への折り返しを検討する。
CUTBACK_TRY_PROB = 0.3
CUTBACK_MAX_RANGE = SCALE * 3.0  # 15m(ボックス内は狭いので短い距離を想定)
CUTBACK_MF_BONUS = 3.0  # MFへの折り返しを優先的に選びやすくする(得点者の偏り緩和が狙い)

# ミドルシュート関連: MFがシュートゾーンには届かないがアタッキングサード内にいる場合の
# 低確率・低成功率のロングシュート。
MID_SHOOT_ZONE_DEPTH = 40
MID_SHOT_TRY_PROB = 0.15
MID_SHOT_COL_SPREAD_MULT = 1.6  # 通常シュートより着弾のブレを大きくする(遠距離ゆえの精度低下)

# サイドチェンジ(「2進んで1戻る」プレス回避)関連: 同じサイドでの前進に詰まった状態が
# 一定回数続いたら、逆サイドの味方へのパスに一時的なボーナスを与え、相手の守備ブロックを
# 左右に揺さぶる。デゼルビの「同サイドで相手を引きつけて逆へ逃がす」リズムの再現。
SWITCH_AFTER_STUCK = 2   # 同サイドで前進できないアクションが何回続いたらサイドチェンジを狙うか
SWITCH_BONUS = 2.5       # 逆サイドの受け手へのパススコアボーナス
PROGRESS_EPS = 2         # 「前進した」とみなす攻撃方向の前進量(m)

# ハーフスペース関連: 中央(|col-中央| < HALF_SPACE_INNER)とサイド(>= WIDE_COL_THRESHOLD)の
# 間の列帯を「ハーフスペース」と定義する。デゼルビ/グアルディオラ系のポジショナルプレーで
# 崩しの主戦場となるレーン。攻撃側ハーフでハーフスペースに立つ味方へのパスにボーナスを与え、
# スルーパス(裏抜け)の典型レーンとしても扱う。
HALF_SPACE_INNER = 8    # 中央帯の半幅(これ未満は「中央」)
HALFSPACE_BONUS = 1.2   # 敵陣ハーフスペースの受け手へのパススコアボーナス

# バックパス(ビルドアップ)関連: DFがGKへ戻すかどうかの基礎確率と、戦術による補正。
BACKPASS_TRY_PROB_BASE = 0.12
BACKPASS_PASSRISK_COEF = 0.15  # pass_riskが低い(安全志向)ほど戻しやすい
BACKPASS_LINE_COEF = 0.01      # line_heightが低い(リトリート)ほど戻しやすい
BACKPASS_TRY_PROB_CAP = 0.5

# GKの飛び出し(クロスのキャッチ)関連。
GK_CLAIM_BASE_RANGE = SCALE * 3.0  # 15m(ここまでならGKが飛び出して届く基準距離)
GK_CLAIM_BASE_PROB = 0.5
GK_CLAIM_PROB_CAP = 0.5

# GKビルドアップ(配球)関連: GKがボールを持ったとき、通常の前進度スコアリングではなく
# 「空いている(最寄りの相手が遠い)後方の受け手へ選択的に散らす」専用ロジックを使う。
# デゼルビの「相手のプレスを引きつけてから空いた方へ逃がす」ビルドアップの再現。
GK_DIST_MAX_RANGE = SCALE * 7.0    # 35m(GKの配球が届く範囲)
GK_DIST_FREENESS_COEF = 0.3        # 受け手の「フリー度」(最寄りの相手との距離)の重み
GK_DIST_FREENESS_CAP = 20.0        # フリー度として評価する距離の上限(m)
# GKの配球先として考慮するポジション(DF全般+アンカー+ウイングバック)
GK_DIST_TARGET_PREFIXES = ("DF",)
GK_DIST_TARGET_KEYS = ("MF_DM", "MF_LWB", "MF_RWB")
GK_DIST_SUCC_BONUS = 0.3           # フリーな受け手への短い配球は通常のパスより成功しやすい

# オフサイド関連: パス(通常/スルー/クロス/カットバック)の受け手が、パスの瞬間に
# 「最終ライン(守備側で2番目にゴールに近い選手)より前」かつ「ボールより前」かつ「敵陣内」に
# いる場合はオフサイド。攻撃側の反則として相手ボール(最寄りの守備者のフリーキック相当)になる。
# これによりハイライン戦術は「裏を取られるリスク」と引き換えに「相手をオフサイドに
# 引っかける」武器を持つ、という現実的なトレードオフが成立する。
OFFSIDE_ENABLED = True
# ラインの上下動に選手の追随が1〜2秒遅れる(移動速度上限がある)ため、数m程度のはみ出しは
# 「ライン上の駆け引きの範囲内」として見逃す。これがないと守備ラインが下がる度に
# 攻撃側FWが一時的に取り残されて非現実的な頻度でオフサイドになる。
ONSIDE_TOLERANCE = 3.0

# スルーパス(裏抜けラン)関連: 敵陣に入ったボール保持者が、最終ラインの手前で駆け引きしている
# FWの「裏のスペース」へパスを通す。成功すれば受け手がライン裏へ走り込んだ状態でボールを持ち、
# 一気にシュートチャンスになる。ハーフスペースは裏へのパスの典型レーンとしてボーナスを与える。
THROUGH_TRY_PROB = 0.18       # 条件を満たしたとき試みる基礎確率(pass_riskで補正)
THROUGH_RUN_DEPTH = 6         # 最終ラインの何m裏へ走り込むか
THROUGH_MAX_RANGE = SCALE * 7.0  # スルーパスの最大距離(35m)
THROUGH_LINE_MARGIN = 10      # ラインの手前何m以内にいるFWを裏抜け候補とするか
THROUGH_MISTIME_PROB = 0.15   # 飛び出しのタイミングが早すぎてオフサイドになる確率
THROUGH_MIN_ADVANCE = 40      # 自ゴールから何m以上進んだ位置からスルーパスを狙えるか


def euclid(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def choose_pass_target(holder, teammates, attack_dir, recent_holders, rng,
                       pass_risk=1.0, width=1.0, switch_side=0):
    """switch_side: 0=通常。+1/-1のとき、その符号側(col-中央の符号)にいる受け手への
    パスにSWITCH_BONUSを与える(「2進んで1戻る」のサイドチェンジ狙い)。"""
    vision = holder["stats"]["vision"]
    max_range = SCALE * (4 + vision / 5.0)
    holder_is_df = holder["pos_key"].startswith("DF")

    hp = (holder["row"], holder["col"])
    candidates = []
    for num, p in teammates:
        pp = (p["row"], p["col"])
        d = euclid(hp, pp)
        if d <= max_range and d >= PASS_MIN_DIST:
            progress = (pp[0] - hp[0]) * attack_dir
            # pass_riskが高いほど距離ペナルティを軽視し、前進的なパスを選びやすくなる
            score = progress * PROGRESS_COEF - d * DIST_COEF * (2.0 - pass_risk)
            if num in recent_holders:
                score -= REPEAT_PENALTY
            if holder_is_df and p["pos_key"].startswith("DF"):
                score -= DF_TO_DF_PENALTY
            if p["pos_key"].startswith("MF") or p["pos_key"].startswith("FW"):
                score += FORWARD_BONUS * pass_risk
            if is_wide_position(p["pos_key"]):
                # widthが高い(サイド攻撃)戦術ほどサイドの選手を使いたがり、
                # widthが低い(中央志向)戦術ほどサイド展開を避ける。
                score += (width - 1.0) * WIDE_BONUS_COEF
            if is_halfspace(pp[1]) and in_opponent_half(pp[0], attack_dir):
                # 敵陣ハーフスペースに立つ味方は崩しの起点として優先度を上げる
                score += HALFSPACE_BONUS
            if switch_side != 0:
                cand_side = pp[1] - CENTER_COL
                if cand_side * switch_side >= HALF_SPACE_INNER:
                    # 詰まっているサイドと逆の、明確に反対側にいる受け手を優先する
                    score += SWITCH_BONUS
            candidates.append((score, num, p, d))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:PASS_CANDIDATE_TOP_K]
    min_score = min(c[0] for c in top)
    shift = abs(min_score) + 1.0
    weights = [c[0] + shift for c in top]
    chosen = rng.choices(top, weights=weights, k=1)[0]
    return chosen


def pass_success_probability(holder, target_dist):
    kick = holder["stats"]["kick"]
    acc = holder["stats"]["accuracy"]
    base = (kick + acc) / 2 / 30.0
    base = max(0.3, min(0.97, base))
    dist_penalty = min(0.35, target_dist * PASS_DIST_PENALTY_COEF)
    return max(0.15, base - dist_penalty)


def nearest_defender(pos, defenders):
    best = None
    best_d = None
    for num, p in defenders:
        d = euclid(pos, (p["row"], p["col"]))
        if best_d is None or d < best_d:
            best_d = d
            best = (num, p, d)
    return best


def pick_recovering_defender(pos, defenders, rng, top_k=2):
    scored = []
    for num, p in defenders:
        d = euclid(pos, (p["row"], p["col"]))
        scored.append((d, num, p))
    scored.sort(key=lambda x: x[0])
    top = scored[:top_k]
    d, num, p = rng.choice(top)
    return num, p, d


def intercept_probability(pass_target_pos, defenders, press_intensity=1.0):
    num, p, d = nearest_defender(pass_target_pos, defenders)
    if d is None:
        return 0.0, None
    cap = INTERCEPT_DIST_CAP * press_intensity
    if d > cap:
        return 0.0, None
    base = max(0.0, (cap - d) / cap) * 0.45 * press_intensity
    tactic_bonus = (p["stats"]["tactic"] - 15) * 0.008
    prob = max(0.0, min(INTERCEPT_PROB_CAP, base + tactic_bonus))
    return prob, num


def in_shoot_zone(holder, attack_dir, rows=105):
    if attack_dir == 1:
        return holder["row"] >= rows - SHOOT_ZONE_DEPTH + 1
    else:
        return holder["row"] <= SHOOT_ZONE_DEPTH


def in_mid_shoot_zone(holder, attack_dir, rows=105):
    """MFがミドルシュートを試みられる深さ(アタッキングサード相当)にいるかどうか"""
    if attack_dir == 1:
        return holder["row"] >= rows - MID_SHOOT_ZONE_DEPTH + 1
    else:
        return holder["row"] <= MID_SHOOT_ZONE_DEPTH


def in_cross_zone(holder, attack_dir, rows=105):
    """サイドの選手がクロスを試みられる深さ(アタッキングサード相当)にいるかどうか"""
    if attack_dir == 1:
        return holder["row"] >= rows - CROSS_ZONE_DEPTH + 1
    else:
        return holder["row"] <= CROSS_ZONE_DEPTH


def is_wide(pos_or_player, cols=PITCH_COLS):
    center = (cols + 1) // 2
    col = pos_or_player["col"] if isinstance(pos_or_player, dict) else pos_or_player
    return abs(col - center) >= WIDE_COL_THRESHOLD


def col_zone(col, cols=PITCH_COLS):
    """列位置を「中央/ハーフスペース/サイド」の3ゾーンに分類する"""
    center = (cols + 1) // 2
    d = abs(col - center)
    if d >= WIDE_COL_THRESHOLD:
        return "wide"
    if d >= HALF_SPACE_INNER:
        return "halfspace"
    return "center"


def is_halfspace(col, cols=PITCH_COLS):
    return col_zone(col, cols) == "halfspace"


def in_opponent_half(row, attack_dir, rows=105):
    if attack_dir == 1:
        return row > rows / 2
    return row <= rows / 2


def is_in_box(player, attack_dir, cols=PITCH_COLS, rows=105):
    """ボックス内(中央±BOX_HALF_WIDTH かつ相手ゴールから深い位置)に走り込んでいるかどうか"""
    center = (cols + 1) // 2
    if attack_dir == 1:
        deep_enough = player["row"] >= rows - BOX_DEPTH + 1
    else:
        deep_enough = player["row"] <= BOX_DEPTH
    return abs(player["col"] - center) <= BOX_HALF_WIDTH and deep_enough


def choose_cross_target(holder, teammates, attack_dir, rng):
    """ボックス内に走り込んでいる味方の中から、クロスの送り先を選ぶ"""
    hp = (holder["row"], holder["col"])
    center = CENTER_COL
    candidates = []
    for num, p in teammates:
        if not is_in_box(p, attack_dir):
            continue
        d = euclid(hp, (p["row"], p["col"]))
        if d > CROSS_MAX_RANGE or d < 1.0:
            continue
        centrality = BOX_HALF_WIDTH - abs(p["col"] - center)  # ゴール正面に近いほど高評価
        score = centrality - d * 0.05
        candidates.append((score, num, p, d))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:PASS_CANDIDATE_TOP_K]
    min_score = min(c[0] for c in top)
    shift = abs(min_score) + 1.0
    weights = [c[0] + shift for c in top]
    return rng.choices(top, weights=weights, k=1)[0]


def cross_success_probability(holder, target_dist):
    kick = holder["stats"]["kick"]
    vision = holder["stats"]["vision"]
    base = (kick + vision) / 2 / 32.0  # クロスは通常のパスよりやや難度が高い
    base = max(0.25, min(0.85, base))
    dist_penalty = min(0.30, target_dist * CROSS_DIST_PENALTY_COEF)
    return max(0.12, base - dist_penalty)


def choose_cutback_target(holder, teammates, attack_dir, rng):
    """シュートゾーン内でボールを持った際、ボックスへ走り込んでいる味方の中から
    折り返しの送り先を選ぶ(MFへの折り返しを優先的にボーナスして選びやすくする)。"""
    hp = (holder["row"], holder["col"])
    candidates = []
    for num, p in teammates:
        if not is_in_box(p, attack_dir):
            continue
        d = euclid(hp, (p["row"], p["col"]))
        if d > CUTBACK_MAX_RANGE or d < 1.0:
            continue
        score = -d * 0.1
        if p["pos_key"].startswith("MF"):
            score += CUTBACK_MF_BONUS
        candidates.append((score, num, p, d))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:PASS_CANDIDATE_TOP_K]
    min_score = min(c[0] for c in top)
    shift = abs(min_score) + 1.0
    weights = [c[0] + shift for c in top]
    return rng.choices(top, weights=weights, k=1)[0]


def compute_shot_column(holder, rng, cols=PITCH_COLS, spread_mult=1.0):
    """シュートの着弾列(col)を、選手のcol位置を中心に正確性(accuracy)に応じたブレを加えて算出する。
    spread_multを1より大きくすると、ミドルシュートのような遠距離シュートのブレを大きくできる。"""
    acc = holder["stats"]["accuracy"]
    spread = max(2.0, 12.0 - acc * 0.3) * spread_mult  # 正確性が高いほどブレが小さくなる(標準偏差, m)
    offset = rng.gauss(0.0, spread / 2.0)
    col = holder["col"] + offset
    return int(round(max(1, min(cols, col))))


def is_goal_column(col, cols=PITCH_COLS):
    center = (cols + 1) // 2
    return abs(col - center) <= GOAL_ZONE_HALF_WIDTH


def shoot_success_probability(holder, gk):
    kick = holder["stats"]["kick"]
    acc = holder["stats"]["accuracy"]
    gk_acc = gk["stats"]["accuracy"]
    dist = euclid((holder["row"], holder["col"]), (gk["row"], gk["col"]))
    base = (kick * 1.2 + acc) / 40.0
    gk_factor = gk_acc / 25.0
    prob = base - gk_factor * 0.3 + dist * SHOOT_DIST_COEF
    return max(0.05, min(0.6, prob))


def offside_line_row(defenders, attack_dir, rows=105):
    """守備側の「最終ライン」= 自ゴールから2番目に近い選手のrow(通常はGKの次のDF)。"""
    row_list = sorted((p["row"] for _, p in defenders), reverse=(attack_dir == 1))
    if len(row_list) >= 2:
        return row_list[1]
    if row_list:
        return row_list[0]
    return rows if attack_dir == 1 else 1


def is_offside(receiver_pos, passer_pos, defenders, attack_dir, rows=105):
    """パスの瞬間の受け手位置がオフサイドかどうか。
    受け手が(1)敵陣内 (2)最終ラインより前 (3)ボール(パサー)より前、をすべて満たすと成立。"""
    if not OFFSIDE_ENABLED:
        return False
    r_row = receiver_pos[0]
    if not in_opponent_half(r_row, attack_dir, rows):
        return False
    line = offside_line_row(defenders, attack_dir, rows)
    beyond_line = (r_row - line) * attack_dir > ONSIDE_TOLERANCE
    beyond_ball = (r_row - passer_pos[0]) * attack_dir > 0
    return beyond_line and beyond_ball


def choose_through_target(holder, teammates, defenders, attack_dir, rng, rows=105):
    """裏抜けランの受け手を選ぶ。最終ラインの少し手前(オンサイド)で駆け引きしているFWを探し、
    ラインのTHROUGH_RUN_DEPTH裏の地点を走り込み先として返す。
    ハーフスペースのレーンはスルーパスの典型コースとしてボーナスを与える。
    戻り値: (score, num, player, dist, run_pos) or None"""
    line = offside_line_row(defenders, attack_dir, rows)
    hp = (holder["row"], holder["col"])
    candidates = []
    for num, p in teammates:
        if not p["pos_key"].startswith("FW"):
            continue
        gap = (line - p["row"]) * attack_dir  # 正: ラインの手前(オンサイド)にいる
        if gap < 0 or gap > THROUGH_LINE_MARGIN:
            continue
        run_row = max(1, min(rows, line + attack_dir * THROUGH_RUN_DEPTH))
        run_pos = (run_row, p["col"])
        d = euclid(hp, run_pos)
        if d > THROUGH_MAX_RANGE or d < PASS_MIN_DIST:
            continue
        score = 3.0 - gap * 0.1 - d * 0.03
        if is_halfspace(p["col"]) or is_halfspace(holder["col"]):
            score += HALFSPACE_BONUS  # ハーフスペースは裏へのスルーパスの典型レーン
        candidates.append((score, num, p, d, run_pos))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:PASS_CANDIDATE_TOP_K]
    min_score = min(c[0] for c in top)
    shift = abs(min_score) + 1.0
    weights = [c[0] + shift for c in top]
    return rng.choices(top, weights=weights, k=1)[0]


def through_success_probability(holder, target_dist):
    """スルーパスの成功率。視野とキック力に依存し、通常のパスより難度が高い。"""
    kick = holder["stats"]["kick"]
    vision = holder["stats"]["vision"]
    base = (kick * 0.8 + vision * 1.2) / 2 / 32.0
    base = max(0.2, min(0.75, base))
    dist_penalty = min(0.30, target_dist * PASS_DIST_PENALTY_COEF * 1.5)
    return max(0.10, base - dist_penalty)


def choose_gk_distribution(holder, teammates, defenders, rng):
    """GKの配球先を選ぶ。前進度ではなく「フリー度」(受け手の最寄りの相手までの距離)を
    最重視し、相手プレスが片側に寄っていれば逆の空いた方へ自然に散らされる。"""
    hp = (holder["row"], holder["col"])
    candidates = []
    for num, p in teammates:
        pos_key = p["pos_key"]
        if not (pos_key.startswith(GK_DIST_TARGET_PREFIXES) or pos_key in GK_DIST_TARGET_KEYS):
            continue
        pp = (p["row"], p["col"])
        d = euclid(hp, pp)
        if d > GK_DIST_MAX_RANGE or d < PASS_MIN_DIST:
            continue
        _, _, nearest_d = nearest_defender(pp, defenders)
        freeness = min(GK_DIST_FREENESS_CAP, nearest_d if nearest_d is not None else GK_DIST_FREENESS_CAP)
        score = freeness * GK_DIST_FREENESS_COEF - d * 0.02
        candidates.append((score, num, p, d))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:PASS_CANDIDATE_TOP_K]
    min_score = min(c[0] for c in top)
    shift = abs(min_score) + 1.0
    weights = [c[0] + shift for c in top]
    return rng.choices(top, weights=weights, k=1)[0]


def backpass_try_probability(pass_risk, line_height):
    """DFがGKへ戻すことを検討する確率。安全志向(pass_risk低)・リトリート(line_height低)ほど高くなる。"""
    prob = (BACKPASS_TRY_PROB_BASE
            + (1.0 - pass_risk) * BACKPASS_PASSRISK_COEF
            + (-line_height) * BACKPASS_LINE_COEF)
    return max(0.0, min(BACKPASS_TRY_PROB_CAP, prob))


def gk_claim_probability(gk, target_pos, tactic):
    """クロスの着弾点に対し、守備側GKが飛び出してキャッチできる確率。
    press_intensity/line_heightが高い(積極的な)戦術ほど飛び出す範囲が広がる。"""
    dist = euclid((gk["row"], gk["col"]), target_pos)
    reach_mult = max(0.6, min(1.5, 1.0 + tactic["line_height"] * 0.05 + (tactic["press_intensity"] - 1.0) * 0.3))
    effective_range = GK_CLAIM_BASE_RANGE * reach_mult
    if dist > effective_range:
        return 0.0
    base = (effective_range - dist) / effective_range * GK_CLAIM_BASE_PROB
    stat_bonus = (gk["stats"]["accuracy"] - 15) * 0.01
    return max(0.0, min(GK_CLAIM_PROB_CAP, base + stat_bonus))


def mid_shot_success_probability(holder, gk):
    """ミドルシュート(MFの遠距離シュート)の成功率。通常のシュートより距離が明確な
    ペナルティになる点、成功率の上限が低い点が異なる(遠距離ゆえの現実的な低確率)。"""
    kick = holder["stats"]["kick"]
    acc = holder["stats"]["accuracy"]
    gk_acc = gk["stats"]["accuracy"]
    dist = euclid((holder["row"], holder["col"]), (gk["row"], gk["col"]))
    base = (kick * 0.7 + acc * 0.5) / 40.0
    gk_factor = gk_acc / 30.0
    dist_penalty = min(0.35, dist * 0.01)
    prob = base - gk_factor * 0.2 - dist_penalty
    return max(0.03, min(0.30, prob))


def resolve_ball_action(sim, rng):
    """1ステップ分のボールアクション(パス/インターセプト/シュート)を解決する。戻り値はイベント情報のdict。"""
    holder_team, holder_num = sim.ball_holder
    holder_dict = sim.team_a if holder_team == "A" else sim.team_b
    opp_team = "B" if holder_team == "A" else "A"
    opp_dict = sim.team_b if holder_team == "A" else sim.team_a
    holder = holder_dict[holder_num]
    attack_dir = 1 if holder_team == "A" else -1

    holder_tactic = sim.tactics[holder_team]
    opp_tactic = sim.tactics[opp_team]
    pass_risk = holder_tactic["pass_risk"]
    width = holder_tactic["width"]
    press_intensity = opp_tactic["press_intensity"]

    if not hasattr(sim, "_recent_holders"):
        sim._recent_holders = {"A": [], "B": []}
    recent = sim._recent_holders[holder_team]

    def record_holder(team, num):
        hist = sim._recent_holders[team]
        hist.append(num)
        if len(hist) > RECENT_MEMORY:
            hist.pop(0)

    teammates = [(n, p) for n, p in holder_dict.items() if n != holder_num]
    defenders = list(opp_dict.items())

    def resolve_offside(kind, receiver_pos):
        """オフサイド成立時の共通処理: 受け手位置に最も近い守備者のフリーキック(相当)で再開"""
        num_d, p_d, _ = nearest_defender(receiver_pos, defenders)
        new_team = opp_team
        sim.ball_holder = (new_team, num_d)
        record_holder(new_team, num_d)
        return {
            "event": "OFFSIDE",
            "detail": "%s%02d の%sはオフサイド → %s%02d のフリーキックで再開" % (
                holder_team, holder_num, kind, new_team, num_d),
        }

    holder_wide = is_wide(holder)

    # 「2進んで1戻る」用のサイド詰まり状態(チームごと)。同じサイドで前進できない
    # アクションがSWITCH_AFTER_STUCK回続いたら、逆サイドへのパスにボーナスを与える。
    if not hasattr(sim, "_side_state"):
        sim._side_state = {"A": {"side": 0, "count": 0, "best_row": None},
                           "B": {"side": 0, "count": 0, "best_row": None}}
        sim._last_switch_side = {"A": 0, "B": 0}
    st = sim._side_state[holder_team]
    side_off = holder["col"] - CENTER_COL
    holder_side = 1 if side_off >= HALF_SPACE_INNER else (-1 if side_off <= -HALF_SPACE_INNER else 0)

    if holder_side != 0 and holder_side == st["side"]:
        if st["best_row"] is not None and (holder["row"] - st["best_row"]) * attack_dir >= PROGRESS_EPS:
            st["count"] = 0
            st["best_row"] = holder["row"]
        else:
            st["count"] += 1
    else:
        st["side"] = holder_side
        st["count"] = 0
        st["best_row"] = holder["row"]

    switch_side = -st["side"] if (st["side"] != 0 and st["count"] >= SWITCH_AFTER_STUCK) else 0
    sim._last_switch_side[holder_team] = switch_side  # 分析・デバッグ用に公開

    # GKがボールを持っている場合は専用の配球ロジックを使う。前進度ではなくフリー度で
    # 受け手を選ぶため、相手プレスが寄っている側と逆の「空いている」CB/SB/アンカーへ散らされる。
    if holder["pos_key"] == "GK":
        gk_choice = choose_gk_distribution(holder, teammates, defenders, rng)
        if gk_choice is not None:
            g_score, g_num, g_p, g_dist = gk_choice
            g_pos = (g_p["row"], g_p["col"])
            # 受け手はフリー度基準で選ばれている(=近くに相手がいない)ため、
            # 通常のパスより成功しやすい補正を加える(GKの短い配球は現実にも高確率で通る)
            g_succ_prob = min(0.95, pass_success_probability(holder, g_dist) + GK_DIST_SUCC_BONUS)
            g_inter_prob, g_inter_num = intercept_probability(g_pos, defenders, press_intensity=press_intensity)

            roll = rng.random()
            if roll < g_inter_prob:
                new_team = opp_team
                sim.ball_holder = (new_team, g_inter_num)
                record_holder(new_team, g_inter_num)
                return {
                    "event": "INTERCEPT",
                    "detail": "%s01(GK) の配球を %s%02d がインターセプト！攻守交代" % (
                        holder_team, new_team, g_inter_num)
                }

            roll2 = rng.random()
            if roll2 < g_succ_prob:
                sim.ball_holder = (holder_team, g_num)
                record_holder(holder_team, g_num)
                return {
                    "event": "BUILDUP_OK",
                    "detail": "%s01(GK) → %s%02d ビルドアップ配球成功 (成功率%.2f)" % (
                        holder_team, holder_team, g_num, g_succ_prob)
                }
            else:
                num, p, d = pick_recovering_defender(g_pos, defenders, rng, top_k=2)
                new_team = opp_team
                sim.ball_holder = (new_team, num)
                record_holder(new_team, num)
                return {
                    "event": "BUILDUP_FAIL",
                    "detail": "%s01(GK) → %s%02d ビルドアップ配球失敗 (成功率%.2f) → %s%02d がボール回収、攻守交代" % (
                        holder_team, holder_team, g_num, g_succ_prob, new_team, num)
                }
        # 配球先がいない場合は下の通常パス選択にフォールバックする。

    # DFがボールを持っている場合、まずGKへのバックパス(ビルドアップ)を検討する。
    # 通常のパススコアリングは前進度を重視するためGKは実質選ばれないので、独立した分岐にしている。
    if holder["pos_key"].startswith("DF"):
        line_height = holder_tactic["line_height"]
        if rng.random() < backpass_try_probability(pass_risk, line_height):
            gk_self = holder_dict[1]
            bp_pos = (gk_self["row"], gk_self["col"])
            bp_dist = euclid((holder["row"], holder["col"]), bp_pos)
            bp_succ_prob = pass_success_probability(holder, bp_dist)
            bp_inter_prob, bp_inter_num = intercept_probability(bp_pos, defenders, press_intensity=press_intensity)

            roll = rng.random()
            if roll < bp_inter_prob:
                new_team = opp_team
                sim.ball_holder = (new_team, bp_inter_num)
                record_holder(new_team, bp_inter_num)
                return {
                    "event": "INTERCEPT",
                    "detail": "%s%02d のバックパスを %s%02d がインターセプト！攻守交代" % (
                        holder_team, holder_num, new_team, bp_inter_num)
                }

            roll2 = rng.random()
            if roll2 < bp_succ_prob:
                sim.ball_holder = (holder_team, 1)
                record_holder(holder_team, 1)
                return {
                    "event": "BACKPASS_OK",
                    "detail": "%s%02d → %s01(GK) バックパス成功 (成功率%.2f)" % (
                        holder_team, holder_num, holder_team, bp_succ_prob)
                }
            else:
                num, p, d = pick_recovering_defender(bp_pos, defenders, rng, top_k=2)
                new_team = opp_team
                sim.ball_holder = (new_team, num)
                record_holder(new_team, num)
                return {
                    "event": "BACKPASS_FAIL",
                    "detail": "%s%02d → %s01(GK) バックパス失敗 (成功率%.2f) → %s%02d がボール回収、攻守交代" % (
                        holder_team, holder_num, holder_team, bp_succ_prob, new_team, num)
                }

    if in_cross_zone(holder, attack_dir) and holder_wide:
        # サイドの深い位置: シュート角度が悪いので、シュートではなくクロスを試みる。
        cross_try_prob_eff = min(0.9, CROSS_TRY_PROB * pass_risk)
        if rng.random() < cross_try_prob_eff:
            cross_choice = choose_cross_target(holder, teammates, attack_dir, rng)
            if cross_choice is not None:
                c_score, c_num, c_p, c_dist = cross_choice
                c_pos = (c_p["row"], c_p["col"])

                # パスの瞬間の受け手位置でオフサイド判定(最終ラインより前ならクロスは通らない)
                if is_offside(c_pos, (holder["row"], holder["col"]), defenders, attack_dir):
                    return resolve_offside("クロス", c_pos)

                # 通常のインターセプト判定の前に、守備側GKが飛び出してキャッチできるか判定する。
                # 失敗した場合は特別扱いせず、そのまま下の通常のクロス解決へフォールバックする。
                gk_def = opp_dict[1]
                gk_claim_prob = gk_claim_probability(gk_def, c_pos, opp_tactic)
                if rng.random() < gk_claim_prob:
                    sim.ball_holder = (opp_team, 1)
                    record_holder(opp_team, 1)
                    return {
                        "event": "GK_CLAIM",
                        "detail": "%s%02d のクロスに %s01(GK) が飛び出してキャッチ！ (確率%.2f)" % (
                            holder_team, holder_num, opp_team, gk_claim_prob)
                    }

                c_succ_prob = cross_success_probability(holder, c_dist)
                c_inter_prob, c_inter_num = intercept_probability(c_pos, defenders, press_intensity=press_intensity)

                roll = rng.random()
                if roll < c_inter_prob:
                    new_team = opp_team
                    sim.ball_holder = (new_team, c_inter_num)
                    record_holder(new_team, c_inter_num)
                    return {
                        "event": "INTERCEPT",
                        "detail": "%s%02d のクロスを %s%02d がインターセプト！攻守交代" % (
                            holder_team, holder_num, new_team, c_inter_num)
                    }

                roll2 = rng.random()
                if roll2 < c_succ_prob:
                    sim.ball_holder = (holder_team, c_num)
                    record_holder(holder_team, c_num)
                    return {
                        "event": "CROSS_OK",
                        "detail": "%s%02d のクロスが %s%02d に通った (成功率%.2f)" % (
                            holder_team, holder_num, holder_team, c_num, c_succ_prob)
                    }
                else:
                    num, p, d = pick_recovering_defender(c_pos, defenders, rng, top_k=2)
                    new_team = opp_team
                    sim.ball_holder = (new_team, num)
                    record_holder(new_team, num)
                    return {
                        "event": "CROSS_FAIL",
                        "detail": "%s%02d のクロスが合わず(成功率%.2f) → %s%02d がボール回収、攻守交代" % (
                            holder_team, holder_num, c_succ_prob, new_team, num)
                    }
            # ボックス内に走り込んでいる味方がいない場合は、下の通常パス選択にフォールバックする。

    # シュートゾーン内(かつ中央寄り)なら、まずカットバック(ボックス内の味方、MF優先)を検討し、
    # それがなければシュートを試みる（相手GK=背番号1に対して）。pass_riskが高いほど積極的に狙う。
    if in_shoot_zone(holder, attack_dir) and not holder_wide:
        if rng.random() < CUTBACK_TRY_PROB:
            cutback_choice = choose_cutback_target(holder, teammates, attack_dir, rng)
            if cutback_choice is not None:
                cb_score, cb_num, cb_p, cb_dist = cutback_choice
                cb_pos = (cb_p["row"], cb_p["col"])
                if is_offside(cb_pos, (holder["row"], holder["col"]), defenders, attack_dir):
                    return resolve_offside("カットバック", cb_pos)
                cb_succ_prob = pass_success_probability(holder, cb_dist)
                cb_inter_prob, cb_inter_num = intercept_probability(cb_pos, defenders, press_intensity=press_intensity)

                roll = rng.random()
                if roll < cb_inter_prob:
                    new_team = opp_team
                    sim.ball_holder = (new_team, cb_inter_num)
                    record_holder(new_team, cb_inter_num)
                    return {
                        "event": "INTERCEPT",
                        "detail": "%s%02d のカットバックを %s%02d がインターセプト！攻守交代" % (
                            holder_team, holder_num, new_team, cb_inter_num)
                    }

                roll2 = rng.random()
                if roll2 < cb_succ_prob:
                    sim.ball_holder = (holder_team, cb_num)
                    record_holder(holder_team, cb_num)
                    return {
                        "event": "CUTBACK_OK",
                        "detail": "%s%02d のカットバックが %s%02d に通った (成功率%.2f)" % (
                            holder_team, holder_num, holder_team, cb_num, cb_succ_prob)
                    }
                else:
                    num, p, d = pick_recovering_defender(cb_pos, defenders, rng, top_k=2)
                    new_team = opp_team
                    sim.ball_holder = (new_team, num)
                    record_holder(new_team, num)
                    return {
                        "event": "CUTBACK_FAIL",
                        "detail": "%s%02d のカットバックが合わず(成功率%.2f) → %s%02d がボール回収、攻守交代" % (
                            holder_team, holder_num, cb_succ_prob, new_team, num)
                    }
            # ボックス内に走り込んでいる味方がいない場合は、下のシュートへフォールバックする。

        shoot_try_prob_eff = min(0.9, SHOOT_TRY_PROB * pass_risk)
        if rng.random() < shoot_try_prob_eff:
            shot_col = compute_shot_column(holder, rng)
            gk = opp_dict[1]

            if not is_goal_column(shot_col):
                new_team = opp_team
                sim.ball_holder = (new_team, 1)
                record_holder(new_team, 1)
                return {
                    "event": "SHOT_OFF_TARGET",
                    "detail": "%s%02d のシュートは枠外(狙った列=%d、ゴールエリア列=%d〜%d) → %s01(GK)ボール保持" % (
                        holder_team, holder_num, shot_col,
                        CENTER_COL - GOAL_ZONE_HALF_WIDTH, CENTER_COL + GOAL_ZONE_HALF_WIDTH, new_team),
                }

            succ_prob = shoot_success_probability(holder, gk)
            if rng.random() < succ_prob:
                record_holder(holder_team, holder_num)
                return {
                    "event": "GOAL",
                    "detail": "%s%02d がシュート！(着弾列=%d) ゴール！！ (成功率%.2f)" % (
                        holder_team, holder_num, shot_col, succ_prob),
                    "scoring_team": holder_team,
                }
            else:
                new_team = opp_team
                sim.ball_holder = (new_team, 1)
                record_holder(new_team, 1)
                return {
                    "event": "SHOT_SAVED",
                    "detail": "%s%02d のシュート(着弾列=%d)を %s01(GK) がセーブ (成功率%.2f) → 攻守交代" % (
                        holder_team, holder_num, shot_col, new_team, succ_prob),
                }

    # シュートゾーンには届かないがアタッキングサード内のMFは、低確率でミドルシュートを試みる。
    elif in_mid_shoot_zone(holder, attack_dir) and not holder_wide and holder["pos_key"].startswith("MF"):
        mid_shot_try_prob_eff = min(0.9, MID_SHOT_TRY_PROB * pass_risk)
        if rng.random() < mid_shot_try_prob_eff:
            shot_col = compute_shot_column(holder, rng, spread_mult=MID_SHOT_COL_SPREAD_MULT)
            gk = opp_dict[1]

            if not is_goal_column(shot_col):
                new_team = opp_team
                sim.ball_holder = (new_team, 1)
                record_holder(new_team, 1)
                return {
                    "event": "SHOT_OFF_TARGET",
                    "detail": "%s%02d のミドルシュートは枠外(狙った列=%d、ゴールエリア列=%d〜%d) → %s01(GK)ボール保持" % (
                        holder_team, holder_num, shot_col,
                        CENTER_COL - GOAL_ZONE_HALF_WIDTH, CENTER_COL + GOAL_ZONE_HALF_WIDTH, new_team),
                }

            succ_prob = mid_shot_success_probability(holder, gk)
            if rng.random() < succ_prob:
                record_holder(holder_team, holder_num)
                return {
                    "event": "GOAL",
                    "detail": "%s%02d がミドルシュート！(着弾列=%d) ゴール！！ (成功率%.2f)" % (
                        holder_team, holder_num, shot_col, succ_prob),
                    "scoring_team": holder_team,
                }
            else:
                new_team = opp_team
                sim.ball_holder = (new_team, 1)
                record_holder(new_team, 1)
                return {
                    "event": "SHOT_SAVED",
                    "detail": "%s%02d のミドルシュート(着弾列=%d)を %s01(GK) がセーブ (成功率%.2f) → 攻守交代" % (
                        holder_team, holder_num, shot_col, new_team, succ_prob),
                }

    # 敵陣までボールを運んだら、最終ライン裏へのスルーパス(裏抜けラン)を狙う。
    # 受け手はラインの手前で駆け引きしているFW。成功すれば受け手がライン裏に走り込んだ
    # 状態でボールを持ち、一気にシュートチャンスになる。飛び出しが早すぎればオフサイド。
    advance = holder["row"] if attack_dir == 1 else (106 - holder["row"])
    if advance >= THROUGH_MIN_ADVANCE and not in_shoot_zone(holder, attack_dir):
        if rng.random() < min(0.9, THROUGH_TRY_PROB * pass_risk):
            th_choice = choose_through_target(holder, teammates, defenders, attack_dir, rng)
            if th_choice is not None:
                t_score, t_num, t_p, t_dist, run_pos = th_choice

                if rng.random() < THROUGH_MISTIME_PROB:
                    return resolve_offside("スルーパス(飛び出しが早すぎた)", (t_p["row"], t_p["col"]))

                t_succ_prob = through_success_probability(holder, t_dist)
                t_inter_prob, t_inter_num = intercept_probability(run_pos, defenders, press_intensity=press_intensity)

                roll = rng.random()
                if roll < t_inter_prob:
                    new_team = opp_team
                    sim.ball_holder = (new_team, t_inter_num)
                    record_holder(new_team, t_inter_num)
                    return {
                        "event": "INTERCEPT",
                        "detail": "%s%02d のスルーパスを %s%02d がインターセプト！攻守交代" % (
                            holder_team, holder_num, new_team, t_inter_num)
                    }

                roll2 = rng.random()
                if roll2 < t_succ_prob:
                    # 受け手が最終ラインの裏へ走り込んでボールを受ける(位置も実際に動かす)
                    t_p["row"], t_p["col"] = run_pos
                    sim.ball_holder = (holder_team, t_num)
                    record_holder(holder_team, t_num)
                    return {
                        "event": "THROUGH_OK",
                        "detail": "%s%02d のスルーパスで %s%02d がライン裏へ抜け出した！ (成功率%.2f)" % (
                            holder_team, holder_num, holder_team, t_num, t_succ_prob)
                    }
                else:
                    num, p, d = pick_recovering_defender(run_pos, defenders, rng, top_k=2)
                    new_team = opp_team
                    sim.ball_holder = (new_team, num)
                    record_holder(new_team, num)
                    return {
                        "event": "THROUGH_FAIL",
                        "detail": "%s%02d のスルーパスが合わず(成功率%.2f) → %s%02d がボール回収、攻守交代" % (
                            holder_team, holder_num, t_succ_prob, new_team, num)
                    }
            # 裏抜け候補がいない場合は下の通常パス選択にフォールバックする。

    choice = choose_pass_target(holder, teammates, attack_dir, recent, rng,
                                pass_risk=pass_risk, width=width, switch_side=switch_side)

    if choice is None:
        record_holder(holder_team, holder_num)
        return {"event": "HOLD", "detail": "%s%02d がボールを保持（パス候補なし）" % (holder_team, holder_num)}

    score, target_num, target_p, dist = choice
    target_pos = (target_p["row"], target_p["col"])

    # 通常のパスもパスの瞬間の受け手位置でオフサイド判定
    if is_offside(target_pos, (holder["row"], holder["col"]), defenders, attack_dir):
        return resolve_offside("パス", target_pos)

    succ_prob = pass_success_probability(holder, dist)
    inter_prob, inter_num = intercept_probability(target_pos, defenders, press_intensity=press_intensity)

    roll = rng.random()
    if roll < inter_prob:
        new_team = opp_team
        sim.ball_holder = (new_team, inter_num)
        record_holder(new_team, inter_num)
        return {
            "event": "INTERCEPT",
            "detail": "%s%02d→%s%02d へのパスを %s%02d がインターセプト！攻守交代" % (
                holder_team, holder_num, target_p["team"], target_num, new_team, inter_num)
        }

    roll2 = rng.random()
    if roll2 < succ_prob:
        sim.ball_holder = (holder_team, target_num)
        record_holder(holder_team, target_num)
        return {
            "event": "PASS_OK",
            "detail": "%s%02d → %s%02d パス成功 (成功率%.2f)" % (
                holder_team, holder_num, holder_team, target_num, succ_prob)
        }
    else:
        num, p, d = pick_recovering_defender(target_pos, defenders, rng, top_k=2)
        new_team = opp_team
        sim.ball_holder = (new_team, num)
        record_holder(new_team, num)
        return {
            "event": "PASS_FAIL",
            "detail": "%s%02d → %s%02d パス失敗 (成功率%.2f) → %s%02d がボール回収、攻守交代" % (
                holder_team, holder_num, holder_team, target_num, succ_prob, new_team, num)
        }
