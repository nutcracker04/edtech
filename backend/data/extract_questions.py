import os
import json
import zipfile
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
load_dotenv()
def process_pdf(pdf_path: str, output_dir: str, api_key: str):
    """
    Process a PDF using Sarvam Vision (Document Intelligence API).
    Extracts text, tables, and images, outputting them into a structured format.
    """
    print(f"Initializing SarvamAI client...")
    client = SarvamAI(api_subscription_key=api_key)

    # We choose "md" (markdown) for easily readable structured text, 
    # but you could also use "json" or "html" depending on how you want to parse later.
    # The API extracts layout, tables, and crops images into an 'images' folder.
    print(f"Creating Document Intelligence job for: {pdf_path}")
    job = client.document_intelligence.create_job(
        language="en-IN",       
        output_format="md"     
    )

    print(f"Job ID: {job.job_id}")
    
    print("Uploading file...")
    job.upload_file(pdf_path)

    print("Starting extraction job...")
    job.start()

    print("Waiting for job to complete (this may take a few minutes)...")
    status = job.wait_until_complete(poll_interval=5.0)
    
    metrics = job.get_page_metrics()
    print(f"Job finished with state: {status.job_state}")
    if metrics:
        print(f"Metrics: {metrics}")

    if status.job_state != "Completed" and status.job_state != "PartiallyCompleted":
        print("Job did not complete successfully.")
        return None

    # Download output
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, f"{job.job_id}_output.zip")
    
    print(f"Downloading output to {zip_path}...")
    job.download_output(zip_path)

    # Unzip the output
    print("Unzipping results...")
    extract_path = os.path.join(output_dir, job.job_id)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    print(f"Extraction successful! Files saved to: {extract_path}")
    return extract_path

def parse_questions_from_markdown(extracted_dir: str):
    """
    A heuristic/regex or LLM-based function to parse the questions out of the markdown.
    Sarvam Vision creates a standard markdown file with inserted image links like `![image](images/X_Y.png)`.
    """
    md_files = list(Path(extracted_dir).glob("*.md"))
    if not md_files:
        print("No markdown file found in the extracted output.")
        return

    md_file_path = md_files[0]
    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # NOTE: Since PDF formats vary largely, a robust way to extract questions here is 
    # either by using regex matching (e.g., looking for "Q1.", "1.", "Question 1:") 
    # or passing this markdown to an LLM to chunk it into structured JSON questions.
    #
    # Because the markdown preserves tables and images directly inline, passing the chunk
    # to an LLM ensures the tables/images stay with their respective question!
    
    print("\nExtracting structured questions using Sarvam LLM page-by-page...")
    
    api_key = os.getenv("SARVAM_API_KEY")
    client = SarvamAI(api_subscription_key=api_key)
    all_questions = []

    # Split markdown into individual pages using the standard horizontal rule marker "---"
    pages = [page.strip() for page in content.split('\n---\n') if page.strip()]
    
    print(f"Total pages to process: {len(pages)}")

    for page_num, page_content in enumerate(pages, start=1):
        if "option" not in page_content.lower() and "?" not in page_content and "1." not in page_content:
            # Skip pages that likely have no questions
            continue
            
        print(f"Processing page {page_num} / {len(pages)}...")

        prompt = f"""
        You are an intelligent document parsing assistant. 
        Below is the markdown text for PAGE {page_num} of an educational PDF. It may contain text, tables, and image references (like ![image](images/...)).
        Extract all the multiple-choice or subjective questions from this specific page.
        
        Output strictly as a JSON array of objects, with each object having the following keys:
        - "page_number": {page_num}
        - "question_number": string
        - "question_text": string
        - "options": list of strings (if multiple choice)
        - "images_referenced": list of image URLs/paths found within the question text or options
        - "tables_referenced": list of markdown tables found within the question
        
        If there are no questions on this page, return an empty array: []
        
        Page {page_num} Content:
        {page_content}
        """

        try:
            response = client.chat.completions(
                messages=[
                    {"role": "system", "content": "You are a helpful JSON extractor. Only output valid JSON array, do not wrap in markdown tags if possible."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            if not response_text:
                continue
                
            questions_json = json.loads(response_text)
            if isinstance(questions_json, list):
                all_questions.extend(questions_json)
                
        except Exception as e:
            print(f"Error parsing page {page_num}: {e}")

    out_json_path = os.path.join(extracted_dir, "extracted_questions.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=4)
        
    print(f"\nSuccessfully extracted {len(all_questions)} total questions to {out_json_path}")
    print(f"Images are saved in: {os.path.join(extracted_dir, 'images/')}")

if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Extract questions, tables, and images from EdTech PDFs using Sarvam Vision.")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the PDF file")
    parser.add_argument("--outdir", type=str, default="output", help="Output directory")
    args = parser.parse_args()

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        print("Error: SARVAM_API_KEY environment variable is not set.")
        print("Please set it using: export SARVAM_API_KEY='your_api_key'")
        exit(1)

    if not os.path.exists(args.pdf):
        print(f"Error: Could not find PDF file at {args.pdf}")
        exit(1)

    extracted_dir = process_pdf(args.pdf, args.outdir, api_key)
    
    if extracted_dir:
        parse_questions_from_markdown(extracted_dir)
