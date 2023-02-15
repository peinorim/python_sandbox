import os
import webbrowser

import openai
import requests

from ai import OPENAI_API_KEY

openai.proxy = 'http://127.0.0.1:3128/'
openai.api_key = OPENAI_API_KEY


class ImageGenerator:

    def generate(self, img_request: str = None) -> bool:
        """

        :param img_request:
        :return:
        """
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
                return webbrowser.open(url)
            return False

        except Exception as err:
            print(err)
            raise err


if __name__ == '__main__':
    img_request = "picture of something"
    res = ImageGenerator().generate(img_request=img_request)
