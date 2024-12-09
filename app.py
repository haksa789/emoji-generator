import os
import logging
import re  # 정규 표현식 모듈 추가
from datetime import datetime
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
openai.api_key = os.getenv("OPENAI_API_KEY")

DEBUG_MODE = os.getenv("DEBUG_MODE", "True") == "True"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 날짜별 로그 파일 설정
log_dir = "logs"
today_date = datetime.now().strftime("%Y-%m-%d")

# 로그 디렉토리 생성
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로그 파일 경로 설정
log_file = f"{log_dir}/{today_date}.log"

# 로깅 설정
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if DEBUG_MODE:
    print(f"Debugging enabled. Logs will be saved in: {log_file}")

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.json
        user_input = data.get("prompt", "").strip()
        if not user_input:
            return jsonify({"error": "오! 프롬프트가 비어 있어요! 멋진 아이디어를 입력해 보세요 😊"}), 400

        logging.info(f"User Prompt: {user_input}")

        # 금지된 입력 패턴 (무의미한 입력)
        invalid_input_patterns = ["^[ㄱ-ㅎㅏ-ㅣ]+$", "^[a-zA-Z]+$", "^[!@#$%^&*()_+=]+$"]
        for pattern in invalid_input_patterns:
            if re.match(pattern, user_input):
                logging.warning("유효하지 않은 입력 패턴")
                return jsonify({"error": "앗! 무의미한 입력이에요. 조금 더 구체적으로 입력해 주세요! 🌟"}), 400

        # 1. 프롬프트에 대한 자세한 설명 생성
        explanation_response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": (
                    "You are an expert who can create detailed descriptions of different topics to the AI who paints. Any word should convey its external features perfectly. For example, even if it seems like I'm asking you a question, you should explain the word, not the question."
                    "Your mission is to generate detailed descriptions based on your input; however, the number of characters must be no more than 200."
                    ),
                },
                {"role": "user", "content": user_input}  # user의 입력값
            ],
        )
        
        detailed_explanation = explanation_response['choices'][0]['message']['content']
        logging.info(f"Detailed Explanation: {detailed_explanation}")

        # 2. 설명을 영어로 번역
        translation_response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator who translates Korean text into English."
                },
                {"role": "user", "content": detailed_explanation}  # 설명된 내용을 영어로 번역
            ],
        )
        
        translated_explanation = translation_response['choices'][0]['message']['content']
        logging.info(f"Translated Explanation: {translated_explanation}")

        # 검증: 번역된 결과가 유효한지 확인
        invalid_keywords = [
            "i'm sorry", "I'm sorry", "i'm unable to", "could you provide", "does not appear to", "meaning is unclear",
            "difficult to understand", "please try again", "may be an error", "may be a typo", "i do not recognize", 
            "does not make sense", "could not process", "could not determine", "ambiguous", "not clear", "unsure", 
            "is confusing", "cannot generate", "unknown context", "lack of clarity", "doesn't seem clear", "hard to understand",
            "not valid", "does not make sense", "is not a valid", "could not understand", "may be a typo", "please provide more context",
            "check for errors", "unrecognizable", "does not appear", "meaning is unclear", "specific term", "unknown term", 
            "does not exist", "is unclear", "is not recognized", "seems to be invalid", "could you clarify", "please clarify"
        ]
        
        if any(keyword in translated_explanation.lower() for keyword in invalid_keywords):
            logging.warning("유효하지 않은 번역 결과")
            return jsonify({"error": "앗! 제가 그 말을 잘 이해하지 못했어요. 다른 멋진 아이디어를 입력해 주세요! 🚀"}), 400

        # 3. 이미지 생성
        response = openai.Image.create(
            prompt=translated_explanation,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        logging.info(f"Generated Image URL: {image_url}")
        
        return jsonify({"image_url": image_url})

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"error": "앗! 뭔가 잘못된 것 같아요. 잠시 후 다시 시도해 주세요! 🙏"}), 500

if __name__ == "__main__":
    app.run(debug=DEBUG_MODE, host='0.0.0.0', port=5000)
