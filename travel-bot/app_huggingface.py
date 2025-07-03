import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
HF_API_KEY = os.getenv("HF_API_KEY")
MODEL_ID = "beomi/KoAlpaca-Polyglot-5.8B"  # Hugging Face 모델 ID

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("message")

    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    body = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{MODEL_ID}",
            headers=headers,
            json=body
        )
        res = response.json()
        return jsonify({"response": res[0]["generated_text"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True) 