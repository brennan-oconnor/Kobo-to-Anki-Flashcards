#imports

import sqlite3
import requests
import csv
import time
import os
import re
from dotenv import load_dotenv

load_dotenv()
merriam_key = os.getenv("MERRIAM_KEY")

#create dictionary from SQLite database

def get_saved_words(file_path):

    connection = sqlite3.connect(file_path)
    cursor = connection.cursor()
    cursor.execute("""SELECT DISTINCT text FROM WordList""")
    results = cursor.fetchall()
    saved_words = []

    for row in results:
        word = row[0].strip(',.;!?:"\'()[]{}<>— ')
        word = word.lower()
        saved_words.append({"Word": word, "Definition": ""})

    connection.close()

    return saved_words

#get definitions from Merriam-Webster API

def get_merriam_definition(get_saved_words):

    session = requests.Session()

    for my_dict in get_saved_words:

        if my_dict["Definition"] == "":
            url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{my_dict['Word']}?key={merriam_key}"
            response = session.get(url)

            if response.status_code == 429:
                time.sleep(1)
                response = session.get(url)

            if response.status_code == 200:
                data = response.json()

                if isinstance(data[0], dict):
                    definition = []
                    for sub_dict in data[:2]:
                        definition.extend(sub_dict.get("shortdef", []))

                    result = "\n".join(definition)
                    my_dict["Definition"] = result

    return get_saved_words

# Get definition from free dictionary API

def get_wiki_definition(get_saved_words):

    session = requests.Session()

    for my_dict in get_saved_words:

        if my_dict["Definition"] == "":
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{my_dict['Word']}"
            response = session.get(url)

            if response.status_code == 429:
                time.sleep(1)
                response = session.get(url)

            if response.status_code == 200:
                data = response.json()

                if isinstance(data[0], dict):
                    definition = []
                    for meaning in data[0].get("meanings", []):
                        for definition_entry in meaning.get("definitions", [])[:2]:
                            definition.append(definition_entry.get("definition", ""))

                    result = "\n".join(definition)
                    my_dict["Definition"] = result

                else:
                    my_dict["Definition"] = "No definition found."

            else:
                my_dict["Definition"] = "No definition found."

    return get_saved_words

# Export to CSV

def write_to_csv(get_saved_words):

    with open('definitions.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        for dict in get_wiki_definition(get_saved_words):
            writer.writerow([dict["Word"], dict["Definition"]])

# Execute functions
dict_creation = get_saved_words("KoboReader.sqlite")
update_definitions = get_merriam_definition(dict_creation)
update_definitions = get_wiki_definition(dict_creation)
write_to_csv(update_definitions)
print("Done!")