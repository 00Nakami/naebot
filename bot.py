import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from discord import Embed, Interaction
import random
import json
import os
from dotenv import load_dotenv
import asyncio

# --- 環境変数 ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKENが.envに設定されていません")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- データファイル ---
STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for user_id, stats in data.items():
                stats.setdefault("streak", 0)
                stats.setdefault("max_streak", 0)
                stats.setdefault("lose_streak", 0)
                stats.setdefault("max_lose_streak", 0)
                stats.setdefault("draw_streak", 0)
                stats.setdefault("max_draw_streak", 0)
            return data
    return {}

def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

stats = load_stats()

# --- ログイン時処理 ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ ログイン完了: {bot.user}")
    print("✅ スラッシュコマンド同期済み")

# ===================== #
# ==== じゃんけん ==== #
# ===================== #

JANKEN_CHOICES = ["ぐー", "ちょき", "ぱー"]

def judge(player, bot_hand):
    if player == bot_hand:
        return "draw"
    elif (player == "ぐー" and bot_hand == "ちょき") or \
         (player == "ちょき" and bot_hand == "ぱー") or \
         (player == "ぱー" and bot_hand == "ぐー"):
        return "win"
    else:
        return "lose"

def get_win_quote(streak):
    if streak >= 5:
        return random.choice([
            f"{streak}連勝とかやばなえすぎやは！",
            "チートナイスーꉂ🤭",
            "絶対チートやんけ！"
        ])
    elif streak >= 3:
        return random.choice([
            f"{streak}連勝はやばなえ",
            "ずるしてるやんけ！",
            "わざと負けてあげましたꉂ🤭"
        ])
    else:
        return random.choice([
            "なんでこれで負けるねん！",
            "手加減してあげてたんよな〜ꉂ🤭",
            "たまたま勝ってなんやねん"
        ])

BOT_QUOTES = {
    "lose": [
        "よゆなえでくさなえꉂ🤭",
        "これはよゆなえこえてなーじーꉂ🤭",
        "いーじーなーじーやなー、"
    ],
    "draw": [
        "つぎはぼこなえにしてやるかーꉂ🤭",
        "ぼこなえにしてやるかー、",
        "引きなえかなー、"
    ]
}

@bot.tree.command(name="janken", description="じゃんけんするなえ！（ぐー・ちょき・ぱー）")
@app_commands.describe(hand="あなたの手を選んでください")
@app_commands.choices(hand=[
    app_commands.Choice(name="ぐー ✊", value="ぐー"),
    app_commands.Choice(name="ちょき ✌️", value="ちょき"),
    app_commands.Choice(name="ぱー ✋", value="ぱー")
])
async def janken(interaction: discord.Interaction, hand: app_commands.Choice[str]):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.InteractionResponded:
        pass  # すでに応答済みなら無視

    user_id = str(interaction.user.id)
    user_hand = hand.value
    bot_hand = random.choice(JANKEN_CHOICES)
    result = judge(user_hand, bot_hand)

    if user_id not in stats:
        stats[user_id] = {
            "win": 0, "lose": 0, "draw": 0,
            "streak": 0, "max_streak": 0,
            "lose_streak": 0, "max_lose_streak": 0,
            "draw_streak": 0, "max_draw_streak": 0,
        }

    stats[user_id][result] += 1

    if result == "win":
        stats[user_id]["streak"] += 1
        stats[user_id]["max_streak"] = max(stats[user_id]["max_streak"], stats[user_id]["streak"])
        stats[user_id]["lose_streak"] = 0
        stats[user_id]["draw_streak"] = 0
    elif result == "lose":
        stats[user_id]["lose_streak"] += 1
        stats[user_id]["max_lose_streak"] = max(stats[user_id]["max_lose_streak"], stats[user_id]["lose_streak"])
        stats[user_id]["streak"] = 0
        stats[user_id]["draw_streak"] = 0
    else:
        stats[user_id]["draw_streak"] += 1
        stats[user_id]["max_draw_streak"] = max(stats[user_id]["max_draw_streak"], stats[user_id]["draw_streak"])
        stats[user_id]["streak"] = 0
        stats[user_id]["lose_streak"] = 0

    save_stats()

    bot_comment = (
        get_win_quote(stats[user_id]["streak"]) if result == "win"
        else random.choice(BOT_QUOTES[result])
    )

    result_text = {
        "win": "あなたの勝ち！ 🎉",
        "lose": "あなたの負け… 💔",
        "draw": "あいこ！ 🤝"
    }

    await interaction.followup.send(
        f"🧍‍♂️ あなたの手: {user_hand}\n"
        f"🐧 なえくんBotの手: {bot_hand}\n"
        f"🎲 結果: {result_text[result]}\n"
        f"🔥 現在の連勝数: {stats[user_id]['streak']}回\n"
        f"💬 なえくんBot: {bot_comment}"
    )

@bot.tree.command(name="janken_stats", description="あなたのじゃんけん戦績を表示します")
async def janken_stats(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.InteractionResponded:
        pass

    user_id = str(interaction.user.id)
    user_stats = stats.get(user_id, {
        "win": 0, "lose": 0, "draw": 0,
        "streak": 0, "max_streak": 0,
        "lose_streak": 0, "max_lose_streak": 0,
        "draw_streak": 0, "max_draw_streak": 0,
    })
    total = user_stats["win"] + user_stats["lose"] + user_stats["draw"]

    if total == 0:
        await interaction.followup.send("📊 まだ対戦履歴がありません！ `/janken` で遊んでみよう！")
        return

    win_rate = (user_stats["win"] / (user_stats["win"] + user_stats["lose"]) * 100) if (user_stats["win"] + user_stats["lose"]) > 0 else 0.0

    await interaction.followup.send(
        f"📊 **{interaction.user.name}さんのじゃんけん戦績**\n"
        f"✅ 勝ち: {user_stats['win']}回\n"
        f"❌ 負け: {user_stats['lose']}回\n"
        f"🤝 あいこ: {user_stats['draw']}回\n"
        f"🔥 現在の連勝数: {user_stats['streak']}回\n"
        f"🏆 最高連勝数: {user_stats['max_streak']}回\n"
        f"☠️ 最高連敗数: {user_stats['max_lose_streak']}回\n"
        f"🤝 最高連続あいこ数: {user_stats['max_draw_streak']}回\n"
        f"🎯 勝率: {win_rate:.1f}%（全{total}回）"
    )

@bot.tree.command(name="janken_ranking", description="じゃんけんのランキングを表示するなえ！")
async def janken_ranking(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
    except discord.errors.InteractionResponded:
        pass

    ranked_stats = []

    for user_id, s in stats.items():
        ranked_stats.append({
            "id": user_id,
            "win": s.get("win", 0),
            "max_streak": s.get("max_streak", 0),
            "max_lose_streak": s.get("max_lose_streak", 0),
            "max_draw_streak": s.get("max_draw_streak", 0),
        })

    async def format_ranking(title, key):
        sorted_list = sorted(ranked_stats, key=lambda x: x[key], reverse=True)[:3]
        if not sorted_list:
            return f"**{title}**\n（データがありません）"
        lines = [f"**{title}**"]
        for i, entry in enumerate(sorted_list, 1):
            try:
                user = await bot.fetch_user(int(entry["id"]))
                value = entry[key]
                lines.append(f"{i}. {user.name} - {value}回")
            except Exception:
                continue
        return "\n".join(lines)

    win_ranking = await format_ranking("🏆 勝利数ランキング", "win")
    streak_ranking = await format_ranking("🔥 最高連勝ランキング", "max_streak")
    lose_ranking = await format_ranking("☠️ 最高連敗ランキング", "max_lose_streak")
    draw_ranking = await format_ranking("🤝 最高連続あいこランキング", "max_draw_streak")

    await interaction.followup.send(
        f"{win_ranking}\n\n{streak_ranking}\n\n{lose_ranking}\n\n{draw_ranking}"
    )

# --- おみくじ ---
@bot.tree.command(name="naemikuji", description="なえみくじ引いて行くなえ？")
async def omikuji(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.InteractionResponded:
        pass

    results = ["大苗 🎉", "中苗 😊", "苗 🙂", "小苗 😌", "末苗 😐", "狐 😢", "大狐 😱"]
    choice = random.choice(results)
    await interaction.followup.send(f"🎋 {interaction.user.mention} さんのなえみくじ結果は **{choice}** なえ〜")

# --- Bedwarskit ---
@bot.tree.command(name="bedwarskit", description="なえくんがおすすめのキットを言うなえ！")
async def bedwarskit(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.InteractionResponded:
        pass

    kits = [
        "ノーキット", "ランダム", "アデトゥンデ", "アグニ", "サンショウウオのエーミーさん", "ベグザット",
        "サイバー", "へファイストス", "灼熱のシールダー", "クリスタル", "リアン", "ルーメンちゃん",
        "メロディ", "Nahla", "海賊のデイビー", "スティクス", "タリヤ", "トリクシー", "ウマ",
        "ヴァネッサ", "虚空の騎士", "ささやき", "レン", "ゼノ（魔法使い）", "ベイカー", "ヤバン人",
        "ルシア", "ナザール", "イザベル", "マルセル", "マーティン", "ラグナー", "Ramil", "アラクネ",
        "エンバー", "アーチャー", "ビルダー", "遺体安置所", "デス・アダー", "エルダー・ツリー",
        "エルドリック", "エベリン", "農家のクリタス", "フレーヤ", "死神", "グローブ", "ハンナ",
        "カイダ", "ラシー", "ライラ", "マリーナ", "ミロ", "マイナー", "シェイラ", "シグリッド",
        "サイラス", "スコル", "トリニティ", "トライトン", "ヴォイドリージェント", "バルカン",
        "ユジ", "ゼニス", "エアリー", "錬金術師", "アレース", "養蜂家のビートリックスさん", "賞金稼ぎ",
        "ケイトリン", "コバルト", "コグスワース", "征服者", "ワニオオカミ", "きょうりゅう手なずけ師のドム",
        "ドリル", "エレクトラ", "漁師", "フローラ", "フォルトゥナ", "フロスティ", "ジンジャーブレッドマン",
        "ゴンビイさん", "イグニス", "ジャック", "ジェイド", "カライヤちゃん", "ラニ", "商人のマルコさん",
        "メタルディテクターさん", "ノエル", "ニョカ", "ニュクス", "パイロキネシス", "からす", "サンタ",
        "羊飼い", "スモーク", "スピリットキャッチャーさん", "スターコレクターのステラちゃん", "テラ",
        "トラッパー", "ウンブラ", "梅子", "ウォーデン", "戦士", "ウィムさん", "シューロット", "ヤミニ",
        "イエティ", "ゼファー"
    ]
    choice = random.choice(kits)
    await interaction.followup.send(f"💯 {interaction.user.mention} さんにおすすめのキットは **{choice}** なえ〜！")

# --- 計算 ---
@bot.tree.command(name="sansuu", description="整数の計算をするなえ！")
@app_commands.describe(
    a="整数1つ目なえ",
    b="整数2つ目なえ",
    op="演算子を選ぶなえ〜"
)
@app_commands.choices(op=[
    app_commands.Choice(name="足し算（+）", value="+"),
    app_commands.Choice(name="引き算（-）", value="-"),
    app_commands.Choice(name="掛け算（×）", value="×"),
    app_commands.Choice(name="割り算（÷）", value="÷"),
])
async def calc(interaction: discord.Interaction, a: int, b: int, op: app_commands.Choice[str]):
    try:
        await interaction.response.defer()
    except discord.errors.InteractionResponded:
        pass

    try:
        if op.value == "+":
            res = a + b
        elif op.value == "-":
            res = a - b
        elif op.value == "×":
            res = a * b
        elif op.value == "÷":
            if b == 0:
                await interaction.followup.send("❌ 0で割るのはできなえ！")
                return
            quotient = a // b
            remainder = a % b
            await interaction.followup.send(f"{a} ÷ {b} = {quotient} あまり {remainder}")
            return
        else:
            await interaction.followup.send("❌ 不正な演算子なえ！")
            return
    except Exception as e:
        await interaction.followup.send(f"❌ エラーが発生したなえ: {e}")
        return

    await interaction.followup.send(f"{a} {op.value} {b} = {res}")

# --- スロット ---
class SlotView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.emojis = ["🐧", "🍒", "🔔", "🦊"]
        self.running = False
        self.message = None

    async def slot_animation(self, interaction: Interaction):
        self.running = True
        final_slots = [None, None, None]
        slots = [random.choice(self.emojis) for _ in range(3)]

        embed = Embed(title="スロットマシン", description="🎰 回転中...", color=discord.Color.gold())
        embed.add_field(name="結果", value=" ".join(slots), inline=False)

        if self.message is None:
            self.message = await interaction.original_response()

        for stop_index in range(3):
            for _ in range(10):
                for i in range(3):
                    if i <= stop_index:
                        if final_slots[i] is None:
                            final_slots[i] = random.choice(self.emojis)
                        slots[i] = final_slots[i]
                    else:
                        slots[i] = random.choice(self.emojis)

                embed.set_field_at(0, name="結果", value=" ".join(slots), inline=False)
                await self.message.edit(embed=embed, view=self)
                await asyncio.sleep(0.02)

        if final_slots[0] == final_slots[1] == final_slots[2]:
            result_msg = f"🎉 大当たり！ {''.join(final_slots)} が揃ったなえ！"
        elif final_slots[0] == final_slots[1] or final_slots[1] == final_slots[2] or final_slots[0] == final_slots[2]:
            result_msg = f"🙂 小当たり！ {''.join(final_slots)} のペアが揃ったなえ！"
        else:
            result_msg = f"😢 残念！ {''.join(final_slots)} はハズレなえ…"

        embed.description = result_msg
        await self.message.edit(embed=embed, view=None)
        self.running = False

    @discord.ui.button(label="回す", style=discord.ButtonStyle.green)
    async def spin(self, interaction: Interaction, button: Button):
        if self.running:
            await interaction.response.send_message("⚠️ もう回ってるなえ！少しまってなえ！", ephemeral=True)
            return
        await interaction.response.defer()
        await self.slot_animation(interaction)

@bot.tree.command(name="slot", description="スロットを回すなえ！")
async def slot(interaction: discord.Interaction):
    view = SlotView()
    embed = Embed(title="スロットマシン", description="🎰 ボタンを押してスロットを回すなえ！", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=view)

# --- 実行 ---
bot.run(DISCORD_TOKEN)
