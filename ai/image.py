import webbrowser

import openai

from ai import OPENAI_API_KEY

openai.proxy = 'http://127.0.0.1:3128/'
openai.api_key = OPENAI_API_KEY

response = openai.Image.create(
    prompt="a dark alley in whitechapel, London in 1888",
    n=1,
    size="1024x1024"
)

webbrowser.open(response['data'][0]['url'], new=0, autoraise=True)
