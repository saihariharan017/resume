import os

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types

from chatbot_config import CHATBOT_TITLE, MODEL_NAME, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from the environment.")

client = genai.Client(api_key=api_key)


@app.get("/")
def index():
    return render_template(
        "index.html",
        chatbot_title=CHATBOT_TITLE,
    )


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    contents = []
    for item in history[-12:]:
        role = item.get("role")
        text = (item.get("content") or "").strip()
        if role in {"user", "model"} and text:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=text)],
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.25,
            ),
        )

        answer = (response.text or "").strip()
        if not answer:
            answer = "I could not generate a response. Please try again."

        return jsonify({"answer": answer})

    except Exception as exc:
        app.logger.exception("Gemini API request failed")
        return jsonify({"error": "The chatbot could not process your request right now."}), 500


if __name__ == "__main__":
    app.run()
