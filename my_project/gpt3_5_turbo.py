import sys
import base64

from my_project.GPTUtil import GPTUtil

if len(sys.argv) < 2:
    raise ValueError("No argument provided. Please provide input")

content = sys.argv[1]
# b64 decode
content = base64.b64decode(content).decode('utf-8')
# content = "Hello World"

response = (GPTUtil.gpt3_5_response(content, False))
# # normal response
# response = g4f.ChatCompletion.create(model=g4f.Model.gpt_35_turbo, messages=[{"role": "user", "content": content}], provider=g4f.Provider.DeepAi)
#
print("result:")
print(response.encode("utf-8"))