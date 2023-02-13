import os
import webbrowser

import openai
import requests

from ai import OPENAI_API_KEY

openai.proxy = 'http://127.0.0.1:3128/'
openai.api_key = OPENAI_API_KEY

img_request = "a dark alley in whitechapel, London in the late 1800's"
url = None

try:

    ai_response = openai.Image.create(
        prompt=img_request,
        n=1,
        size="1024x1024"
    )

    url = ai_response['data'][0]['url']

    response = requests.get(url, proxies={"https": openai.proxy} if openai.proxy else None)
    if response.content:
        f = open(f"{os.getcwd()}\\images\\{img_request.replace(' ', '-').replace('.', '_')}.png", 'wb')
        f.write(response.content)
        f.close()

    if url:
        webbrowser.open(url, new=0, autoraise=True)

except Exception as err:
    print(err)
