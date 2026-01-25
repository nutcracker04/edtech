from typing import List, Dict, Any
from app.models.upload import ExtractedQuestion
from app.models.test import Question, Option
import uuid


def parse_ocr_text_to_questions(
    extracted_questions: List[ExtractedQuestion],
    default_subject: str = "mathematics",
    default_difficulty: str = "medium",
    default_grade: List[str] = ["11", "12"]
) -> List[Question]:
    """
    Convert extracted questions from OCR to proper Question objects.
    """
    questions = []
    
    for eq in extracted_questions:
        # Convert options to Option objects
        options = [
            Option(id=opt["id"], text=opt["text"])
            for opt in eq.options
        ]
        
        # Create Question object
        question = Question(
            id=str(uuid.uuid4()),
            question=eq.question_text,
            options=options,
            correct_answer="",  # User will need to provide this
            explanation="",  # User can add this later
            difficulty=default_difficulty,
            topic="",  # Can be determined from subject classification
            subject=eq.subject or default_subject,
            grade_level=default_grade,
            tags=[],
            source="uploaded",
            answer_type="single_choice"
        )
        
        questions.append(question)
    
    return questions


def merge_question_with_answers(
    questions: List[Question],
    user_answers: Dict[int, str]
) -> List[Dict[str, Any]]:
    """
    Merge questions with user's provided answers.
    Used after user confirms/edits the extracted questions.
    """
    merged = []
    
    for idx, question in enumerate(questions):
        question_dict = question.model_dump()
        
        # Add user's answer if provided
        if idx + 1 in user_answers:
            question_dict["user_answer"] = user_answers[idx + 1]
        
        merged.append(question_dict)
    
    return merged
