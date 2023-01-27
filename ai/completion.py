import openai

from ai import OPENAI_API_KEY

openai.proxy = 'http://127.0.0.1:3128/'
openai.api_key = OPENAI_API_KEY

while True:
    user_input = input("Ask your question or demand : \n")

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=user_input,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        n=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )

    print(response.choices[0].text)
