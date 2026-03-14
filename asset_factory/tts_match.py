import asyncio
import edge_tts
import json
from pypinyin import pinyin, Style

class LightweightTTSAligner:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural"):
        self.voice = voice

    async def generate_and_align(self, text, audio_output):
        """
        核心函数：一次性搞定音频合成和音素时间轴
        """
        communicate = edge_tts.Communicate(text, self.voice)
        submaker = edge_tts.SubMaker()
        audio_data = b""

        # 1. 流式获取音频和词边界（WordBoundary）
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

        # 2. 保存音频
        with open(audio_output, "wb") as f:
            f.write(audio_data)

        # 3. 内存级“字 -> 音素”拆分
        full_phoneme_timeline = []
        for sub in submaker.subs:
            char = sub.text
            start_time = sub.start.total_seconds()
            duration = (sub.end - sub.start).total_seconds()

            # 拆分声母 (Initial) 和 韵母 (Final)
            initial = pinyin(char, style=Style.INITIALS_STRICT, strict=False)[0][0]
            final = pinyin(char, style=Style.FINALS, strict=False)[0][0]

            if initial:
                # 经验公式：声母通常短促，占 25%，韵母占 75%
                initial_dur = duration * 0.25
                full_phoneme_timeline.append({
                    "p": initial,
                    "s": round(start_time, 3),
                    "e": round(start_time + initial_dur, 3)
                })
                full_phoneme_timeline.append({
                    "p": final,
                    "s": round(start_time + initial_dur, 3),
                    "e": round(start_time + duration, 3)
                })
            else:
                # 零声母（如“啊”、“喔”）
                full_phoneme_timeline.append({
                    "p": final,
                    "s": round(start_time, 3),
                    "e": round(start_time + duration, 3)
                })

        return full_phoneme_timeline

# --- 使用示例 ---
async def main():
    aligner = LightweightTTSAligner()
    # 模拟用户的问题
    text = "你好，我是你的智能助手。"
    phonemes = await aligner.generate_and_align(text, "output.mp3")
    
    print("✨ 最终吐给前端的剧本数据：")
    print(json.dumps(phonemes, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())