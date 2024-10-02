from pathlib import Path
import urllib
import logging
import PyPDF2
import backoff
from google.api_core import exceptions
import ratelimit
import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.generative_models import GenerationConfig,GenerativeModel
import json
from google.oauth2 import service_account
from stqdm import stqdm
import streamlit as st

logging.basicConfig(filename="logs.log",
                    format='%(asctime)s %(message)s',
                    filemode='a+')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.info("--------------")

prompt_template = """
    Write a detailed  summary of the following text delimited by triple backquotes.
    Return your response in bullet points which covers the key points of the text.

    ```{text}```

    BULLET POINT SUMMARY:
"""


initial_prompt_template = """
    Write a detail summary of the following text delimited by triple backquotes.

    ```{text}```

    SUMMARY:
"""

final_prompt_template = """
    Write a detailed summary of the following text delimited by triple backquotes.
    Return your response in bullet points which covers the key points of the text.

    ```{text}```

    SUMMARY:
"""

credential = service_account.Credentials.from_service_account_file("rahul-research-test-76a85daa4ecb.json")

PROJECT_ID = "rahul-research-test"  # @param {type:"string"}
vertexai.init(project=PROJECT_ID, credentials=credential)

generation_model = GenerativeModel("gemini-1.5-flash")
# This Generation Config sets the model to respond in JSON format.
generation_config = GenerationConfig(
    temperature=0.0, response_mime_type="application/json"
)


def download_data(data_url="https://services.google.com/fh/files/misc/practitioners_guide_to_mlops_whitepaper.pdf"):
    data_folder = "data"
    Path(data_folder).mkdir(parents=True, exist_ok=True)

    # Define a pdf link to download and place to store the download file
    pdf_url = data_url
    pdf_file = Path(data_folder, pdf_url.split("/")[-1])

    # Download the file using `urllib` library
    urllib.request.urlretrieve(pdf_url, pdf_file)
    return pdf_file

CALL_LIMIT = 20  # Number of calls to allow within a period
ONE_MINUTE = 60  # One minute in seconds
FIVE_MINUTE = 5 * ONE_MINUTE
# A function to print a message when the function is retrying
def backoff_hdlr(details):
    print(
        "Backing off {} seconds after {} tries".format(
            details["wait"], details["tries"]
        )
    )
@backoff.on_exception(  # Retry with exponential backoff strategy when exceptions occur
    backoff.expo,
    (
        exceptions.ResourceExhausted,
        ratelimit.RateLimitException,
    ),  # Exceptions to retry on
    max_time=FIVE_MINUTE,
    on_backoff=backoff_hdlr,  # Function to call when retrying
)
@ratelimit.limits(  # Limit the number of calls to the model per minute
    calls=CALL_LIMIT, period=ONE_MINUTE
)


def model_with_limit_and_backoff(prompt):
    generated_content = generation_model.generate_content(prompt)
    return generated_content

def reduce(initial_summary, prompt_template):
    # Concatenate the summaries from the inital step
    concat_summary = "\n".join(initial_summary)

    # Create a prompt for the model using the concatenated text and a prompt template
    prompt = prompt_template.format(text=concat_summary)

    # Generate a summary using the model and the prompt
    summary = model_with_limit_and_backoff(prompt).text

    return summary


def initial_summary_generator(pdf_file):
    # Read the PDF file and create a list of pages.
    reader = PyPDF2.PdfReader(pdf_file)
    pages = reader.pages

    # Create an empty list to store the summaries.
    initial_summary = []

    # Iterate over the pages and generate a summary
    for idx, page in enumerate(stqdm(pages)):
        # Extract the text from the page and remove any leading or trailing whitespace.
        text = page.extract_text().strip()

        if idx == 0:  # if current page is the first page, no previous context
            prompt = initial_prompt_template.format(context="", text=text)

        else:  # if current page is not the first page, previous context is the summary of the previous page
            prompt = initial_prompt_template.format(
                context=initial_summary[idx - 1], text=text
            )

        # Generate a summary using the model and the prompt
        summary = model_with_limit_and_backoff(prompt).text

        # Append the summary to the list of summaries
        initial_summary.append(summary)

    initial_summary = set(initial_summary) 
    logger.info("Initial Summary Generated")
    return initial_summary





def start_generation(url_path):
    # Creating an object

    # logger.info("STARTED")
    logger.info("============================ Generation Started ================================")
    pdf_file = download_data(url_path)
    logger.info("Data Downloaded")
    initial_summary = initial_summary_generator(pdf_file)
    logger.info("Summary Reduction Started")
    summary = reduce(initial_summary, final_prompt_template)
    logger.info("Summary Reduction Completed")
    print(summary)
    logger.info("SUMMARY generated Process Closed")
    return summary



