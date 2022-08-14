import asyncio
import datetime
import json
import os
import random
import re
import traceback
from PIL import Image, ImageDraw, ImageFont

import discord
import requests
from discord.ext import tasks

os.chdir(os.path.dirname(os.path.abspath(__file__)))
client = discord.Client(intents=discord.Intents.all())

about_bingo = [] #[datetime.datetime, discord.Message, bool, discord.Member × n]

@client.event
async def on_ready():
    print(f"{client.user.name}がログインしました")


def unexpected_error(msg=None):
    """
    予期せぬエラーが起きたときの対処
    エラーメッセージ全文と発生時刻を通知"""

    try:
        if msg is not None:
            content = (
                f"{msg.author}\n"
                f"{msg.content}\n"
                f"{msg.channel.name}\n"
            )
        else:
            content = ""
    except:
        unexpected_error()
        return

    error_notice_webhook_url = os.getenv("error_notice_webhook")
    now = datetime.datetime.now().strftime("%H:%M") #今何時？
    error_msg = f"```\n{traceback.format_exc()}```" #エラーメッセージ全文
    error_content = {
        "content": "<@523303776120209408>", #けいにメンション
        "avatar_url": "https://cdn.discordapp.com/attachments/644880761081561111/703088291066675261/warning.png",
        "embeds": [ #エラー内容・発生時間まとめ
            {
                "title": "エラーが発生しました",
                "description": content + error_msg,
                "color": 0xff0000,
                "footer": {
                    "text": now
                }
            }
        ]
    }
    requests.post(error_notice_webhook_url, json.dumps(error_content), headers={"Content-Type": "application/json"}) #エラーメッセをウェブフックに投稿


@client.event
async def on_message(message):
    try:
        if message.content == "!bingo":
            if len(about_bingo) != 0:
                await message.channel.send("現在募集中またはプレイ中です(仮機能、募集中とプレイ中に分ける)")
                return

            about_bingo.append(datetime.datetime.now())
            embed = discord.Embed(
                title="BINGO募集",
                description=f"{message.author.mention}",
                color=random.choice([0x0000ff, 0x00aa00, 0xff0000, 0xffff00])
            )
            msg = await message.channel.send(content="✋で参加、👋で退出、🆗で開始```リアクションが全て付いてからアクションを行ってください\nメッセージ系タイムアウト1分, リアクション系タイムアウト30秒", embed=embed)
            about_bingo.append(msg)
            await msg.add_reaction("✋")
            await msg.add_reaction("👋")
            await msg.add_reaction("🆗")

            about_bingo.append(False) #プレイ中のフラグ
            about_bingo.append(message.author)

    except:
        unexpected_error()


async def calc_bet(channel, author):
    try:
        while True:
            def check2(m):
                return m.channel == channel and m.author == author

            try:
                reply = await client.wait_for("message", check=check2, timeout=60)
            except asyncio.TimeoutError:
                await channel.send(f"{author.mention} あくしろよ")
            else:
                rep = reply.content.lower()
                rep = rep.replace("lc", "*3456").replace("sb", "*1728").replace("c", "*1728").replace("st", "*64").replace("個", "")
                p = re.compile(r"^[0-9 +*.]+$")
                if p.fullmatch(rep):
                    try:
                        result = eval(rep)
                    except (SyntaxError, NameError, OverflowError, TypeError):
                        await channel.send("不正な入力です")
                    else:
                        try:
                            LC, st = divmod(result, 3456)
                            st, ko = divmod(st, 64)
                        except (TypeError):
                            await channel.send("変な入力するんじゃねぇ！")
                        else:
                            LC = int(LC)
                            st = int(st)
                            ko = int(ko)
                            result_list = []
                            if LC != 0:
                                result_list.append(f"{LC}LC")
                            if st != 0:
                                result_list.append(f"{st}st")
                            if ko != 0:
                                result_list.append(f"{ko}個")
                            result_str = " + ".join(result_list)
                            if result_str == "":
                                result_str = "0"
                            break

                else: #p.fullmatch(msg)に対応
                    await channel.send("使える文字は半角数字, ., +, LC, SB, C, st, 個のみです")

        result = int(result)
        return result_str, result

    except:
        unexpected_error()


def calc_stack(kosuu):
    LC, st = divmod(kosuu, 3456)
    st, ko = divmod(st, 64)

    LC = int(LC)
    st = int(st)
    ko = int(ko)
    result_list = []
    if LC != 0:
        result_list.append(f"{LC}LC")
    if st != 0:
        result_list.append(f"{st}st")
    if ko != 0:
        result_list.append(f"{ko}個")
    result_str = " + ".join(result_list)
    if result_str == "":
        result_str = "0"
    return result_str


def create_pic(bingo_list):
    background = Image.new(mode="RGB", size=(250, 250), color=0xffffff)
    buried = Image.open("buried.png")
    font = ImageFont.truetype("./UDDigiKyokashoN-R.ttc", size=32)
    for x in range(5):
        for y in range(5):
            if bingo_list[x][y] == 0:
                background.paste(buried, (x*50, y*50))
            else:
                void = Image.open("void.png")
                moji = ImageDraw.Draw(void)
                if bingo_list[x][y] < 10:
                    moji.text((16, 9), text=f"{bingo_list[x][y]}", font=font, fill=0x000000)
                else:
                    moji.text((9, 9), text=f"{bingo_list[x][y]}", font=font, fill=0x000000)
                background.paste(void, (x*50, y*50))

    background.save("bingo.png")


async def decide_oya(channel):
    try:
        await channel.send("親になりたい人は「b!oya」を入力してください(コマンド変える？リアクションにする？)")

        def check1(m):
            return m.channel == channel and m.content == "b!oya" and (m.author in about_bingo[3:])

        reply = await client.wait_for("message",check=check1)
        oya = reply.author
        await channel.send(f"{oya.name}さんが親です")

    except:
        unexpected_error()

    await decide_max_bet(channel, oya)


async def decide_max_bet(channel, oya):
    try:
        await channel.send(f"{oya.mention}さん、bet額上限を入力してください(1st=64個のアイテムが前提のプログラムです)\n半角数字と小数点, +, LC, SB, C, st, 個, 単位無しが使用できます\n計算結果に小数点が発生した場合適当に切り捨てられます、正確性は保証しません")
        max_bet_str, max_bet = await calc_bet(channel, oya)
        await channel.send(f"bet額上限は{max_bet_str} ({max_bet}個)です")

    except:
        unexpected_error()

    await children_bet(channel, oya, max_bet, max_bet_str)


async def children_bet(channel, oya, max_bet, max_bet_str):
    try:
        player_list = about_bingo[3:]
        children_list = []
        for player in player_list:
            if player != oya:
                children_list.append(player)

        bet_dict = {}
        for mem in children_list:
            await channel.send(f"{mem.mention}さん、bet額を入力してください\n上限は{max_bet_str} ({max_bet}個)です\n半角数字と小数点, +, LC, SB, C, st, 個, 単位無しが使用できます\n計算結果に小数点が発生した場合適当に切り捨てられます、正確性は保証しません")
            while True:
                bet_str, bet = await calc_bet(channel, mem)
                if bet > max_bet:
                    await channel.send("入力しなおしてください。上限より多い額を賭けています")
                elif bet < 0:
                    await channel.send("入力しなおしてください。負の数を入力しています、賭けなしでプレイする場合0と入力してください")
                else:
                    bet_dict[mem.id] = bet
                    await channel.send(f"{mem.name}さんのbet額を{bet_str} ({bet}個)で受け付けました")
                    break

    except:
        unexpected_error()

    await match_bingo(channel, oya, bet_dict, player_list, children_list, max_bet, max_bet_str)


async def match_bingo(channel, oya, bet_dict, player_list, children_list, max_bet, max_bet_str):
    try:
        bingo_card_dict = {}
        for mem in player_list:
            bingo_list = []
            for i in range(5):
                col = list(range(i*15+1, i*15+16))
                col = random.sample(col, k=5)
                bingo_list.append(col)
            bingo_list[2][2] = 0
            bingo_card_dict[mem.id] = bingo_list
            create_pic(bingo_list)
            f = discord.File("./bingo.png")
            try:
                await mem.send(file=f)
            except discord.errors.Forbidden:
                await channel.send(f"{mem.mention} DMの送信に失敗しました、DMの開放をお願いします。ゲームを終了します(いずれその人を抜いて継続できるようにする)")
                return

        await channel.send("ビンゴカードを全員のDMに配布しました。")

        n = 1
        bingoed_mem_dict = {}
        not_bingo_mem_list = []
        not_bingo_mem_list.append(oya)
        for mem in children_list:
            not_bingo_mem_list.append(mem)
        while True: #全体ループ
            temp_bingoed_mem_list = []
            for mem in not_bingo_mem_list: #1ループ
                if not mem in temp_bingoed_mem_list:
                    for mem_3 in player_list:
                        if mem != mem_3:
                            await mem_3.send(f"{mem.name}さんの番です")
                    await channel.send(f"{mem.name}さんの番です")
                    create_pic(bingo_card_dict[mem.id])
                    f = discord.File("bingo.png")
                    await mem.send(content="あなたの番です", file=f)
                    flag = False
                    timeout_pass = False
                    while True: #適切な入力がされるかタイムアウトするまでループ
                        def check2(m):
                            return m.author == mem and (m.channel == channel or m.channel == mem.dm_channel)

                        try:
                            reply = await client.wait_for("message", check=check2, timeout=60)
                        except asyncio.TimeoutError:
                            await mem.send("あなたはタイムアウトによりパスとなりました")
                            for mem_3 in player_list:
                                if mem != mem_3:
                                    await mem_3.send(f"{mem.name}さんはタイムアウトによりパスしました")
                            await channel.send(f"{mem.name}さんはタイムアウトによりパスしました")
                            timeout_pass = True
                            flag = True
                        else:
                            try:
                                select_num = int(reply.content)
                            except ValueError:
                                await channel.send("入力しなおしてください。1~75の半角数字を入力してください")
                            else:
                                if select_num >= 1 and select_num <= 75:
                                    flag = True
                                    break
                                else:
                                    await mem.send("入力しなおしてください。1~75の整数を半角数字で入力してください")

                        if flag: #適切な入力がされるかタイムアウトしたらbreak
                            break

                    #ビンゴ判定等の処理
                    if not timeout_pass:
                        for mem_3 in player_list:
                            if mem != mem_3:
                                await mem_3.send(f"{mem.name}さんは{select_num}を選択しました")
                        await channel.send(f"{mem.name}さんは{select_num}を選択しました")

                        for mem_2 in not_bingo_mem_list:
                            bingo_list = bingo_card_dict[mem_2.id]
                            changed = False
                            for x in range(5):
                                for y in range(5):
                                    if bingo_list[x][y] == select_num: #選択された数字があったら穴をあける
                                        bingo_list[x][y] = 0
                                        changed = True
                                        break

                            if changed:
                                bingoed = False
                                for col in bingo_list:
                                    if sum(col) == 0: #縦列の判定
                                        bingoed = True
                                        break

                                if not bingoed:
                                    for y in range(5):
                                        sum_raw = 0
                                        for x in range(5):
                                            sum_raw += bingo_list[x][y]
                                            if sum_raw != 0: #0でないならもう調べる必要がないのでbreak
                                                break

                                        if sum_raw == 0: #横列の判定
                                            bingoed = True
                                            break

                                if not bingoed:
                                    if (bingo_list[0][4] + bingo_list[1][3] + bingo_list[2][2] + bingo_list[3][1] + bingo_list[4][0]) == 0 or\
                                        (bingo_list[0][0] + bingo_list[1][1] + bingo_list[2][2] + bingo_list[3][3] + bingo_list[4][4]) == 0: #斜めの判定
                                        bingoed = True

                                create_pic(bingo_list)
                                f = discord.File("bingo.png")
                                if bingoed:
                                    bingoed_mem_dict[mem_2.id] = n
                                    temp_bingoed_mem_list.append(mem_2)

                                    await mem_2.send(content="ビンゴ達成！", file=f)
                                    for mem_3 in player_list:
                                        if mem_3 != mem_2:
                                            await mem_3.send(f"{mem_2.name}さんがビンゴ達成！")
                                    await channel.send(f"{mem_2.name}さんがビンゴ達成！")

                                else:
                                    await mem_2.send(file=f)

            for mem_4 in temp_bingoed_mem_list:
                try:
                    not_bingo_mem_list.remove(mem_4)
                except ValueError:
                    pass

            n += 1

            if len(not_bingo_mem_list) == 0:
                for mem_2 in player_list:
                    await mem_2.send(f"全員ビンゴ達成！{channel.mention}")
                await channel.send("全員ビンゴ達成！")
                await channel.send(f"{bingoed_mem_dict}")
                break

        finish_min = min(bingoed_mem_dict.values()) #最小の手数
        finish_max = max(bingoed_mem_dict.values()) #最大の手数
        #仕様
        #親だけが最速で上がる→全員から2倍貰う
        #親だけがビリ　　　　→全員に2倍払う
        #子一人が最速で上がる→親から2倍貰う
        #子一人がビリ　　　　→親に倍払う
        #最速、ビリがあるのはプレイヤーが3人以上いる場合
        #それ以外→親より早い→親から1倍貰う
        #　　　　 親より遅い→親に1倍払う
        #　　　　 親と同周→やりとりなし
        if len(children_list) >= 2: #3人以上でプレイする場合
            #一人勝ち、一人負けかを判断する
            min_counter = 0
            max_counter = 0
            for finished_loop in bingoed_mem_dict.values():
                if finished_loop == finish_min:
                    min_counter += 1
                if finished_loop == finish_max:
                    max_counter += 1

            is_oya_top_or_biri = False
            if min_counter == 1: #単独負けがいる場合
                for mem_id in bingoed_mem_dict.keys():
                    if bingoed_mem_dict[mem_id] == finish_min:
                        if mem_id == oya.id: #親の単独負けなら
                            is_oya_top_or_biri = True
                            description = ""
                            for mem_id_2 in bet_dict.keys():
                                kosuu = bet_dict[mem_id_2] * 2
                                result_str = calc_stack(kosuu)
                                description += f"<@{mem_id_2}>: {result_str} ({kosuu}個)貰う\n"
                        else: #子の単独負けなら
                            kosuu = bet_dict[mem_id] * 2
                            result_str = calc_stack(kosuu)
                            description += f"<@{mem_id}>: {result_str} ({kosuu}個)払う\n"
                            del bet_dict[mem_id] #この後のforで重複しないために削除

            if max_counter == 1: #単独勝ちがいる場合
                for mem_id in bingoed_mem_dict.keys():
                    if bingoed_mem_dict[mem_id] == finish_min:
                        if mem_id == oya.id: #親の単独勝ちなら
                            is_oya_top_or_biri = True
                            description = ""
                            for mem_id_2 in bet_dict.keys():
                                kosuu = bet_dict[mem_id_2] * 2
                                result_str = calc_stack(kosuu)
                                description += f"<@{mem_id_2}>: {result_str} ({kosuu}個)払う\n"
                        else: #子の単独勝ちなら
                            kosuu = bet_dict[mem_id] * 2
                            result_str = calc_stack(kosuu)
                            description += f"<@{mem_id}>: {result_str} ({kosuu}個)貰う\n"
                            del bet_dict[mem_id] #この後のforで重複しないために削除

            if not is_oya_top_or_biri: #親に役がある場合全員分のやり取りが既に決定しているため不要
                for mem_id in bingoed_mem_dict.keys():
                    if mem_id != oya.id:
                        if bingoed_mem_dict[oya.id] == bingoed_mem_dict[mem_id]: #親と引き分けなら
                            description += f"<@{mem_id}>: やりとりなし\n"
                        elif bingoed_mem_dict[oya.id] < bingoed_mem_dict[mem_id]: #親に負けたら
                            kosuu = bet_dict[mem_id]
                            result_str = calc_stack(kosuu)
                            description += f"<@{mem_id}>: {result_str} ({kosuu}個)払う\n"
                        else: #親に勝ったら
                            kosuu = bet_dict[mem_id]
                            result_str = calc_stack(kosuu)
                            description += f"<@{mem_id}>: {result_str} ({kosuu}個)貰う\n"

        else: #2人でプレイする場合
            if bingoed_mem_dict[oya.id] == bingoed_mem_dict[children_list[0].id]:
                description = f"{children_list[0].mention}: やり取りなし"
            elif bingoed_mem_dict[oya.id] < bingoed_mem_dict[children_list[0].id]: #親が勝った場合
                kosuu = bet_dict[children_list[0].id]
                result_str = calc_stack(kosuu)
                description = f"{children_list[0].mention}: {result_str} ({kosuu}個)払う"
            else: #子が勝った場合
                kosuu = bet_dict[children_list[0].id]
                result_str = calc_stack(kosuu)
                description = f"{children_list[0].mention}: {result_str} ({kosuu}個)貰う"

        embed = discord.Embed(
            title="支払い額",
            description=description,
            color=0x000000
        )
        await channel.send(embed=embed)

        embed = discord.Embed(
            title="次のゲームはどうしますか？親が数字で入力してください。",
            description=(
                "1: 現在の設定で続ける\n"
                "2: bet上限を変更する\n"
                "3: 親を変更する\n"
                "4: メンバーを変更する(途中参加途中退出がいる場合これを使用のこと)\n"
                "5: 終了する\n\n"
                "何も送信しない場合1分後に自動で終了します"
            ),
            color=0x000000
        )
        await channel.send(embed=embed)
        def check3(m):
            return m.author == oya and m.channel == channel and m.content in ("1", "2", "3", "4", "5")

        try:
            reply = await client.wait_for("message", check=check3, timeout=60)
        except asyncio.TimeoutError:
            about_bingo.clear()
            await channel.send("ゲームは終了しました")
        else:
            if reply.content == "1":
                await children_bet(channel, oya, max_bet, max_bet_str)
            elif reply.content == "2":
                await decide_max_bet(channel, oya)
            elif reply.content == "3":
                await decide_oya(channel)
            elif reply.content == "4":
                description = ""
                for mem in player_list:
                    description += f"{mem.mention}\n"
                embed = discord.Embed(
                    title="BINGO募集",
                    description=description,
                    color=random.choice([0x0000ff, 0x00aa00, 0xff0000, 0xffff00])
                )
                msg = await channel.send(content="✋で参加、👋で退出、🆗で開始```リアクションが全て付いてからアクションを行ってください\nメッセージ系タイムアウト1分, リアクション系タイムアウト30秒", embed=embed)
                about_bingo[1] = msg
                about_bingo[2] = False
                about_bingo[0] = datetime.datetime.now()
                await msg.add_reaction("✋")
                await msg.add_reaction("👋")
                await msg.add_reaction("🆗")
            else:
                about_bingo.clear()
                await channel.send("ゲームは終了しました")

    except:
        unexpected_error()


@client.event
async def on_reaction_add(reaction, user):
    try:
        if user.bot:
            return

        if len(about_bingo) == 0:
            return

        if about_bingo[2]:
            return

        if reaction.message == about_bingo[1]:
            msg = about_bingo[1]
            player = reaction.message.guild.get_member(user.id)
            if reaction.emoji == "✋":
                if player in about_bingo:
                    await reaction.remove(user)
                    return
                about_bingo.append(player)
                description = ""
                for mem in about_bingo[3:]:
                    description += f"{mem.mention}\n"
                embed = discord.Embed(
                    title="BINGO募集",
                    description=description,
                    color=msg.embeds[0].color
                )
                await msg.edit(embed=embed)
                await reaction.remove(user)
            elif reaction.emoji == "👋":
                if not (player in about_bingo):
                    await reaction.remove(user)
                    return
                about_bingo.remove(player)
                if len(about_bingo[3:]) == 0:
                    embed = discord.Embed(
                        title="募集終了",
                        description="参加者が全員退出したため募集は終了されました",
                        color=0x000000
                    )
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    about_bingo.clear()
                    return
                description = ""
                for mem in about_bingo[3:]:
                    description += f"{mem.mention}\n"
                embed = discord.Embed(
                    title="BINGO募集",
                    description=description,
                    color=msg.embeds[0].color
                )
                await msg.edit(embed=embed)
                await reaction.remove(user)
            elif reaction.emoji == "🆗":
                if not(player in about_bingo):
                    await reaction.remove(user)
                    return
                if len(about_bingo[3:]) == 1:
                    await msg.channel.send("1人でBINGOする気ですか？させませんよ", delete_after=3)
                    await reaction.remove(user)
                    return
                about_bingo[2] = True
                embed = discord.Embed(
                    title="**募集終了**",
                    description=msg.embeds[0].description,
                    color=msg.embeds[0].color
                )
                await msg.edit(content=f"{user.name}がゲームを開始しました", embed=embed)
                await msg.clear_reactions()
                await decide_oya(msg.channel)
            else:
                await reaction.remove(user)

    except:
        unexpected_error()


@tasks.loop(seconds=60)
async def loop():
    try:
        await client.wait_until_ready()

        before_30min = datetime.datetime.now() - datetime.timedelta(minutes=30)
        #ch = client.get_channel(691901316133290035) #ミニゲーム
        ch = client.get_channel(597978849476870153) #3組

        if len(about_bingo) == 4:
            if about_bingo[0] <= before_30min:
                about_bingo.clear()
                await ch.send("30分間参加がなかったので募集は取り消されました")

    except:
        unexpected_error()

loop.start()


client.run(os.getenv("discord_bot_token_3"))