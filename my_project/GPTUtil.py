import random
import re

import openai
import tiktoken
from openai.openai_object import OpenAIObject

import g4f

from my_project.Config import config

enc = tiktoken.get_encoding("cl100k_base")
assert enc.decode(enc.encode("hello world")) == "hello world"


# Ails
# Aichat
# DeepAi
# GetGpt
# AItianhu
# EasyChat
# DfeHub
# AiService

class GPTUtil:
    _GPT3_PROVIDERS = [
        # g4f.Provider.Ails,
       g4f.Provider.Aichat, # works
       # g4f.Provider.DeepAi,
       g4f.Provider.GetGpt, # works
       # g4f.Provider.AItianhu,
       # g4f.Provider.EasyChat,
       # g4f.Provider.DfeHub,
       # g4f.Provider.AiService
       ]
    # set to random starting index using rand int in range of len(_GPT3_PROVIDERS)
    _GPT_PROVIDER_INDEX = random.randint(0, len(_GPT3_PROVIDERS) - 1)

    openai.api_key = config.open_ai.api_key

    @staticmethod
    def gpt3_5_response(prompt: str, allow_paid: bool = False):
        maxRange = len(GPTUtil._GPT3_PROVIDERS)
        for i in range(maxRange):
            GPTUtil._GPT_PROVIDER_INDEX += 1
            myIndex = GPTUtil._GPT_PROVIDER_INDEX % len(GPTUtil._GPT3_PROVIDERS)
            pickprovider = GPTUtil._GPT3_PROVIDERS[myIndex]
            print("GPTUtil.gpt3Request: trying provider: " + pickprovider.__name__)
            try:
                result = g4f.ChatCompletion.create(model=g4f.Model.gpt_35_turbo,
                                                   messages=[{"role": "user", "content": prompt}],
                                                   provider=pickprovider)
                if result is not None and result != "":
                    print("Succeeded for provider: " + pickprovider.__name__)
                    return result
            except Exception as e:
                print("GPTUtil.gpt3Request: retrying. Failed for " + pickprovider.__name__ + ": " + str(e))
                continue
        if allow_paid:
            print("GPTUtil.gpt3Request: using paid API")
            completion = openai.ChatCompletion.create(
                api_key=config.open_ai.api_key,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}])
            return completion.choices[0].message.content

    @staticmethod
    def getModeration(input):
        openai.api_key = config.open_ai.api_key
        moderation_resp = openai.Moderation.create(
            input=input)
        return moderation_resp

    @staticmethod
    def checkModeration(moderation_result: OpenAIObject, text: str):
        # escape all backticks in text

        # if error in moderation_result
        if "error" in moderation_result:
            raise ValueError(f"Moderation error: {moderation_result['error']}")

        # if results not in moderation_result
        if "results" not in moderation_result:
            raise ValueError(f"Moderation error: no results found")

        # iterate results list
        for result in moderation_result["results"]:
            # if result is flagged
            if result["flagged"]:
                text = text.replace("```", "\\`\\`\\`")
                # raise error
                raise ValueError(f"Your submission has been flagged as inappropriate:\n" +
                                 "```json\n" + str(result.category_scores) + "\n```\n" +
                                 "The content submitted:\n" +
                                 "```json\n" + text + "\n```")

        return True

    @staticmethod
    def getTokens(input: str, model_type: str, wrap: bool = False):
        # To get the tokeniser corresponding to a specific model in the OpenAI API:
        to_encode = input
        enc = tiktoken.encoding_for_model(model_type)
        encoded = enc.encode(input)
        # return length
        return len(encoded)

    @staticmethod
    def getChunks(input, model_type, token_size_max):
        result = []

        lines = re.split(r'[\r\n]+|\. ', input)

        # get tokenizer
        tokenizer = tiktoken.encoding_for_model(model_type)

        # get the tokens count for each line
        tokens_count = []
        for line in lines:
            size = len(tokenizer.encode(line))
            if size > token_size_max:
                raise ValueError(f"Line exceeds token limit of {token_size_max}")
            tokens_count.append(size)

        current_chunk_size = 0
        current_chunk = ""
        for line, line_tokens in zip(lines, tokens_count):
            if current_chunk_size + line_tokens > token_size_max:
                # process current chunk
                result.append(current_chunk)
                # start new chunk
                current_chunk = ""
                current_chunk_size = 0
            current_chunk += line + "\n"
            current_chunk_size += line_tokens
        # process last chunk
        result.append(current_chunk)

        return result

    @staticmethod
    def getFirst(input_str, model_type, token_count):
        # get tokenizer
        tokenizer = tiktoken.encoding_for_model(model_type)

        # encode input string
        encoded = tokenizer.encode(input_str)

        # get text for first X tokens
        text = tokenizer.decode(encoded[:token_count])

        return text
