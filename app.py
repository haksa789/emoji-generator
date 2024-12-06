import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import openai
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/generate": {"origins": "http://localhost:3000"}})

# .env 파일 로드
load_dotenv()
# OpenAI API Key 설정
openai.api_key = os.getenv("OPENAI_API_KEY")  # 환경 변수에서 API 키 불러오기

DEBUG_MODE = os.getenv("DEBUG_MODE", "True") == "True"

if DEBUG_MODE:
    print(f"Debugging enabled. Loaded API Key: {os.getenv('OPENAI_API_KEY')}")

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        # 사용자 요청 데이터 받기
        data = request.json
        user_input = data.get("prompt", "a cat sitting on a chair")
        print(f"Received prompt: {user_input}")  # 입력 로그

        # 1. 프롬프트를 영어로 번역
        translation_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator that converts Korean to English."},
                {"role": "user", "content": user_input}
            ]
        )
        translated_prompt = translation_response['choices'][0]['message']['content']
        print(f"Translated Prompt: {translated_prompt}")  # 번역된 프롬프트 출력        

        # 2. 번역된 프롬프트로 이미지 생성 요청
        response = openai.Image.create(
            prompt=translated_prompt,
            n=1,
            size="512x512"
        )
        print(f"OpenAI API response: {response}")  # 응답 로그

        # 생성된 이미지 URL 반환
        image_url = response['data'][0]['url']
        return jsonify({"image_url": image_url})
    except Exception as e:
        print(f"Error: {str(e)}")  # 에러 로그
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)
