from pyuml import ClassDiagram, Class

# Create a class diagram
diagram = ClassDiagram("Learning Disabilities Detection Web App")

# Dysgraphia module
with diagram.package("Dysgraphia"):
    user = Class("User")
    azure_api = Class("Azure Cognitive Vision API")
    bing_spellcheck = Class("Bing Spellcheck")
    dysgraphia_results = Class("Dysgraphia Detection Results")

    user.has(azure_api)
    azure_api.uses(bing_spellcheck)
    bing_spellcheck.uses(dysgraphia_results)

# Dyslexia module
with diagram.package("Dyslexia"):
    user = Class("User")
    pronunciation_test = Class("Pronunciation Test")
    phonetics_comparison = Class("Phonetics Comparison")
    dictation_test = Class("Dictation Test")
    text_comparison = Class("Text Comparison")
    dyslexia_results = Class("Dyslexia Detection Results")

    user.has(pronunciation_test)
    pronunciation_test.uses(phonetics_comparison)
    user.has(dictation_test)
    dictation_test.uses(text_comparison)
    phonetics_comparison.uses(dyslexia_results)
    text_comparison.uses(dyslexia_results)

# Dyscalculia module
with diagram.package("Dyscalculia"):
    user = Class("User")
    mathematical_quiz = Class("Mathematical Quiz")
    dyscalculia_results = Class("Dyscalculia Detection Results")

    user.has(mathematical_quiz)
    mathematical_quiz.uses(dyscalculia_results)

# Generate the UML diagram
diagram.generate()
