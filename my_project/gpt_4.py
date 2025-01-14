import g4f
import sys
import base64
print(g4f.Provider.Ails.params) # supported args

# Automatic selection of provider
from g4f.Provider import (
    Ails,
    You,
    Bing,
    Yqcloud,
    Theb,
    Aichat,
    Bard,
    Vercel,
    Forefront,
    Lockchat,
    Liaobots,
    H2o,
    ChatgptLogin,
    DeepAi,
    GetGpt
)

if len(sys.argv) < 2:
    raise ValueError("No argument provided. Please provide input")

content = sys.argv[1]
# b64 decode
content = base64.b64decode(content).decode('utf-8')

# normal response
response = g4f.ChatCompletion.create(model=g4f.Model.gpt_4, messages=[{"role": "user", "content": content}], provider=g4f.Provider.Bing) # alterative model setting

print("result:")
print(response.encode("utf-8"))