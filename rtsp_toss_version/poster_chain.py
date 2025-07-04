import requests

from langchain_upstage import ChatUpstage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate


api_key = "up_bOaHQqlyLHKwnqR0AS9dbkUJt3BaB"


prompt = PromptTemplate.from_template(
    """
    ### 역할 ###
    너는 해당 포스터의 내용을 보고 정보를 추출해야합니다.
    분야같은 경우는 해당 리스트에서 최대 5개를 추출하고 꼭 굳이 5개가 아니여도돼

    ### 입력 ###
    {poster_context}

    
    ### 포스터 정보 ###
    1. 세미나 일시: 
    2. 제목:
    3. 주최 장소:  
    4. 주최(국회의원):
    5. 주최(그외):
    6. 주관 및 후원:
    7. 분야(최대 5개선택):
     [경제, 인권, 정치, 사법, 보훈, 금융, 재정, 교육, 외교, 통일, 국방, 선거, 체육, 산업, 보건, 복지, 환경, 노동, 국토, 교통, 기타, 지자체, 공정거래, 과학기술, 공공안전, 문화관광, 해양수산, 여성가족, 정보방송통신, 농림축산식품, 중소거업 벤처]

    8. 키워드:
    9. 좌장:
    10. 패널:


    ### 출력 형식 ###
    Instructions: {instructions}

    """
)


def poster_info(apikey, filename):
    api_key = apikey
    filename = (
        "/Users/sbk/global/rtsp_toss_version/toss-library/APOS_COVER1750126279419.jpg"
    )

    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}

    files = {"document": open(filename, "rb")}
    data = {"model": "ocr"}
    response = requests.post(url, headers=headers, files=files, data=data)

    result = response.json()
    text_result = result["pages"][0]["text"]


    json_parser = JsonOutputParser()

    llm = ChatUpstage(api_key=api_key, model="solar-pro2-preview")
    template = prompt.partial(instructions=json_parser.get_format_instructions())

    chain = (
        {
            "poster_context": RunnablePassthrough(),
        }
        | template
        | llm
        | json_parser
    )

    result = chain.invoke({"poster_context": text_result})

    return result



if __name__ == "__main__":
    result = poster_info(
        api_key,
        "/Users/sbk/global/rtsp_toss_version/toss-library/APOS_COVER1750126279419.jpg",
    )
    print(result)
