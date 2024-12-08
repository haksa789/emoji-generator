import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import openai
from flask_cors import CORS

# .env 파일 로드
load_dotenv()

# Flask 앱 생성 및 CORS 설정
app = Flask(__name__)
CORS(app, resources={r"/generate": {"origins": os.getenv("CORS_ORIGIN")}})

# OpenAI API Key 설정
openai.api_key = os.getenv("OPENAI_API_KEY")  # 환경 변수에서 API 키 불러오기

DEBUG_MODE = os.getenv("DEBUG_MODE", "True") == "True"

# 로깅 설정
logging.basicConfig(
    filename="logs/server.log",  # 로그 파일 경로
    level=logging.INFO,  # 로그 레벨
    format="%(asctime)s - %(levelname)s - %(message)s"  # 로그 포맷
)

if DEBUG_MODE:
    print(f"Debugging enabled. Loaded API Key: {os.getenv('OPENAI_API_KEY')}")
    print(f"CORS Origin: {os.getenv('CORS_ORIGIN')}")

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        # 사용자 요청 데이터 받기
        data = request.json
        user_input = data.get("prompt", "a cat sitting on a chair")
        logging.info(f"User Prompt: {user_input}")  # 프롬프트 로그 저장
        print(f"Received prompt: {user_input}")  # 터미널 로그

        # 1. 프롬프트를 영어로 번역하고 디테일 추가
        translation_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator and assistant that translates Korean prompts to English and enhances them with detailed descriptions for image generation."},
                {"role": "user", "content": user_input}
            ]
        )
        translated_prompt = translation_response['choices'][0]['message']['content']
        logging.info(f"Translated Prompt: {translated_prompt}")  # 번역된 프롬프트 저장
        print(f"Translated Prompt: {translated_prompt}")  # 터미널 로그

        # 2. 번역된 프롬프트로 이미지 생성 요청
        response = openai.Image.create(
            prompt=translated_prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        logging.info(f"OpenAI Image Response: {response}")  # OpenAI 응답 저장
        logging.info(f"Generated Image URL: {image_url}")  # 이미지 URL만 별도로 저장
        print(f"OpenAI API response: {response}")  # 터미널 로그

        # 생성된 이미지 URL 반환
        return jsonify({"image_url": image_url})
    except Exception as e:
        logging.error(f"Error: {str(e)}")  # 에러 로그 기록
        print(f"Error: {str(e)}")  # 터미널 로그
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=DEBUG_MODE, host='0.0.0.0', port=5000)
