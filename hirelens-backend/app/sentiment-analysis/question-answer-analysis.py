from openai import OpenAI
# openrouter openai api key: "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"

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="OPENROUTER_API_KEY",
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  extra_body={},
  model="deepseek/deepseek-chat-v3-0324:free",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)