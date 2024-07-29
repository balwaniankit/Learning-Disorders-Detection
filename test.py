import pandas as pd
import random

def get_sentence(level: int):
    if level == 1:
        sentence_df = pd.read_csv("data/level1_sentence.csv")
    elif level == 2:
        sentence_df = pd.read_csv("data/level2_sentence.csv")
    else:
        return ""

    # Convert Index object to a list
    columns_list = sentence_df.columns.tolist()

    # Choose a random column from the list of columns
    random_column = random.choice(columns_list)

    # Get the sentence from the selected column
    sentence = sentence_df[random_column].iloc[0]
    return sentence

level = 1
selected_sentence = get_sentence(level)
print(selected_sentence)
