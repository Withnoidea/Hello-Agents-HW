import os
import requests
from tavily import TavilyClient
from dotenv import load_dotenv
def get_attraction(city: str, weather: str) -> str:
  
  """
  根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
  """

  # 1.从环境变量中获取Tavily API密钥
  load_dotenv()
  api_key = os.environ.get("TAVILY_API_KEY")
  if not api_key:
    return "错误:未配置TAVILY_API_KEY环境变量。"
  
  # 2.初始化Tavily客户端
  tavily = TavilyClient(api_key=api_key)

  # 3.构建搜索查询
  query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"
  
  try:
    # 4.调用Tavily Search API进行搜索
    response = tavily.search(query=query, search_depth="basic", include_answer=True)

    # 5. Tavily返回的结果已经非常干净，可以直接使用
    # response['answer'] 是一个基于所有搜索结果的总结性回答
    if response.get("answer"):
      return response["answer"]
    
    # 如果没有综合性回答，则格式化原始结果
    forrmatted_results = []
    for result in response.get("results", []):
      forrmatted_results.append(f"- {result['title']}: {result['content']}")

    
    if not forrmatted_results:
      return "抱歉，没有找到相关的景点推荐。"

    return "根据搜索，为您找到以下信息:\n" + "\n".join(forrmatted_results)
  
  except Exception as e:
    return f"错误:执行Tavily搜索时出现问题 - {e}"


def translateX(text: str) -> str:
    """
    将天气信息翻译成中文。
    """

    # load_dotenv()
    url = os.environ.get("TRANSLATION_API")

    payload = {
        "text": text,
        "source_lang": "auto",
        "target_lang": "ZH"
    }

    resp = requests.post(url, json=payload)
    return resp.json()["data"]
    

txt = get_attraction("北京", "晴朗")

print(translateX(txt) + "\n" + txt)