# 增加HF_ENDPOINT，避免Connection aborted. 
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# 指定模型缓存到 E 盘
os.environ["HF_HOME"] = r"E:\document\project\huggingface_cache"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 指定模型ID
model_id = "Qwen/Qwen1.5-0.5B-Chat"

# 设置设备，优先使用GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# 加载分词器（只加载一次）
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 加载模型，并将其移动到指定设备（只加载一次）
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)

print("模型和分词器加载完成！")

# 对话历史：先放一个 system 角色设定，之后 user/assistant 轮流追加
messages = [
    {"role": "system", "content": "You are a helpful assistant. Response only in Chinese."}
]

print("===== 开始对话（输入 exit 或 quit 结束）=====")

while True:
    # 1) 获取用户输入
    user_input = input("\n你: ").strip()
    if user_input.lower() in ("exit", "quit", "q"):
        print("对话结束。")
        break
    if not user_input:
        continue

    # 2) 把用户消息追加进历史
    messages.append({"role": "user", "content": user_input})

    # 3) 用聊天模板格式化【整个】对话历史
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # 4) 编码输入文本
    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    # 5) 使用模型生成回答
    generated_ids = model.generate(
        model_inputs.input_ids,
        max_new_tokens=512
    )

    # 6) 截取掉输入部分，只保留模型新生成的内容
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    # 7) 解码生成的 Token ID
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    # 8) 关键：把模型的回复也追加进历史，下一轮才能带上上下文
    messages.append({"role": "assistant", "content": response})

    # 9) 打印模型回复
    print(f"模型: {response}")
