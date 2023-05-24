import os
import re
import airtable
import openai
import time
import shutil

# Set up Airtable API client
AIRTABLE_API_KEY = "keyeDQ87k9Looanna"
AIRTABLE_BASE_KEY = "appOo3NIs0nT86pYB"
AIRTABLE_TABLE_NAME = "Imported table"
airtable_client = airtable.Airtable(AIRTABLE_BASE_KEY, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Set up OpenAI API client
OPENAI_API_KEY = "****"
openai.api_key = OPENAI_API_KEY

# Define function to generate a description using OpenAI API

def generate_description(item_name):
    prompt = f"Write me a description, in a paragraph of at least 100 words, to be used on an ecommerce platform for {item_name}. Do not mention the name of the item."
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    if response.choices[0].text.strip():
        print(f"{item_name} description, done!")
        return response.choices[0].text.strip()
    else:
        print(f"Error: could not generate description for {item_name}")
        return None

# Define function to generate bullet points using OpenAI API
def generate_bullet_points(description):
    prompt = f"Generate short points for:\n{description}. Using at least 5 bullets. Each bullet should have a maximum of 10 words. Use this bullet:'•'. Do not mention the name of the item. Include dimensions if they're mentioned in the description or item name:{item_name}. Don't put a full stop at the end of the bullet"
    completions = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.5,
        )
    
    if completions.choices[0].text.strip():
        bullet_points = completions.choices[0].text.strip()
        bullet_points = [bp.strip() for bp in bullet_points.split("\n")]
        bullet_points = "\n".join(bullet_points)
        print("Bullets, done!")
        return bullet_points
    else:
        print("Error: could not generate bullet points")
        return None

# Define folder paths
NEW_SHIPMENT_SOURCE_FOLDER_PATH = r"C:\Users\Andreo\Desktop\idkWhatToNameYouMan\New_Shipment"
CURRENT_BATCH_DESTINATION_FOLDER_PATH = r"C:\Users\Andreo\Desktop\idkWhatToNameYouMan\Sorted\Current_Batch"
TO_IMAGEBANK_DESTINATION_FOLDER_PATH = r"C:\Users\Andreo\Desktop\idkWhatToNameYouMan\Sorted\To_Imagebank"
NOT_ON_AIRTABLE_DESTINATION_FOLDER_PATH = r"C:\Users\Andreo\Desktop\idkWhatToNameYouMan\Sorted\Not_On_Airtable"

# Define time variables for rate limiting
start_time = time.time()
request_count = 0

# Define maximum requests and tokens per minute
MAX_REQUESTS_PER_MINUTE = 20
MAX_TOKENS_PER_MINUTE = 40000

# Define time variables for rate limiting
start_time = time.time()
request_count = 0
token_count = 0

# Loop over files in folder
for filename in os.listdir(NEW_SHIPMENT_SOURCE_FOLDER_PATH):
    # Rate limit to 20 requests and 40000 tokens per minute
    if request_count >= MAX_REQUESTS_PER_MINUTE or token_count >= MAX_TOKENS_PER_MINUTE:
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            time.sleep(60 - elapsed_time)
        start_time = time.time()
        request_count = 0
        token_count = 0
        request_count = 0

    if filename.endswith(".jpg"):
        # Get item number and image number from file name
        match = re.search(r"^(.*)_([0-9]+)\.jpg$", filename)
        if match:
            item_number = match.group(1)
            image_number = int(match.group(2))
        else:
            print(f"Error: could not extract item and image numbers from file name {filename}")
            continue
        
        # Determine which Airtable field to update based on the image number
        if image_number >= 1 and image_number <= 11:
            airtable_field = f"Image {image_number}"
        else:
            print(f"Error: invalid image number {image_number} for file {filename}")
            continue
       # Search for item in Airtable using item number
        records = airtable_client.search("ItemNo+Col", item_number)

        # If item is found
        if records:
            record = records[0]
            airtable_client.update(record["id"], {airtable_field:filename})
            tacc_web_status = record["fields"].get("TACC Web Status")

            # Check TACC web status
            if tacc_web_status is None or not tacc_web_status.isdigit() and image_number == 1:
                destination_folder = CURRENT_BATCH_DESTINATION_FOLDER_PATH
                airtable_client.update(record["id"], {"TACC Web Status": "129"})
                source_path = os.path.join(NEW_SHIPMENT_SOURCE_FOLDER_PATH, filename)
                destination_path = os.path.join(destination_folder, filename)
                shutil.move(source_path, destination_path)
                print(f"{item_number} is Offline. Moving {filename} to 'current batch' folder. Updated {item_number}'s batch no. to 129")
            elif tacc_web_status is not None and tacc_web_status.isdigit() and image_number != 1:
                destination_folder = CURRENT_BATCH_DESTINATION_FOLDER_PATH
                source_path = os.path.join(NEW_SHIPMENT_SOURCE_FOLDER_PATH, filename)
                destination_path = os.path.join(destination_folder, filename)
                shutil.move(source_path, destination_path)
                print(f"{item_number} is Offline. Moving {filename} to 'current batch' folder. Updated {item_number}'s batch no. to 129")
            else:
                destination_folder = TO_IMAGEBANK_DESTINATION_FOLDER_PATH
                source_path = os.path.join(NEW_SHIPMENT_SOURCE_FOLDER_PATH, filename)
                destination_path = os.path.join(destination_folder, filename)
                shutil.move(source_path, destination_path)
                print(f"{item_number} is Online. Batch {tacc_web_status}. Moving {filename} to 'To Image Bank' folder")

            # Generate description and bullet points
            

        else:
            destination_folder = NOT_ON_AIRTABLE_DESTINATION_FOLDER_PATH
            source_path = os.path.join(NEW_SHIPMENT_SOURCE_FOLDER_PATH, filename)
            destination_path = os.path.join(destination_folder, filename)
            shutil.move(source_path, destination_path)
            print(f"No record found for item number {item_number}. Moving {filename} to 'Not on Airtable' folder")

            