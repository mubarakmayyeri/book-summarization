import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Form, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from groq import Groq

# Load environment variables
load_dotenv()

# Set API keys and Telegram credentials
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
VALID_PASS_KEY = os.getenv('PASS_KEY')

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

# FastAPI app instance
app = FastAPI()

# Set up templates directory
templates = Jinja2Templates(directory="templates")

def chat_template_creation(book_name):
    messages = [
        {
            "role": "system",
            "content": f"""
                    Generate a summary of the book {book_name} with the following format:
                                *Book Name* by *Author Name*

                                *Overview*
                                Provide a brief overview of the book's content and main themes.

                                *Principal Insights*
                                1. Key Insight 1
                                2. Key Insight 2
                                3. Key Insight 3
                                4. Key Insight 4
                                5. Key Insight 5
                                6. Key Insight 6
                                7. Key Insight 7

                                *Application in Practical Life*
                                - Application Point 1
                                - Application Point 2
                                - Application Point 3
                                - Application Point 4
                                - Application Point 5

                                *Related Readings*
                                - _Related Book 1_ and brief description
                                - _Related Book 2_ and brief description
                                - _Related Book 3_ and brief description
                                - _Related Book 4_ and brief description

                                *Final Thoughts*
                                _Provide concluding thoughts on the book_.

                                Include the formatting symbols as specified in the format. Ensure the final thoughts content starts and ends with a underscore symbol. Enusre to use a single asterisk (*) for highlighting the subheadings and other keywords instead of ##. Give the summary with specified format as a python string
                                Don't use double asterisks, use only single asterisks for highlighting the text
                                
                                """
        },
        {
            "role": "user",
            "content": f"Generate a summary of the book *{book_name}*."
        }
    ]
    return messages

def summary_generation(messages):
    chat_completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=messages,
        temperature=0.5,
        max_tokens=1024
    )
    return chat_completion.choices[0].message.content

def send_message(token, channel_id, message, parse_mode='Markdown'):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': channel_id,
        'text': message,
        'parse_mode': parse_mode
    }
    response = requests.post(url, data=payload)
    return response.json()

# Dependency to verify the pass key
def verify_pass_key(pass_key: str = Form(...)):
    if pass_key != VALID_PASS_KEY:
        raise HTTPException(status_code=403, detail="Invalid pass key")
    return pass_key

@app.get("/")
def read_root():
    return {"Hello": "There!"}

# Route to serve the HTML form and display the result on the same page
@app.get("/generate_summary/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "summary": None, "telegram_response": None, "error": None})

# Route to handle form submission and display results on the same page
@app.post("/generate_summary/", response_class=HTMLResponse)
async def generate_summary(
    request: Request,
    book_name: str = Form(...),
    pass_key: str = Form(...)
):
    if not verify_pass_key(pass_key):
        return templates.TemplateResponse("home.html", {"request": request, "summary": None, "telegram_response": None, "error": "Invalid pass key. Please try again."})
    
    try:
        chat_template = chat_template_creation(book_name)
        summary = summary_generation(chat_template)
        tg_response = send_message(TOKEN, CHANNEL_ID, summary)
        return templates.TemplateResponse("home.html", {"request": request, "summary": summary, "telegram_response": tg_response, "error": None})
    except Exception as e:
        return templates.TemplateResponse("home.html", {"request": request, "summary": None, "telegram_response": None, "error": str(e)})