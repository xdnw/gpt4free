import urllib

import unicodedata

import json
import os
import re

import requests
from bs4 import BeautifulSoup

class PW_Wiki_Scrape:
    SKIP_PAGES = set()
    SKIP_PAGES.add("the_union_of_eos")  # uses n word
    SKIP_PAGES.add("doc")  # meta sub page
    SKIP_PAGES.add("python")  # meta sub page
    SKIP_PAGES.add("vietnamese_civil_war_1949-55") # no content
    SKIP_PAGES.add("pw-imperator") # flagged as inappropriate by openai

    @staticmethod
    def slugify(value, allow_unicode=False):
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    @staticmethod
    def getCategoryPages(categories):
        url = "https://politicsandwar.fandom.com/wiki/Category:" + categories

        while url:
            # div class="category-page__members"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            pages = {}

            # get div
            div = soup.find("div", {"class": "category-page__members"})
            # get all links
            links = div.find_all("a")
            for link in links:
                # skip if href is empty or none
                if not link["href"]:
                    continue
                # skip if link text does not contain any letters
                if not any(c.isalpha() for c in link.text):
                    continue

                # skip if title contains Category:
                if "Category:" in link.text or "Category:" in link["href"]:
                    continue
                # add to pages
                pages[link.text] = link["href"]

            # Find the link to the next page
            nav_div = soup.find("div", {"class": "category-page__pagination"})
            if nav_div is not None:
                next_link = nav_div.find("a", {"class": "category-page__pagination-next"})
            else:
                next_link = None

            # If there is a next page, update the URL and continue
            if next_link is not None:
                url = next_link["href"]
            else:
                url = None

        return pages

    @staticmethod
    def getAllPages():
        # map of page name to page url
        pages = {}

        url = "https://politicsandwar.fandom.com/wiki/Special:AllPages"
        while url:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            link_div = soup.find("ul", {"class": "mw-allpages-chunk"})

            # Find all the links within the div
            links = link_div.find_all("a")

            # Print the text of each link
            for link in links:

                # skip if href is empty or none
                if not link["href"]:
                    continue
                # skip if link text does not contain any letters
                if not any(c.isalpha() for c in link.text):
                    continue

                # add to pages
                pages[link.text] = link["href"]


            # Find the link to the next page
            nav_div = soup.find("div", {"class": "mw-allpages-nav"})

            if nav_div is not None:
                next_link = nav_div.find("a", string=lambda s: s.startswith("Next page"))
            else:
                next_link = None

            # If there is a next page, update the URL and continue
            if next_link is not None:
                url = "https://politicsandwar.fandom.com" + next_link["href"]
            else:
                url = None

            # If there is a next page, update the URL and continue
            if next_link:
                url = "https://politicsandwar.fandom.com" + next_link["href"]
            else:
                url = None
        return pages

    @staticmethod
    def getTable(blocks, page_element, title):
        # Find all the rows in the table
        rows = page_element.find_all('tr')

        # page title from url /
        key = urllib.parse.unquote(title) + ".InfoBox"
        reset_key = False
        # Loop through each row and extract the key/value pairs

        for row in rows:
            # Get the cells in the row
            cells = row.find_all(['td', "th"])
            # If there are cells in the row, extract the key/value pairs

            if cells:
                # skip if cells length is less than 2
                if len(cells) == 1:
                    if reset_key:
                        reset_key = False
                        key = cells[0].get_text().strip()
                        key = ''.join([i if ord(i) < 128 else ' ' for i in key])
                    # only if key is empty
                    continue
                if len(cells) < 2:
                    continue

                reset_key = True
                # The first cell is the key
                left = cells[0].get_text().strip()
                # The subsequent cells are the values
                right = [cell.get_text().strip() for cell in cells[1:]]
                combined = str((str(left), str(right)))
                # create list if not exist and append combined to blocks[key]
                blocks.setdefault(key, []).append(combined)

    @staticmethod
    def extractSections(url):
        response = requests.get(url)
        page_title = url.split("/")[-1]
        print("Extracting: " + url)

        soup = BeautifulSoup(response.content, "html.parser")

        # remove`nowraplinks collapsible autocollapse navbox-subgroup`
        for div in soup.find_all("div", {"class": "nowraplinks collapsible autocollapse navbox-subgroup"}):
            div.decompose()

        blocks = {}

        # get content of page-header__categories class
        categories = soup.find("div", {"class": "page-header__categories"})
        if categories is not None:
            blocks["categories"] = [category.text.strip() for category in categories.find_all("a")]


        # get mw-parser-output div
        div = soup.find("div", {"class": "mw-parser-output"})
        # get second child
        # if length is sufficient
        if len(div.contents) > 2:
            # iterate over div.contents and find first table with more than 1 row
            found_child = div.contents[2]
            for child in div.contents:
                if child.name == "table":
                    found_child = child
                    rows = child.find_all('tr')
                    if len(rows) > 1:
                        break

            # if first child is table
            if found_child and found_child.name == "table":
                PW_Wiki_Scrape.getTable(blocks, found_child, page_title)
            else:
                # find first table element infobox
                infobox = div.find("table", {"class": "infobox"})
                #  if exists get table
                if infobox is not None:
                    PW_Wiki_Scrape.getTable(blocks, infobox, page_title)

        # get the content before the first h2 inside mw-parser-output
        content = ""
        for element in div.contents:
            if element.name == "table":
                continue
            if element.name == "h2" or element.name == "h3" or element.name == "div":
                break
            content += str(element.text.strip())

        # trim content
        blocks["main"] = content.strip()

        for heading in soup.find_all(["h2", "h3"]):  # find separators, in this case h2 and h3 nodes
            if heading.text == "Related links":
                break
            values = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ["h2", "h3"]:  # iterate through siblings until separator is encountered
                    break
                text = sibling.text.strip()
                if text == "":
                    continue
                values.append(text)
            if heading.name == "h2":
                # if values is not, or is empty list or is empty string continue
                if not values or values == "" or values == []:
                    continue
                key = heading.text
                key = ''.join([i if ord(i) < 128 else ' ' for i in key])
                blocks[key] = values
            elif heading.name == "h3":
                h2_heading = heading.find_previous_sibling("h2")
                if h2_heading is not None:
                    h2_text = h2_heading.text
                    h3_text = heading.text

                    # skip if values is empty
                    if not values or values == "" or values == []:
                        continue

                    key = f"{h2_text}.{h3_text}"
                    key = ''.join([i if ord(i) < 128 else ' ' for i in key])
                    blocks[key] = values

        return blocks

    @staticmethod
    def saveToJson(page_name, url):
        blocks = PW_Wiki_Scrape.extractSections(url)
        slug = PW_Wiki_Scrape.slugify(page_name)

        # test
        if not os.path.exists("json/"):
            os.makedirs("json/")

        # save to json
        with open(f"json/{slug}.json", "w+") as outfile:
            json.dump(blocks, outfile, indent=4)

    @staticmethod
    def fetchDefaultPages():
        pages_to_save = set()
        pages_to_save.add("Frequently_Asked_Questions")
        pages_to_save.add("Paperless")

        categories_to_save = ["Wars", "Alliances", "Treaties", "Guides", "Mechanics", "API"]
        # iterate categories
        for category in categories_to_save:
            # get the pages from each category
            pages = PW_Wiki_Scrape.getCategoryPages(category)
            # iterate pages--
            for page in pages:
                # get page name
                page_name = page.split("/")[-1]
                page_name = urllib.parse.unquote(page_name)
                # remove bad chars
                page_name = re.sub(r'[^\w\s-]', '', page_name)
                # replace spaces with _
                page_name = page_name.replace(" ", "_")
                # save to json
                pages_to_save.add(page_name)
        # save to sitemap.json
        with open("sitemap.json", "w+") as outfile:
            json.dump(list(pages_to_save), outfile, indent=4)

    @staticmethod
    def getSitemapCached():
        # if file not exists, fetch and save to sitemap.json
        filename = "sitemap.json"
        if not os.path.exists(filename):
            print("Fetching default pages")
            PW_Wiki_Scrape.fetchDefaultPages()

        with open("sitemap.json", "r") as infile:
            print("Loading sitemap.json")
            return json.load(infile)

    @staticmethod
    def saveDefaultPages():
        _pages_to_save = PW_Wiki_Scrape.getSitemapCached()

        # iterate each page
        for page in _pages_to_save:
            url = f"https://politicsandwar.fandom.com/wiki/{urllib.parse.quote(page)}"
            # strip non filename chars
            slug = PW_Wiki_Scrape.slugify(page)

            if slug in PW_Wiki_Scrape.SKIP_PAGES:
                continue

            # check if file exists
            if os.path.exists(f"json/{slug}.json"):
                print(f"Skipping {slug}.json")
                continue

            # save to json
            print(f"Saving {slug}.json")
            PW_Wiki_Scrape.saveToJson(page, url)

    @staticmethod
    def getLongestKeyValue():
        # iterate over all files in json
        # load the json
        # iterate keys/values
        # get the longest key and value

        longest_key_len = 0
        longest_key = ""

        longest_value_len = 0
        longest_value = ""

        for filename in os.listdir("json"):
            with open(f"json/{filename}", "r") as infile:
                data = json.load(infile)
                for key, value in data.items():
                    keyStr = str(key)
                    valueStr = str(value)
                    if len(keyStr) > longest_key_len:
                        longest_key_len = len(keyStr)
                        longest_key = keyStr
                    if len(valueStr) > longest_value_len:
                        longest_value_len = len(valueStr)
                        longest_value = valueStr

        print(f"Longest key: {longest_key} ({longest_key_len})")
        print(f"Longest value: {longest_value} ({longest_value_len})")

    @staticmethod
    def stripNotPrintable():
        # load each file from `json_old`
        # strip all characters that dont print
        # save to `json` folder
        for filename in os.listdir("json/"):
            # skip if dir
            if os.path.isdir(filename):
                continue
            if not filename.endswith(".json"):
                continue
            new_data = {}
            with open(f"json/{filename}", "r") as infile:
                data = json.load(infile)
                for key, value in data.items():
                    # strip all characters that dont print
                    key = ''.join([i if ord(i) < 128 else ' ' for i in key])
                    # if the key doesnt contain any letters or numbers, remove it
                    if not any(char.isalnum() for char in key):
                        continue


                    # value might be a list or string
                    if isinstance(value, list):
                        new_value = []
                        for v in value:
                            # skip anything with `v · d · e` in it
                            if "v · d · e" in v:
                                continue
                            # allow newline and tabs in values
                            v = ''.join([i if ord(i) < 128 or i == "\n" or i == "\t" else ' ' for i in v])
                            new_value.append(v)
                        value = new_value
                    else:
                        # allow newline and tabs in values
                        value = ''.join([i if ord(i) < 128 or i == "\n" or i == "\t" else ' ' for i in value])
                    new_data[key] = value
            # save to `json` folder overwrite existing
            with open(f"json/{filename}", "w+") as outfile:
                json.dump(new_data, outfile, indent=4)

    @staticmethod
    def getPageJson(page_name):
        file_name = PW_Wiki_Scrape.slugify(page_name)
        if file_name in PW_Wiki_Scrape.SKIP_PAGES:
            return None

        # if not exists fetch and save
        if not os.path.exists(f"json/{file_name}.json"):
            url = f"https://politicsandwar.fandom.com/wiki/{urllib.parse.quote(page_name)}"
            PW_Wiki_Scrape.saveToJson(page_name, url)

        # load json
        with open(f"json/{file_name}.json", "r") as infile:
            return json.load(infile)

