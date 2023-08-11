from flask import Flask, request, abort
import os
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Set OpenAI API details
openai.api_type = "azure"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

app = Flask(__name__)

# Initialize messages list with the system message
#messages = [
#    {"role": "system", "content": "You are a helpful assistant that has a deep understanding of cat and also speaks like a cat. \
#                                   Your name is MewBot or 喵喵號 in Chinese. You not only provide fun facts about cats, you are also very good at telling jokes.  \
#                                   You know everything about cats: lifestyles, habits, anecdotes, and rarely-known cat facts. \
#                                   You will say you don't know if the answer does not match any result from your database. Be concise with your response \
#                                   Refrain from responding in simplified Chinese, you will respond in traditional Chinese at all time."},
#]

messages = [
    {"role": "system", "content":  "您是一個很火爆的人,回答都很不耐煩,也很簡短,你名字叫'浪子',2020年10月31日出生.\
                                    常常都會在語言前面加'幹!',也常會講'幹x娘',說話都很粗俗.\
                                    你的職業是卡車司機,常常熬夜加班開車,沒有女友.\
                                    你不知道科技、電腦、程式或AI模型是什麼,所以不能回答這些內容,也不能說自己是聊天機器人.\
                                    任何時候都必須扮演真正的低俗火爆浪子,若要回答科技或是專業問題時,就回答'幹!我不知道.' \
                                    只能用繁體中文回覆."},
]


# This function takes a chat message as input, appends it to the messages list, sends the recent messages to the OpenAI API, and returns the assistant's response.
def aoai_chat_model(chat):
    # Append the user's message to the messages list
    messages.append({"role": "user", "content": chat})

    # Only send the last 5 messages to the API
    recent_messages = messages[-5:]

    # Send the recent messages to the OpenAI API and get the response
    response_chat = openai.ChatCompletion.create(
        engine="gpt-35-turbo",
        messages=recent_messages,
        temperature=0.7,
        max_tokens=150,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    # Append the assistant's response to the messages list
    messages.append({"role": "assistant", "content": response_chat['choices'][0]['message']['content'].strip()})

    return response_chat['choices'][0]['message']['content'].strip()

# Initialize Line API with access token and channel secret
line_bot_api = LineBotApi(os.getenv('LINE_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# This route serves as a health check or landing page for the web app.
@app.route("/")
def mewobot():
    return 'ok Time!!!'

# This route handles callbacks from the Line API, verifies the signature, and passes the request body to the handler.
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# This event handler is triggered when a message event is received from the Line API. It sends the user's message to the OpenAI chat model and replies with the assistant's response.
@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=aoai_chat_model(event.message.text))
    )

if __name__ == "__main__":
    app.run()
