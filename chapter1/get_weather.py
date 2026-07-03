import requests


# 天气英文名称与中文的映射字典
WEATHER_NAME_TO_CN = {
    "clear/sunny": "晴朗",
    "partly cloudy": "少云",
    "cloudy": "多云",
    "overcast": "阴天",
    "haze": "霾",
    "dust haze": "尘霾",
    "blowing dust": "吹尘",
    "dust storm": "尘暴",
    "sandstorm": "沙暴",
    "severe sandstorm": "强沙暴",
    "mist": "雾",
    "smoke": "烟",
    "smoky haze": "烟霾",
    "smog": "烟雾",
    "severe smog": "强烟雾",
    "saharan dust": "撒哈拉沙尘",
    "dust": "尘埃",
    "patchy rain nearby": "局部小雨",
    "patchy snow nearby": "局部小雪",
    "patchy sleet nearby": "局部雨夹雪",
    "patchy freezing drizzle nearby": "局部冻雨",
    "thundery outbreaks in nearby": "局部雷阵雨",
    "blowing snow": "吹雪",
    "blizzard": "暴雪",
    "fog": "雾",
    "freezing fog": "冻雾",
    "patchy light drizzle": "局部细雨",
    "light drizzle": "毛毛雨",
    "freezing drizzle": "冻雨",
    "heavy freezing drizzle": "冻雨",
    "patchy light rain": "局部小雨",
    "light rain": "小雨",
    "moderate rain at times": "中等阵雨",
    "moderate rain": "中雨",
    "heavy rain at times": "大阵雨",
    "heavy rain": "大雨",
    "light freezing rain": "小冻雨",
    "moderate or heavy freezing rain": "中冻雨",
    "light sleet": "小雨夹雪",
    "moderate or heavy sleet": "中雨夹雪",
    "patchy light snow": "局部小雪",
    "light snow": "小雪",
    "patchy moderate snow": "局部中雪",
    "moderate snow": "中雪",
    "patchy heavy snow": "局部大雪",
    "heavy snow": "大雪",
    "ice pellets": "冰粒",
    "light rain shower": "小阵雨",
    "moderate or heavy rain shower": "大阵雨",
    "torrential rain shower": "暴雨",
    "light sleet showers": "小雨夹雪阵",
    "moderate or heavy sleet showers": "中雨夹雪阵",
    "light snow showers": "小雪阵",
    "moderate or heavy snow showers": "大雪阵",
    "light showers of ice pellets": "小冰粒阵",
    "moderate or heavy showers of ice pellets": "中冰粒阵",
    "patchy light rain in area with thunder": "局部雷阵雨",
    "moderate or heavy rain in area with thunder": "雷暴雨",
    "patchy light snow in area with thunder": "局部雷阵雪",
    "moderate or heavy snow in area with thunder": "强雷暴雪",
}

def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 获取天气信息。
    """
    # API端点，我们请求JSON格式的数据
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()

        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value'].lower()
        weather_desc_cn = WEATHER_NAME_TO_CN.get(weather_desc, weather_desc)
        temp_c = current_condition['temp_C']
        # 格式化成自然语言返回

        return f"{city}当前天气:{weather_desc_cn}\n气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"



# while True:
#     city = input("请输入城市名称查询当地天气\n(输入exit退出程序):")
#     if city.lower() == 'exit':
#         print("退出程序。")
#         break
#     print(get_weather(city))
