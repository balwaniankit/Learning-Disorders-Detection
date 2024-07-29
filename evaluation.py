from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import os

# Set your Azure Computer Vision API credentials
subscription_key = "c331e6137fc24de4adcecc707cd9570e"
endpoint = "https://mycoginitiveservices.cognitiveservices.azure.com/"

# Initialize the Computer Vision client
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Function to perform OCR on an image
def ocr_image(image_path):
    with open(image_path, "rb") as image_stream:
        ocr_results = computervision_client.recognize_printed_text_in_stream(image_stream)
    return ocr_results

# Function to evaluate OCR performance on a dataset
def evaluate_ocr_performance(dataset_path):
    dysgraphic_correct = 0
    non_dysgraphic_correct = 0
    dysgraphic_total = 0
    non_dysgraphic_total = 0

    dysgraphic_images_path = os.path.join(dataset_path, "dyslexic")
    non_dysgraphic_images_path = os.path.join(dataset_path, "non_dyslexic")

    # Evaluate dysgraphic images
    for image_file in os.listdir(dysgraphic_images_path):
        image_path = os.path.join(dysgraphic_images_path, image_file)
        ocr_results = ocr_image(image_path)
        detected_text = ''.join([line.text for region in ocr_results.regions for line in region.lines])
        if "dysgraphic" in detected_text.lower():
            dysgraphic_correct += 1
        dysgraphic_total += 1

    # Evaluate non-dysgraphic images
    for image_file in os.listdir(non_dysgraphic_images_path):
        image_path = os.path.join(non_dysgraphic_images_path, image_file)
        ocr_results = ocr_image(image_path)
        detected_text = ''.join([line.text for region in ocr_results.regions for line in region.lines])
        if "dysgraphic" not in detected_text.lower():
            non_dysgraphic_correct += 1
        non_dysgraphic_total += 1

    # Calculate accuracy
    dysgraphic_accuracy = dysgraphic_correct / dysgraphic_total
    non_dysgraphic_accuracy = non_dysgraphic_correct / non_dysgraphic_total

    print("Dysgraphic Accuracy: {:.2f}%".format(dysgraphic_accuracy * 100))
    print("Non-Dysgraphic Accuracy: {:.2f}%".format(non_dysgraphic_accuracy * 100))

# Provide the path to your labeled dataset
dataset_path = "data"

# Evaluate OCR performance on the dataset
evaluate_ocr_performance(dataset_path)
