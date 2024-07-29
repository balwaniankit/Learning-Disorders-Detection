import streamlit as st
from PIL import Image
import os
from textblob import TextBlob
import language_tool_python
import requests
import pandas as pd
import random
import speech_recognition as sr
import pyttsx3
import time
import eng_to_ipa as ipa
import streamlit.components.v1 as components
import form


from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

import time

from abydos.phonetic import Soundex, Metaphone, Caverphone, NYSIIS

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


# image to text API authentication
subscription_key_imagetotext = "c331e6137fc24de4adcecc707cd9570e"
endpoint_imagetotext = "https://mycoginitiveservices.cognitiveservices.azure.com/"
computervision_client = ComputerVisionClient(
    endpoint_imagetotext, CognitiveServicesCredentials(subscription_key_imagetotext))


# text correction API authentication
api_key_textcorrection = "c54fcfeb442340a68c2126dc3e4ed5a8"
endpoint_textcorrection = "https://api.bing.microsoft.com/v7.0/SpellCheck"

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

my_tool = language_tool_python.LanguageTool('en-US')

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# method for extracting the text


def image_to_text(path):
    read_image = open(path, "rb")
    read_response = computervision_client.read_in_stream(read_image, raw=True)
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status.lower() not in ['notstarted', 'running']:
            break
        time.sleep(5)

    text = []
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                text.append(line.text)

    return " ".join(text)

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# method for finding the spelling accuracy


def spelling_accuracy(extracted_text):
    spell_corrected = TextBlob(extracted_text).correct()
    return ((len(extracted_text) - (levenshtein(extracted_text, spell_corrected)))/(len(extracted_text)+1))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# method for gramatical accuracy


def gramatical_accuracy(extracted_text):
    spell_corrected = TextBlob(extracted_text).correct()
    correct_text = my_tool.correct(spell_corrected)
    extracted_text_set = set(spell_corrected.split(" "))
    correct_text_set = set(correct_text.split(" "))
    n = max(len(extracted_text_set - correct_text_set),
            len(correct_text_set - extracted_text_set))
    return ((len(spell_corrected) - n)/(len(spell_corrected)+1))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# percentage of corrections


def percentage_of_corrections(extracted_text):
    data = {'text': extracted_text}
    params = {
        'mkt': 'en-us',
        'mode': 'proof'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Ocp-Apim-Subscription-Key': api_key_textcorrection,
    }
    response = requests.post(endpoint_textcorrection,
                             headers=headers, params=params, data=data)
    json_response = response.json()
    return len(json_response['flaggedTokens'])/len(extracted_text.split(" "))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# percentage of phonetic accuracy


def percentage_of_phonetic_accuraccy(extracted_text: str):
    soundex = Soundex()
    metaphone = Metaphone()
    caverphone = Caverphone()
    nysiis = NYSIIS()
    spell_corrected = TextBlob(extracted_text).correct()

    extracted_text_list = extracted_text.split(" ")
    extracted_phonetics_soundex = [soundex.encode(
        string) for string in extracted_text_list]
    extracted_phonetics_metaphone = [metaphone.encode(
        string) for string in extracted_text_list]
    extracted_phonetics_caverphone = [caverphone.encode(
        string) for string in extracted_text_list]
    extracted_phonetics_nysiis = [nysiis.encode(
        string) for string in extracted_text_list]

    extracted_soundex_string = " ".join(extracted_phonetics_soundex)
    extracted_metaphone_string = " ".join(extracted_phonetics_metaphone)
    extracted_caverphone_string = " ".join(extracted_phonetics_caverphone)
    extracted_nysiis_string = " ".join(extracted_phonetics_nysiis)

    spell_corrected_list = spell_corrected.split(" ")
    spell_corrected_phonetics_soundex = [
        soundex.encode(string) for string in spell_corrected_list]
    spell_corrected_phonetics_metaphone = [
        metaphone.encode(string) for string in spell_corrected_list]
    spell_corrected_phonetics_caverphone = [
        caverphone.encode(string) for string in spell_corrected_list]
    spell_corrected_phonetics_nysiis = [nysiis.encode(
        string) for string in spell_corrected_list]

    spell_corrected_soundex_string = " ".join(
        spell_corrected_phonetics_soundex)
    spell_corrected_metaphone_string = " ".join(
        spell_corrected_phonetics_metaphone)
    spell_corrected_caverphone_string = " ".join(
        spell_corrected_phonetics_caverphone)
    spell_corrected_nysiis_string = " ".join(spell_corrected_phonetics_nysiis)

    soundex_score = (len(extracted_soundex_string)-(levenshtein(extracted_soundex_string,
                     spell_corrected_soundex_string)))/(len(extracted_soundex_string)+1)
    # print(spell_corrected_soundex_string)
    # print(extracted_soundex_string)
    # print(soundex_score)
    metaphone_score = (len(extracted_metaphone_string)-(levenshtein(extracted_metaphone_string,
                       spell_corrected_metaphone_string)))/(len(extracted_metaphone_string)+1)
    # print(metaphone_score)
    caverphone_score = (len(extracted_caverphone_string)-(levenshtein(extracted_caverphone_string,
                        spell_corrected_caverphone_string)))/(len(extracted_caverphone_string)+1)
    # print(caverphone_score)
    nysiis_score = (len(extracted_nysiis_string)-(levenshtein(extracted_nysiis_string,
                    spell_corrected_nysiis_string)))/(len(extracted_nysiis_string)+1)
    # print(nysiis_score)
    return ((0.5*caverphone_score + 0.2*soundex_score + 0.2*metaphone_score + 0.1 * nysiis_score))*100

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


def get_feature_array(path: str):
    feature_array = []
    extracted_text = image_to_text(path)
    feature_array.append(spelling_accuracy(extracted_text))
    feature_array.append(gramatical_accuracy(extracted_text))
    feature_array.append(percentage_of_corrections(extracted_text))
    feature_array.append(percentage_of_phonetic_accuraccy(extracted_text))
    return feature_array

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


def generate_csv(folder: str, label: int, csv_name: str):
    arr = []
    for image in os.listdir(folder):
        path = os.path.join(folder, image)
        feature_array = get_feature_array(path)
        feature_array.append(label)
        # print(feature_array)
        arr.append(feature_array)
        print(feature_array)
    print(arr)
    pd.DataFrame(arr, columns=["spelling_accuracy", "gramatical_accuracy", " percentage_of_corrections",
                 "percentage_of_phonetic_accuraccy", "presence_of_dyslexia"]).to_csv(csv_name)

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''


def score(input):
    if input[0] <= 96.40350723266602:
        var0 = [0.0, 1.0]
    else:
        if input[1] <= 99.1046028137207:
            var0 = [0.0, 1.0]
        else:
            if input[2] <= 2.408450722694397:
                if input[2] <= 1.7936508059501648:
                    var0 = [1.0, 0.0]
                else:
                    var0 = [0.0, 1.0]
            else:
                var0 = [1.0, 0.0]
    return var0

# '''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# deploying the model


st.set_page_config(page_title="Learning Disabilities Webapp")

hide_menu_style = """
<style>
#MainMenu {visibility: hidden; }
footer {visibility: hidden; }
</style>
"""


st.markdown(hide_menu_style, unsafe_allow_html=True)
st.title("Learning Disabilities Web App")

tab2, tab3, tab5, tab6= st.tabs(["Writing", "Pronunciation", "Dictation", "Dyscalulia Test"])


# with tab1: #Parental Questionnaire
#         dyslexia_questions = [
#             "Does your child struggle with reading words accurately and fluently?",
#             "Does your child often confuse similar-sounding words, such as 'cat' and 'bat'?",
#             "Does your child have difficulty spelling common words?",
#             "Does your child find it challenging to follow written instructions?",
#             "Does your child frequently lose their place while reading?"
#         ]

#         dysgraphia_questions = [
#             "Does your child struggle with handwriting, making it hard to read their writing?",
#             "Does your child have difficulty forming letters and numbers correctly?",
#             "Does your child experience pain or discomfort while writing or drawing for an extended period?",
#             "Does your child often reverse letters or numbers, like writing 'b' instead of 'd'?",
#             "Does your child find it challenging to organize their thoughts in writing?"
#         ]

#         dyscalculia_questions = [
#             "Does your child have difficulty understanding and working with numbers?",
#             "Does your child find it challenging to remember basic math facts, such as addition and subtraction?",
#             "Does your child struggle with telling time or understanding concepts like 'greater than' and 'less than'?",
#             "Does your child have difficulty solving word problems in math?",
#             "Does your child often mix up mathematical symbols or transpose numbers, like writing '35' instead of '53'?"
#         ]

#         # Function to evaluate responses
#         def evaluate_responses(questions, responses):
#             yes_count = 0
#             for i, response in enumerate(responses):
#                 if response.lower() == "yes":
#                     yes_count += 1
#             return yes_count

#         # Create a Streamlit app for the Parental Questionnaire
#         st.title("Parental Questionnaire")

#         st.subheader("Please answer the following questions about your child:")

#         dyslexia_responses = []
#         dysgraphia_responses = []
#         dyscalculia_responses = []

#         # Collect responses for each category
#         # Collect responses for each category
#         for i, question in enumerate(dyslexia_questions):
#             st.write(f"{i + 1}. {question}")
#             response = st.text_input(f"Your response ({i + 1}):", key=f"dyslexia_response_{i}").strip().lower()
#             dyslexia_responses.append(response)

#         for i, question in enumerate(dysgraphia_questions):
#             st.write(f"{i + 1}. {question}")
#             response = st.text_input(f"Your response ({i + 1}):", key=f"dysgraphia_response_{i}").strip().lower()
#             dysgraphia_responses.append(response)

#         for i, question in enumerate(dyscalculia_questions):
#             st.write(f"{i + 1}. {question}")
#             response = st.text_input(f"Your response ({i + 1}):", key=f"dyscalculia_response_{i}").strip().lower()
#             dyscalculia_responses.append(response)

#         # Add unique key to the submit button
#         if st.button("Submit Parental Questionnaire"):
#             # Evaluate responses for each category
#             dyslexia_yes_count = evaluate_responses(dyslexia_questions, dyslexia_responses)
#             dysgraphia_yes_count = evaluate_responses(dysgraphia_questions, dysgraphia_responses)
#             dyscalculia_yes_count = evaluate_responses(dyscalculia_questions, dyscalculia_responses)

#             # Suggest further assessment based on responses for each disability
#             if dyslexia_yes_count > 2:
#                 st.write("Based on your responses, we recommend that your child takes further assessments for dyslexia.")
            
#             if dysgraphia_yes_count > 2:
#                 st.write("Based on your responses, we recommend that your child takes further assessments for dysgraphia.")
            
#             if dyscalculia_yes_count > 2:
#                 st.write("Based on your responses, we recommend that your child takes further assessments for dyscalculia.")

with tab2: #Writing
    st.title(" Detection Using Handwriting Samples")
    # st.write("This is a simple web app that works based on machine learning techniques. This application can predict the presence of dyslexia from the handwriting sample of a person.")
    with st.container():
        st.write("---")
        image = st.file_uploader("Upload the handwriting sample that you want to test", type=["jpg"])
        if image is not None:
            st.write("Please review the image selected")
            st.write(image.name)
            image_uploaded = Image.open(image)
            image_uploaded.save("temp.jpg")
            st.image(image_uploaded, width=224)

        if st.button("Predict", help="click after uploading the correct image"):
            try:
                feature_array = get_feature_array("temp.jpg")
                result = score(feature_array)
                if result[0] == 1:
                    st.write("From the tests on this handwriting sample there is slim chance that this child is suffering from dysgraphia")
                else:
                    st.write("From the tests on this handwriting sample there is high chance that this child is suffering from dysgraphia")
            except:
                st.write("Something went wrong at the server end please refresh the application and try again")

with tab3: #Pronunciation

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    def get_10_word_array(level: int):
        if (level == 1):
            voc = pd.read_csv("data\elementary_voc.csv")
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10)
            return selected_list
        elif(level == 2):
            voc = pd.read_csv("data\intermediate_voc.csv")
            # return (type(voc))
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10) 
            return selected_list
        else:
            return ([])
    
#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def listen_for(seconds: int):
        with sr.Microphone() as source:
            r = sr.Recognizer()
            print("Recognizing...")
            audio_data = r.record(source, seconds)
            text = r.recognize_google(audio_data)
            print(text)
            return text
 
 #'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def talk(Word : str):
        engine = pyttsx3.init()
        engine.say(Word)
        engine.runAndWait()
    
#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # j+1 instead of j since previous_row and current_row are one character longer
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    def check_pronounciation(str1 : str , str2: str):
        s1 = ipa.convert(str1)
        s2 = ipa.convert(str2)
        return levenshtein(s1,s2)

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''
    
    def dictate_10_words(level : int):
        words = get_10_word_array(level)
        for i in words:
            talk(i)
            time.sleep(8)
        return words

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    def random_seq():
        list = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0','1','2','3','4','5','6','7','8','9']
        return " ".join(random.sample(list, 5))

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    # Function to get a paragraph from a CSV file
    def get_paragraph(level: int):
        if level == 1:
            paragraph_df = pd.read_csv("data/level1_paragraph.csv")
        elif level == 2:
            paragraph_df = pd.read_csv("data/level2_paragraph.csv")
        else:
            return ""

        paragraph_columns_list = paragraph_df.columns.tolist()
        random_column = random.choice(paragraph_columns_list)
        paragraph = paragraph_df[random_column].iloc[0]
        return paragraph

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

# Function to get a sentences from a CSV file
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

#'''-------------------------------------------------------------------------------------------------------------------------------------------------------------------------'''

    # tab1, tab2= st.tabs(["Home", "pronounciation test"])
    tab1, tab2, tab3, tab4 = st.tabs(["Home", "Words Pronunciation Test", "Sentence Pronounciation Test" , "Paragraph Pronunciation Test"])

    level = 1


    with tab1:
        st.header("A Test for Dyslexia")
        st.subheader("Navigate through the tabs to take the test.")
        option = st.selectbox(
            "You need to speak into the system's microphone. Kindly speak aloud. Select Yes when ready to take the test", ('Yes', 'No'), key= "pro")
        if option=='Yes':
            level = 1
        elif option == 'No':
            level = 2
        

    with tab2:
        st.header("The pronounciation and reading ability of the user will be measured here")
        pronounciation_test = st.button("Start a pronounciation test")
        pronounciation_accuracy = 0
        
        if pronounciation_test:
            st.subheader("Please repeat the following words you only have 10 seconds to do that.")
         
            arr = get_10_word_array(level)
            for i in range(len(arr)):
                arr[i] = str(arr[i])
                arr[i] = arr[i].strip()

            str_displayed = str(" ".join(arr))
            words = st.text(">> " + "\n>>".join(arr) )
            status = st.text("listening........")
            str_pronounced = listen_for(10)
            status.write("Time up! calculating accuracy......")
        
        
            pronounciation_accuracy = 1- (check_pronounciation(str_displayed, str_pronounced)/len(str_displayed))
        
            st.write("the pronounciation accuracy is: " + str(pronounciation_accuracy*100))
            st.write("original : " + str_displayed)
            st.write("original phonetics: " + ipa.convert(str_displayed) )
            st.write("\npronounced: " + str_pronounced)
            st.write("\npronounced phonetics: " + ipa.convert(str_pronounced))

    with tab3:
        st.header("Sentence Pronunciation Test")
        sentence_test = st.button("Start Sentence Pronunciation Test")
        sentence_accuracy = 0

        if sentence_test:
            st.subheader("Please repeat the following sentence within 5 seconds.")
            selected_sentence = get_sentence(level)

            if selected_sentence:
                st.write(selected_sentence)

                status = st.text("Listening...")
                audio_data = listen_for(5)
                status.write("Time up! Calculating accuracy...")

                sentence_accuracy = 1 - (check_pronounciation(selected_sentence, audio_data) / len(selected_sentence))

                st.write("The pronunciation accuracy is:", sentence_accuracy*100)
                status.write("original : " + ipa.convert(selected_sentence))
                st.write("\npronounced: " + audio_data)
                st.write("\npronounced IPA : " + ipa.convert(audio_data))

    with tab4:
        st.header("Paragraph Pronunciation Test")
        paragraph_test = st.button("Start Paragraph Pronunciation Test")
        paragraph_accuracy = 0

        if paragraph_test:
            st.subheader("Please repeat the following paragraph within 15 seconds.")
            selected_paragraph = get_paragraph(level)
            
            if selected_paragraph:
                st.write(selected_paragraph)

                status = st.text("Listening...")
                audio_data = listen_for(12)
                status.write("Time up! Calculating accuracy...")

                paragraph_accuracy = 1 - (check_pronounciation(selected_paragraph, audio_data) / len(selected_paragraph))

                st.write("The pronunciation accuracy is:", paragraph_accuracy*100)
                status.write("original : " + ipa.convert(selected_paragraph))
                st.write("\npronounced: " + audio_data)
                st.write("\npronounced IPA : " + ipa.convert(audio_data))
                   
        
with tab5: #Dictation
    def talk(Word : str):
        engine = pyttsx3.init()
        engine.say(Word)
        engine.runAndWait()
    
    def get_10_word_array(level: int):
        if (level == 1):
            voc = pd.read_csv("data\elementary_voc.csv")
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10)
            return selected_list
        
        elif(level == 2):
            voc = pd.read_csv("data\elementary_voc.csv")
            arr = voc.squeeze().to_numpy()
            selected_list = random.sample(list(arr), 10) 
            return selected_list
        else:
            return ([])
    
    def dictate_10_words(level : int):
        words = get_10_word_array(level)
        for i in words:
            talk(i)
            time.sleep(5)
        return words

    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]


    def check_written_words(str1 : str , str2: str):
        s1 = ipa.convert(str1)
        s2 = ipa.convert(str2)
        return levenshtein(s1,s2)
    
    level = 1
    cb = st.checkbox('start dictation')
    if cb:
        option = st.selectbox("It is advisable to connect your headphones to listen the words properly. Once you connect your headphones, select yes from the dropdown", ('Yes', 'No'), key= "pro1")
        if option=='Yes':
            level = 1
        elif option == 'No':
            level = 2

        form = st.form(key='my_form')
        w1 = form.text_input(label='word1') 
        w2 = form.text_input(label='word2')
        w3 = form.text_input(label='word3')
        w4 = form.text_input(label='word4')
        w5 = form.text_input(label='word5')
        w6 = form.text_input(label='word6')
        w7 = form.text_input(label='word7')
        w8 = form.text_input(label='word8')
        w9 = form.text_input(label='word9')
        w10 = form.text_input(label='word10')
        submit_button = form.form_submit_button(label='Submit')



        @st.cache
        def bind_socket():
        # This function will only be run the first time it's called
            dictated_words = dictate_10_words(level)
            return dictated_words


        dictated_words = bind_socket() 
# print(dictated_words)

        if submit_button:
            typed_words = []
            typed_words.append(w1)
            typed_words.append(w2)
            typed_words.append(w3)
            typed_words.append(w4)
            typed_words.append(w5)
            typed_words.append(w6)
            typed_words.append(w7)
            typed_words.append(w8)
            typed_words.append(w9)
            typed_words.append(w10)

            print(typed_words)
            print(dictated_words)

            # st.write("your dictation score is (lesser the better) : " , levenshtein(" ".join(typed_words) , " ".join(dictated_words)))
            # st.write("dictated words: " + " ".join(dictated_words))
            # st.write("typed words: " + " ".join(typed_words))
            # laven_distance = levenshtein(" ".join(typed_words) , " ".join(dictated_words))
            dictation_accuracy = 1 - (check_written_words(" ".join(typed_words) , " ".join(dictated_words)) / len(" ".join(typed_words)))
            # dictation_accuracy = 1 - (check_written_words(" ".join(dictated_words), " ".join(map(str, typed_words))) / len(" ".join(dictated_words)))
            st.write("The dictation accuracy is:", dictation_accuracy)
            st.write("dictated words: " + " ".join(dictated_words))
            st.write("\noriginal : " + ipa.convert(" ".join(typed_words)))
            st.write("\ntyped words: " + " ".join(typed_words))
            st.write("\npronounced: " + ipa.convert(" ".join(dictated_words)))

with tab6: #Dyscalulia Test
        questions_1_4 = {
            "Syllabus-based Problems": [
                {
                    "question": "1. Compare and tell which number is bigger or smaller : 6070 , 8079",
                    "options": ["a) Bigger, Smaller", "b) Smaller, Bigger", "c) Both are equal"],
                    "correct_answer": "b) Smaller, Bigger"
                },
                {
                    "question": "2. Ajay deposited 18,000 in one bank and 15,000 in another. What is the total amount of money deposited in the banks ?",
                    "options": ["a) 30,000", "b)33,000", "c) 35,000", "d) 31,000"],
                    "correct_answer": "b) 33,000"
                },
                {
                    "question": "3. A bicycle cost Rs 1220. What is the cost of 38 bicycles?",
                    "options": ["a) 46360", "b) 45260", "c) 46700", "d) 47500"],
                    "correct_answer": "a) 46360"
                },
                {
                    "question": "4. How many hours are there in 300 minutes?",
                    "options": ["a) 9", "b) 8", "c) 2", "d) 5"],
                    "correct_answer": "d) 5"
                },
                {
                    "question": "5. Ajay has 9 notes. The total value of those notes is Rs 500. Which notes does Ajay have and how many of each?",
                    "options": ["a) 8 notes of Rs 50 and 1 note of Rs 100", "b) 2 notes of Rs 100, 2 notes of Rs 50 and 5 notes of Rs 20", "c) 3 notes of Rs 50 and 6 notes of Rs 20", "d) 4 notes of Rs 100 and 5 notes of Rs 10"],
                    "correct_answer": "a) 8 notes of Rs 50 and 1 note of Rs 100"
                },
                {
                    "question": "6. In a certain year, the Ganesh festival started on the 9th of September and ended on the 18th of September. For how many days was the festival celebrated?",
                    "options": ["a) 7", "b) 11", "c) 12", "d) 10"],
                    "correct_answer": "d) 10"
                },
                {
                    "question": "7. If 1 litre of petrol costs Rs 70, how much do two and a half litres of petrol cost",
                    "options": ["a) Rs.200", "b) Rs.150", "c) Rs.250", "d) Rs.175"],
                    "correct_answer": "d) Rs.175"
                },
                {
                    "question": "8. The sides of a rectangular field are 150m, 120m, 150m and 120m. Find the perimeter of the field.",
                    "options": ["a) 500m", "b) 540m", "c) 520m", "d) 550m"],
                    "correct_answer": "b) 540"
                },
                {
                    "question": "9. Convert 8 kilometres(km) into metres(m)",
                    "options": ["a)80m ", "b)800m ", "c)8000m ", "d)8m "],
                    "correct_answer": "c)8000m "
                },
                {
                    "question": "10.Count the odd numbers from the list: 35, 67, 32, 30, 43, 34, 51, 56, 88, 79",
                    "options": ["a) 7", "b) 3", "c) 5", "d) 2"],
                    "correct_answer": "c) 5"
                },
            ]
        }

        st.title("Dyscalculia Assessment Test")
        selected_questions = questions_1_4

        user_responses = {}  # Dictionary to store user responses

        for section, section_questions in selected_questions.items():
            st.subheader(f"{section} Questions:")
            for i, question_data in enumerate(section_questions):
                question = question_data["question"]
                options = question_data["options"]
                st.write(question)
                user_choice = st.radio(f"Select an option ({section}-{i + 1})", options)
                user_responses[f"{section}-{i + 1}"] = user_choice  # Store user responses

        if st.button("Submit"):
            # Calculating the user's score
            score = 0
            for key, user_answer in user_responses.items():
                for section_questions in selected_questions.values():
                    for question_data in section_questions:
                        if user_answer == question_data["correct_answer"]:
                            score += 1

            st.write(f"Your score: {score}/{len(user_responses)}")

            # # Classify the user's score
            # if score <= 4:
            #     st.write("From the tests, the score is 'Low Average.' There are high chances that this child is suffering from dyscalculia.")
            # elif 5 <= score <= 7:
            #     st.write("From the tests, the score is 'Average.' There might be or might not be chances that this child is suffering from dyscalculia.")
            # else:
            #     st.write("From the tests, the score is 'High Average.' There is a slim chance that this child is suffering from dyscalculia.")


