from openai import OpenAI

class OpenAICompatibleClient:
  """
  一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
  """
  def __init__(self, model: str, api_key: str, base_url: str):
    self.model = model
    self.client = OpenAI(api_key=api_key, base_url=base_url)
  def generate(self, prompt: str, system_prompt: str) -> str:
    response = self.client.chat.completions.create(
      model=self.model,
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
      ]
    )