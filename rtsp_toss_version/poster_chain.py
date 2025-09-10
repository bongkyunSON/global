import base64
from pprint import pprint

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import PromptTemplate


api_key = "AIzaSyASVj38hqqlBK0kMl4_hl4gpODTFin_b9E"


# 두 작업(OCR, JSON 추출)에 모두 사용할 LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=api_key,
)


# --- 1. OCR(이미지에서 텍스트 추출)를 위한 부분 ---

def create_multimodal_message(input_dict: dict) -> list[HumanMessage]:
    """이미지 경로와 텍스트 프롬프트를 받아 HumanMessage 객체를 생성합니다."""
    with open(input_dict["image_path"], "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": input_dict["prompt"]},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded_image}"},
        ]
    )
    return [message]

# 이미지에서 텍스트를 추출하는 체인
ocr_chain = RunnableLambda(create_multimodal_message) | llm | StrOutputParser()


# --- 2. 추출된 텍스트에서 정보를 JSON 형식으로 추출하기 위한 부분 ---

json_prompt_template = PromptTemplate.from_template(
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
json_parser = JsonOutputParser()
# prompt 템플릿에 출력 형식(json) 정보를 미리 주입합니다.
json_extraction_prompt = json_prompt_template.partial(
    instructions=json_parser.get_format_instructions()
)

# 텍스트에서 JSON을 추출하는 체인
json_extraction_chain = json_extraction_prompt | llm | json_parser


# --- 3. 위에서 만든 두 체인을 하나로 연결 ---

chain = (
    # chain.invoke의 입력이 ocr_chain으로 전달되어 텍스트가 추출됩니다.
    # 추출된 텍스트는 "poster_context" 키의 값이 됩니다.
    {"poster_context": ocr_chain}
    # 위에서 만들어진 {"poster_context": "추출된 텍스트"}가 
    # json_extraction_chain으로 전달됩니다.
    | json_extraction_chain
)


if __name__ == "__main__":
    image_file_path = "/Users/sbk/global/rtsp_toss_version/poster.jpeg"
    # OCR 단계에서 사용할 프롬프트
    prompt_text = "이 이미지에서 보이는 모든 텍스트를 순서대로 정확하게 추출해줘."

    # 전체 체인 실행
    result = chain.invoke({"image_path": image_file_path, "prompt": prompt_text})
    
    print("--- 최종 추출 결과 ---")
    pprint(result)
