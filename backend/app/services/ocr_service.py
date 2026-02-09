import pytesseract
from PIL import Image
import io
import re
from typing import List, Dict, Any
from app.config import settings
from app.utils.image_processing import (
    preprocess_image,
    resize_image,
    enhance_contrast,
    deskew_image,
    image_to_pil
)
from app.models.upload import ExtractedQuestion


# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


class OCRService:
    async def extract_questions_from_image(self, image_bytes: bytes) -> List[ExtractedQuestion]:
        """
        Extract questions from uploaded test paper image using Tesseract OCR.
        
        Returns list of extracted questions with confidence scores.
        """
        try:
            # Preprocess image
            processed_image = preprocess_image(image_bytes)
            
            # Enhance contrast
            enhanced = enhance_contrast(processed_image)
            
            # Deskew if needed
            deskewed = deskew_image(enhanced)
            
            # Resize for optimal OCR
            resized = resize_image(deskewed)
            
            # Convert to PIL Image
            pil_image = image_to_pil(resized)
            
            # Perform OCR with detailed data
            ocr_data = pytesseract.image_to_data(
                pil_image,
                lang=settings.tesseract_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text with confidence scores
            full_text = pytesseract.image_to_string(
                pil_image,
                lang=settings.tesseract_lang
            )
            
            # Parse the OCR text to identify questions
            questions = self.parse_questions(full_text, ocr_data)
            
            return questions
        
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    async def process_pdf(self, pdf_content: bytes) -> List[ExtractedQuestion]:
        # Placeholder for PDF processing logic
        # You would typically convert PDF to images here
        return []

    def parse_questions(self, text: str, ocr_data: Dict[str, Any]) -> List[ExtractedQuestion]:
        """
        Parse OCR text to identify individual questions and their options.
        
        This function looks for patterns like:
        - Question numbers: 1., Q1, Question 1, etc.
        - Options: A), (A), a), (a), etc.
        """
        questions = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Pattern to identify question numbers
        question_pattern = re.compile(r'^(\d+)[\.).\s]+(.+)', re.MULTILINE)
        
        # Pattern to identify options
        option_pattern = re.compile(r'^[(\[]?([A-Da-d])[\]).\s]+(.+)', re.MULTILINE)
        
        current_question = None
        current_options = []
        question_number = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new question
            question_match = question_pattern.match(line)
            if question_match:
                # Save previous question if exists
                if current_question:
                    questions.append(ExtractedQuestion(
                        question_number=question_number,
                        question_text=current_question,
                        options=[{"id": opt[0], "text": opt[1]} for opt in current_options],
                        confidence=self.calculate_average_confidence(ocr_data, i),
                        subject=None,  # Will be classified later
                        topic=None
                    ))
                
                # Start new question
                question_number = int(question_match.group(1))
                current_question = question_match.group(2).strip()
                current_options = []
                continue
            
            # Check if this line is an option
            option_match = option_pattern.match(line)
            if option_match and current_question:
                option_id = option_match.group(1).upper()
                option_text = option_match.group(2).strip()
                current_options.append((option_id, option_text))
                continue
            
            # If we have a current question and this isn't an option, it's continuation of question text
            if current_question and not option_match:
                current_question += " " + line
        
        # Don't forget the last question
        if current_question:
            questions.append(ExtractedQuestion(
                question_number=question_number,
                question_text=current_question,
                options=[{"id": opt[0], "text": opt[1]} for opt in current_options],
                confidence=self.calculate_average_confidence(ocr_data, len(lines) - 1),
                subject=None,
                topic=None
            ))
        
        return questions


    def calculate_average_confidence(self, ocr_data: Dict[str, Any], line_index: int) -> float:
        """
        Calculate average confidence score from OCR data.
        """
        confidences = [
            conf for conf in ocr_data.get('conf', [])
            if conf != -1  # -1 means no confidence data
        ]
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)


    async def classify_question_subject(self, question_text: str) -> str:
        """
        Classify question into subject based on keywords.
        This is a simple keyword-based classifier.
        For better accuracy, you could use an ML model.
        """
        question_lower = question_text.lower()
        
        # Physics keywords
        physics_keywords = ['force', 'velocity', 'acceleration', 'mass', 'energy', 
                           'momentum', 'friction', 'gravity', 'wave', 'frequency',
                           'circuit', 'current', 'voltage', 'resistance', 'magnetic']
        
        # Chemistry keywords
        chemistry_keywords = ['molecule', 'atom', 'compound', 'reaction', 'acid',
                             'base', 'ion', 'electron', 'bond', 'organic', 'solution',
                             'catalyst', 'oxidation', 'reduction', 'element']
        
        # Mathematics keywords
        math_keywords = ['equation', 'derivative', 'integral', 'matrix', 'vector',
                        'probability', 'logarithm', 'trigonometry', 'angle', 'polynomial',
                        'function', 'limit', 'calculate', 'solve', 'prove']
        
        # Count matches
        physics_count = sum(1 for kw in physics_keywords if kw in question_lower)
        chemistry_count = sum(1 for kw in chemistry_keywords if kw in question_lower)
        math_count = sum(1 for kw in math_keywords if kw in question_lower)
        
        # Return subject with highest count
        max_count = max(physics_count, chemistry_count, math_count)
        if max_count == 0:
            return "unknown"
        
        if physics_count == max_count:
            return "physics"
        elif chemistry_count == max_count:
            return "chemistry"
        else:
            return "mathematics"

ocr_service = OCRService()
