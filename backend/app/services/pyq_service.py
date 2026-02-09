
import os
import io
import json
import base64
import requests
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from PIL import Image
from pdf2image import convert_from_bytes
from app.database import supabase
from app.config import settings

class PyqService:
    def __init__(self):
        # We use the same NVIDIA API key as before
        self.api_key = "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"
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "mistralai/mistral-large-3-675b-instruct-2512" # Or specifically the vision one if different endpoint
        # The user provided link: https://build.nvidia.com/mistralai/mistral-large-3-675b-instruct-2512
        # The API endpoint for that is usually standard chat/completions
        
    def _fetch_tag_hierarchy(self) -> Dict[str, Any]:
        """
        Fetches the complete Subject -> Chapter -> Topic hierarchy from DB.
        Returns a structured dictionary for the prompt.
        """
        subjects = supabase.table("subjects").select("id, name").execute().data
        chapters = supabase.table("chapters").select("id, name, subject_id").execute().data
        topics = supabase.table("topics").select("id, name, chapter_id").execute().data
        
        hierarchy = {}
        for s in subjects:
            s_name = s["name"]
            hierarchy[s_name] = {}
            
            s_chapters = [c for c in chapters if c["subject_id"] == s["id"]]
            for c in s_chapters:
                c_name = c["name"]
                hierarchy[s_name][c_name] = []
                
                c_topics = [t for t in topics if t["chapter_id"] == c["id"]]
                for t in c_topics:
                    hierarchy[s_name][c_name].append(t["name"])
                    
        return hierarchy

    async def process_pyq_paper(self, file_content: bytes, paper_id: str, exam_meta: dict):
        """
        Main entry point:
        1. Convert PDF to Images
        2. For each image -> Extract Questions (Logic + Diagram BBox)
        3. If Diagram -> Crop & Upload
        4. Save to `pyq_questions`
        """
        try:
            # Update status to processing
            supabase.table("pyq_papers").update({"processing_status": "processing"}).eq("id", paper_id).execute()
            
            images = convert_from_bytes(file_content)
            hierarchy = self._fetch_tag_hierarchy()
            
            total_questions = 0
            
            for i, image in enumerate(images):
                page_num = i + 1
                try:
                    # 1. Extract Data
                    extracted_data = self._extract_from_page(image, hierarchy)
                    
                    # 2. Process & Save
                    for q in extracted_data:
                        # Handle Image Cropping
                        image_url = None
                        if q.get("has_image") and q.get("bbox"):
                            image_url = self._crop_and_upload_image(image, q["bbox"], paper_id, page_num, q.get("question_number", 0))
                        
                        # Resolve Tags (Strict Mapping)
                        # Expecting lists from updated prompt, but handle single strings for robustness
                        subjects_raw = q.get("subject")
                        chapters_raw = q.get("chapter")
                        topics_raw = q.get("topic")
                        
                        # Normalize to lists
                        if isinstance(subjects_raw, str): subjects_raw = [subjects_raw]
                        elif not subjects_raw: subjects_raw = []
                        
                        if isinstance(chapters_raw, str): chapters_raw = [chapters_raw]
                        elif not chapters_raw: chapters_raw = []
                        
                        if isinstance(topics_raw, str): topics_raw = [topics_raw]
                        elif not topics_raw: topics_raw = []

                        s_id, c_ids, t_ids = self._resolve_tags(subjects_raw, chapters_raw, topics_raw)
                        
                        # Use the first subject as primary if multiple (DB schema technically has single subject_id for now)
                        # But we support multiple chapters/topics
                        
                        question_payload = {
                            "paper_id": paper_id,
                            "question_text": q.get("question_text"),
                            "options": q.get("options", []),
                            "correct_answer": q.get("correct_answer"),
                            "has_image": q.get("has_image", False),
                            "image_url": image_url,
                            "subject_id": s_id,
                            "chapter_ids": c_ids, # New Array Column
                            "topic_ids": t_ids,   # New Array Column
                            "chapter_id": c_ids[0] if c_ids else None, # Legacy/Primary
                            "topic_id": t_ids[0] if t_ids else None,   # Legacy/Primary
                            "page_number": page_num,
                            "question_number": q.get("question_number"),
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        supabase.table("pyq_questions").insert(question_payload).execute()
                        total_questions += 1
                        
                except Exception as e:
                    print(f"Error processing page {page_num}: {str(e)}")
                    # Continue to next page rather than failing entire paper
            
            # Update paper status
            supabase.table("pyq_papers").update({
                "processing_status": "completed", 
                "total_questions": total_questions
            }).eq("id", paper_id).execute()
            
            return {"status": "success", "total_questions": total_questions}
            
        except Exception as e:
            supabase.table("pyq_papers").update({
                "processing_status": "failed",
                "error_message": str(e)
            }).eq("id", paper_id).execute()
            raise e

    def _extract_from_page(self, image: Image.Image, hierarchy: Dict) -> List[Dict]:
        """
        Calls Mistral Vision API to extract questions.
        Prompt requests JSON list with bounding boxes for diagrams.
        """
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        prompt = f"""
        You are an expert exam digitizer. Extract all questions from this page.
        
        Hierarchy for tagging (Subject -> Chapter -> Topic):
        {json.dumps(hierarchy, indent=2)}
        
        OUTPUT FORMAT (JSON List):
        [
          {{
            "question_number": 1,
            "question_text": "Full text of question...",
            "options": [{{"id": "A", "text": "..."}}, ...],
            "correct_answer": "A", (if marked),
            "subject": "Math", 
            "chapter": ["Calculus", "Functions"], (Can be a list if multiple concepts involved),
            "topic": ["Limits", "Domain"], (Can be a list if multiple concepts involved),
            "has_image": true/false, (Does this question have a diagram/figure?),
            "bbox": [ymin, xmin, ymax, xmax] (Normalized 0-1 coordinates of the diagram ONLY, if has_image is true. 0,0 is top-left)
          }}
        ]
        
        IMPORTANT:
        1. Return ONLY the JSON list. No markdown formatting, no explanation.
        2. Accurately transcribe all math formulas using LaTeX.
        1. Return ONLY the JSON list. No markdown formatting, no explanation.
        2. Accurately transcribe all math formulas using LaTeX.
        3. **CRITICAL**: You MUST double-escape all LaTeX backslashes. 
           - Write `\\frac` for `\frac`
           - Write `\\alpha` for `\alpha`
           - Write `\\int` for `\int`
           - The raw JSON string must look like: "text": "Solve $\\int x dx$"
        4. **CRITICAL - Character Set**: 
           - NEVER use Unicode subscripts (₀₁₂₃₄₅₆₇₈₉) or superscripts (⁰¹²³⁴⁵⁶⁷⁸⁹)
           - Use LaTeX syntax: _2 for subscript, ^2 for superscript
           - Example: Write $H_2O$ NOT H₂O
           - Example: Write $x^2$ NOT x²
        5. **CRITICAL - Math Mode Wrapping**:
           - ALL mathematical expressions must be wrapped in $...$ (inline) or $$...$$ (block)
           - Chemistry formulas: $\\text{{H}}_2\\text{{SO}}_4$ not H₂SO₄
           - Variables and symbols: $\\alpha$, $\\beta$, $\\theta$ not \\alpha, β, θ
           - Mixed text-math: 'The compound $\\beta$-naphthol' not 'The compound \\β-naphthol'
        6. **CRITICAL - Tables**:
           - DO NOT use LaTeX tabular environment
           - Instead, format as simple text table:
           | A | B | Y |
           | 0 | 0 | 0 |
           | 1 | 0 | 1 |
           OR describe in words: 'Truth table: A=0,B=0→Y=0; A=1,B=0→Y=1...'
        7. Degree symbol: Use $0^\\circ$C not 0°C or 0\\degreeC
        8. If a question has a diagram, set has_image=true and provide the bounding box [ymin, xmin, ymax, xmax] for the diagram.
        9. INVALID CHARACTERS: Do not use unescaped backslashes.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        payload = {
            "model": self.model, 
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}} 
                    ]
                }
            ],
            "temperature": 0.2,
            "top_p": 1,
            "max_tokens": 4096,
            "stream": False
        }
        
        response = requests.post(self.invoke_url, headers=headers, json=payload)
        
        if response.status_code != 200:
             print(f"Error Status: {response.status_code}")
             print(f"Error Response: {response.text}")
        
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        
        def repair_json_content(json_str: str) -> str:
            """
            Attempts to repair common JSON errors in LLM output, specifically unescaped LaTeX backslashes.
            Replaces `\` with `\\` unless it is followed by a valid escape character.
            """
            # Regex to match backslash NOT followed by valid JSON escape chars (" \ / b f n r t u)
            # We want to match `\` that is NOT followed by these.
            # \u must be followed by 4 hex, but we'll just check for u for simplicity as \user is rare in latex
            # LaTeX: \alpha, \int, \frac -> all invalid escapes.
            return re.sub(r'\\(?![/\"\\bfnrtu])', r'\\\\', json_str)

        try:
            # Attempt to find JSON list in the content
            start_index = content.find('[')
            end_index = content.rfind(']')
            
            if start_index != -1 and end_index != -1:
                json_str = content[start_index : end_index + 1]
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try repairing
                    print("JSON Decode Error in list, attempting repair...")
                    json_str_repaired = repair_json_content(json_str)
                    data = json.loads(json_str_repaired)
                return data
            else:
                print(f"No JSON array found in response")
                # Try to fallback to finding any JSON object if list not found
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                    
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    print("JSON Decode Error in fallback, attempting repair...")
                    data = json.loads(repair_json_content(content))
                return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Content snippet: {content[:200]}")
            return []
            
            # Fallback to existing logic if [] not found or still fails
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```json")[1].split("```")[0]
                
            try:
                data = json.loads(content)
            except:
                data = json.loads(repair_json_content(content))
            
            if isinstance(data, dict):
                for key in data:
                    if isinstance(data[key], list):
                        return data[key]
            return data if isinstance(data, list) else []
            
        except Exception as e:
            print(f"Failed to parse JSON: {content[:100]}... Error: {str(e)}")
            return []

    def _crop_and_upload_image(self, original_image: Image.Image, bbox: List[float], paper_id: str, page: int, q_num: int) -> Optional[str]:
        """
        Crops the image based on bbox [ymin, xmin, ymax, xmax] (0-1 normalized).
        Uploads to Supabase storage.
        """
        try:
            width, height = original_image.size
            ymin, xmin, ymax, xmax = bbox
            
            # Convert to pixels
            left = xmin * width
            top = ymin * height
            right = xmax * width
            bottom = ymax * height
            
            # Crop
            cropped = original_image.crop((left, top, right, bottom))
            
            # Save to buffer
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            buf.seek(0)
            
            # Upload
            file_path = f"{paper_id}/p{page}_q{q_num}.png"
            bucket = "question-images" # Ensure this bucket exists
            
            # Check if bucket exists, if not use 'questions' or assume it exists
            # For this implementation, we try upload directly
            
            result = supabase.storage.from_(bucket).upload(
                file = buf.read(),
                path = file_path,
                file_options={"content-type": "image/png"}
            )
            
            # Get Public URL
            public_url = supabase.storage.from_(bucket).get_public_url(file_path)
            return public_url
            
        except Exception as e:
            print(f"Error cropping/uploading image: {e}")
            return None

    def _resolve_tags(self, s_names: List[str], c_names: List[str], t_names: List[str]) -> Tuple[Optional[str], List[str], List[str]]:
        """
        Resolves names to IDs using DB lookup. 
        Accepts lists of names and returns lists of IDs.
        """
        s_id = None
        c_ids = []
        t_ids = []
        
        # 1. Resolve Subject (Single for now, take first)
        if s_names and len(s_names) > 0:
            s_name = s_names[0]
            if s_name:
                res = supabase.table("subjects").select("id").eq("name", s_name).execute()
                if res.data: s_id = res.data[0]["id"]
            
        # 2. Resolve Chapters
        if c_names and s_id:
            for c_name in c_names:
                if not c_name: continue
                # We filter by subject_id to ensure correctness
                res = supabase.table("chapters").select("id").eq("name", c_name).eq("subject_id", s_id).execute()
                if res.data:
                    c_ids.append(res.data[0]["id"])
        
        # 3. Resolve Topics
        # Topics need to belong to one of the resolved chapters.
        # This is tricky because we don't know which topic belongs to which chapter from names alone easily
        # unless names are unique or we check all resolved chapters.
        if t_names and c_ids:
            for t_name in t_names:
                if not t_name: continue
                # Search in all resolved chapters
                # Or just search by name and filter by chapter_ids in python (or use `in` query)
                
                # Using `in` query for chapter_id
                res = supabase.table("topics").select("id").eq("name", t_name).in_("chapter_id", c_ids).execute()
                if res.data:
                    t_ids.append(res.data[0]["id"])
            
        return s_id, c_ids, t_ids

    def delete_images_from_storage(self, image_urls: List[str]):
        """
        Deletes images from Supabase storage.
        Expects full public URLs. Extracts the path relative to the bucket.
        """
        if not image_urls:
            return
            
        try:
            # Extract paths from URLs
            # URL format example: https://<project>.supabase.co/storage/v1/object/public/question-images/{paper_id}/{filename}
            # We need just {paper_id}/{filename} which comes after the bucket name "question-images/"
            
            paths = []
            bucket_name = "question-images"
            
            for url in image_urls:
                if not url: continue
                
                if bucket_name in url:
                    # Split by bucket name and take the part after
                    parts = url.split(f"{bucket_name}/")
                    if len(parts) > 1:
                        # Decode URL components if needed, but usually storage paths are safe? 
                        # Ideally we should just grab the suffix.
                        paths.append(parts[1])
            
            if paths:
                supabase.storage.from_(bucket_name).remove(paths)
                print(f"Deleted {len(paths)} images from storage: {paths}")
                
        except Exception as e:
            print(f"Error deleting images from storage: {e}")

pyq_service = PyqService()
