import re
import os
import time

from scrape_wiki import PW_Wiki_Scrape
from GPTUtil import GPTUtil
import g4f
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

# Load the wiki pages
PW_Wiki_Scrape.saveDefaultPages()

# Iterate over the sitemap
sitemap = PW_Wiki_Scrape.getSitemapCached()

def getSummary(page_name, page_json):
    prompt_summary = """# Goal:
You will be provided text from a fandom wiki page for the nation simulator game Politics And War. 
Take the information in `text` and summarize the factual information as concise dot points (start each line with `- `). 
Do not make anything up. 

# Text:
{text}

# Summary:"""

    categories = page_json['categories']
    # get main
    main = page_json['main']

    # combine page name, categories and main
    page = "### Page Name: " + str(page_name) + "\n### Categories:\n" + str(categories) + "\n### Blurb\n" + str(main)

        # get tokens from prompt
    max_tokens = 4096
    prompt_tokens = GPTUtil.getTokens(prompt_summary, "gpt-3.5-turbo")
    remaining_tokens = max_tokens - prompt_tokens

    # Add summary, main, headings and then as much of the page that will fit in the 4096 tokens
    page_json_copy = page_json.copy()
    page_json_copy.pop('categories', None)
    page_json_copy.pop('main', None)
    page = page + "\n" + "### Contents:" + "".join([f"\n- {key}" for key in page_json_copy.keys()])
    page_json_copy = "### Excerpt:\n" + str(page_json_copy)
    page = (page + "\n" + page_json_copy).replace("\\n", "\n")
    page = re.sub(r'\n+', '\n', page).replace("\\n", "\n").replace(r'\t+', '\t').replace(r'\s{2,}', ' ')

    page_first = GPTUtil.getFirst(page, "gpt-3.5-turbo", remaining_tokens)

    moderation_result = GPTUtil.getModeration(page_first)
    GPTUtil.checkModeration(moderation_result, page_first)

    # replace text in prompt
    prompt = prompt_summary.replace("{text}", page_first)

    result = None
    try:
        return GPTUtil.gpt3Request(prompt)
    except Exception as e:
        print(prompt)
        print("Error: " +  repr(e))
        return None

def saveSummary(page_name):
    page_json = PW_Wiki_Scrape.getPageJson(page_name)
    slug = PW_Wiki_Scrape.slugify(page_name)
    if page_json is None:
        print("Error: Page " + slug + " does not exist")
        return

    save_location = "json/summary/" + slug + ".txt"
    # if exists, skip
    if os.path.exists(save_location):
        print("Skipping " + slug + " as it already exists")
        return

    # if exists in json/summary/errors
    if os.path.exists("json/summary/error/" + slug + ".txt"):
        print("Skipping Error " + slug + " as it already exists in json/summary/error")
        return

    print("Summarizing page " + slug)

    summary = getSummary(page_name, page_json)

    raiseError = False

    if summary is None or summary == "" or ("- " not in summary):
        save_location = "json/summary/error/" + slug + ".txt"
        if summary is None:
            summary = ""
        # raiseError = True

    summary = ''.join([i if ord(i) < 128 or i == "\n" or i == "\t" else ' ' for i in summary])

    # create folder if not exists
    if not os.path.exists(os.path.dirname(save_location)):
        os.makedirs(os.path.dirname(save_location))
    with open(save_location, 'w+') as outfile:
        outfile.write(summary)

    if raiseError:
        raise Exception("Error: Summary for " + page_name + " is empty")

PW_Wiki_Scrape.stripNotPrintable()

all_categories = set()
# print the sections not needed
for page_name in sitemap:
    # load the json
    page_json = PW_Wiki_Scrape.getPageJson(page_name)
    if page_json is None:
        print("Error: Page " + page_name + " does not exist")
        continue
    # get categories
    categories = page_json['categories']
    if categories is None:
        print("Error: Categories is None for " + page_name)
        continue
    # iterate over categories
    for category in categories:
        # skip if ends with  more
        if category.endswith(" more"):
            continue
        all_categories.add(category)

# save a summary of each page
for page_name in sitemap:
    page_json = PW_Wiki_Scrape.getPageJson(page_name)
    if page_json is None:
        print("Error: Page " + page_name + " does not exist")
        continue
    categories = page_json['categories']

    # skip if any of the categories contains `Roleplay`
    if categories is not None and any("Roleplay" in s for s in categories):
        print("Skipping " + page_name + " as it contains Roleplay")
        continue

    saveSummary(page_name)
