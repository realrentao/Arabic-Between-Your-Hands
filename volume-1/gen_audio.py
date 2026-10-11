# -*- coding: utf-8 -*-
"""
《阿拉伯语在你手中》第一册 · 真人发音批处理
- 提取全站 .ar 阿语短语（去重）
- 用 edge-tts ar-AE-FatimaNeural 生成 mp3
- 输出 js/ar_audio_map.js（window.AR_AUDIO 映射）
- 为每个 HTML 注入映射脚本标签（在 app.js 之前）
支持断点续跑：已存在且非空的文件跳过。
"""
import re, glob, os, json, asyncio, edge_tts

BASE = os.path.dirname(os.path.abspath(__file__))
VOICE = "ar-AE-FatimaNeural"
CONCURRENCY = 12

def collect_phrases():
    phrases = []
    for f in glob.glob(os.path.join(BASE, "*.html")):
        s = open(f, encoding="utf-8").read()
        for m in re.findall(r'class="ar"[^>]*>(.*?)</span>', s, re.S):
            txt = re.sub(r"<[^>]+>", "", m)
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                phrases.append(txt)
    uniq = sorted(set(phrases), key=lambda x: (len(x), x))
    return uniq

def build_mapping(uniq):
    return {p: "audio/a%04d.mp3" % (i + 1) for i, p in enumerate(uniq)}

async def worker(sem, p, path, fails):
    async with sem:
        if os.path.exists(path) and os.path.getsize(path) > 200:
            return
        try:
            await edge_tts.Communicate(p, VOICE).save(path)
        except Exception as e:
            fails.append((p, repr(e)))

async def main():
    uniq = collect_phrases()
    mapping = build_mapping(uniq)
    out_dir = os.path.join(BASE, "audio")
    os.makedirs(out_dir, exist_ok=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    fails = []
    total = len(uniq)
    done = 0

    async def tracked(p, path):
        nonlocal done
        await worker(sem, p, path, fails)
        done += 1
        if done % 100 == 0 or done == total:
            print("进度 %d/%d  失败 %d" % (done, total, len(fails)), flush=True)

    await asyncio.gather(*[tracked(p, os.path.join(BASE, mapping[p])) for p in uniq])

    # 写出映射
    with open(os.path.join(BASE, "js", "ar_audio_map.js"), "w", encoding="utf-8") as f:
        f.write("/* 自动生成：阿语真人发音映射（ar-AE-FatimaNeural）。勿手改。 */\n")
        f.write("window.AR_AUDIO = ")
        f.write(json.dumps(mapping, ensure_ascii=False, sort_keys=True))
        f.write(";\n")

    # 注入脚本标签到每个 HTML（在 app.js 之前）
    tag = '<script src="js/ar_audio_map.js"></script>\n  <script src="js/app.js"></script>'
    for f in glob.glob(os.path.join(BASE, "*.html")):
        s = open(f, encoding="utf-8").read()
        if "ar_audio_map.js" in s:
            continue
        s = s.replace('<script src="js/app.js"></script>', tag, 1)
        open(f, "w", encoding="utf-8").write(s)

    print("完成：唯一短语 %d，失败 %d" % (total, len(fails)), flush=True)
    if fails:
        for p, e in fails[:20]:
            print("  FAIL", repr(p), e)

if __name__ == "__main__":
    asyncio.run(main())
