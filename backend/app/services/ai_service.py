from typing import List, Dict, Any, Optional
import json
from groq import Groq
from app.config import settings
from supabase import create_client


class AIService:
    def __init__(self):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"  # Fast and accurate
        
        # Initialize Supabase client for fetching hierarchy
        self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    
    def _build_topic_lookup(self, hierarchy: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Build a flat lookup table: topic_name -> {subject, chapter}
        This makes it easy for AI to select just the topic, and we auto-fill the rest.
        """
        lookup = {}
        for subject, chapters in hierarchy.items():
            for chapter, topics in chapters.items():
                for topic in topics:
                    lookup[topic] = {
                        "subject": subject,
                        "chapter": chapter,
                        "topic": topic
                    }
        return lookup
    
    def _fetch_tag_hierarchy(self) -> Dict[str, Any]:
        """
        Fetch the complete tag hierarchy from Supabase.
        Returns a structured dict with subjects, chapters, and topics (names only).
        """
        try:
            # Fetch all subjects
            subjects_response = self.supabase.table("subjects").select("id, name").execute()
            subjects = {s["id"]: s["name"] for s in subjects_response.data}
            
            # Fetch all chapters with subject mapping
            chapters_response = self.supabase.table("chapters").select("id, name, subject_id").execute()
            chapters_by_subject = {}
            for c in chapters_response.data:
                subject_id = c["subject_id"]
                if subject_id not in chapters_by_subject:
                    chapters_by_subject[subject_id] = []
                chapters_by_subject[subject_id].append(c["name"])
            
            # Fetch all topics with chapter mapping
            topics_response = self.supabase.table("topics").select("id, name, chapter_id").execute()
            topics_by_chapter = {}
            chapter_to_subject = {c["id"]: c["subject_id"] for c in chapters_response.data}
            
            for t in topics_response.data:
                chapter_id = t["chapter_id"]
                if chapter_id not in topics_by_chapter:
                    topics_by_chapter[chapter_id] = []
                topics_by_chapter[chapter_id].append(t["name"])
            
            # Build structured hierarchy
            hierarchy = {}
            for subject_id, subject_name in subjects.items():
                hierarchy[subject_name] = {}
                chapters = chapters_by_subject.get(subject_id, [])
                
                for chapter_data in chapters_response.data:
                    if chapter_data["subject_id"] == subject_id:
                        chapter_name = chapter_data["name"]
                        chapter_id = chapter_data["id"]
                        topics = topics_by_chapter.get(chapter_id, [])
                        hierarchy[subject_name][chapter_name] = topics
            
            return hierarchy
            
        except Exception as e:
            print(f"Error fetching tag hierarchy: {e}")
            return {}
    
    def get_tag_hierarchy_with_ids(self) -> Dict[str, Any]:
        """
        Fetch the complete tag hierarchy with IDs for frontend mapping.
        Returns a structured dict with IDs and names.
        """
        try:
            # Fetch all subjects
            subjects_response = self.supabase.table("subjects").select("id, name").execute()
            
            # Fetch all chapters
            chapters_response = self.supabase.table("chapters").select("id, name, subject_id").execute()
            
            # Fetch all topics
            topics_response = self.supabase.table("topics").select("id, name, chapter_id").execute()
            
            # Build hierarchy with IDs
            hierarchy = {}
            
            for subject in subjects_response.data:
                subject_id = subject["id"]
                subject_name = subject["name"]
                
                hierarchy[subject_name] = {
                    "id": subject_id,
                    "name": subject_name,
                    "chapters": {}
                }
                
                # Add chapters for this subject
                for chapter in chapters_response.data:
                    if chapter["subject_id"] == subject_id:
                        chapter_id = chapter["id"]
                        chapter_name = chapter["name"]
                        
                        hierarchy[subject_name]["chapters"][chapter_name] = {
                            "id": chapter_id,
                            "name": chapter_name,
                            "topics": {}
                        }
                        
                        # Add topics for this chapter
                        for topic in topics_response.data:
                            if topic["chapter_id"] == chapter_id:
                                topic_name = topic["name"]
                                hierarchy[subject_name]["chapters"][chapter_name]["topics"][topic_name] = {
                                    "id": topic["id"],
                                    "name": topic_name
                                }
            
            return hierarchy
            
        except Exception as e:
            print(f"Error fetching tag hierarchy with IDs: {e}")
            return {}
    
    def parse_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse multiple-choice questions from raw text using LLM.
        
        Args:
            text: Raw text containing questions
            
        Returns:
            List of parsed questions with structure:
            {
                "question_text": str,
                "options": [{"id": "A", "text": "..."}, ...],
                "correct_answer": str,
                "difficulty_level": str,
                "subject": str (must match available subjects),
                "chapter": str (must match available chapters),
                "topic": str (must match available topics)
            }
        """
        # Fetch available tags from database
        tag_hierarchy = self._fetch_tag_hierarchy()
        
        # Build topic lookup for easy mapping
        topic_lookup = self._build_topic_lookup(tag_hierarchy)
        
        # Debug: Log hierarchy info
        print(f"[DEBUG] Fetched tag hierarchy: {len(tag_hierarchy)} subjects")
        print(f"[DEBUG] Total topics available: {len(topic_lookup)}")
        for subject in list(tag_hierarchy.keys())[:3]:  # Show first 3
            print(f"[DEBUG]   - {subject}")
        
        # Determine if we should constrain tags or let AI generate freely
        has_tags = len(topic_lookup) > 0
        
        if has_tags:
            # Format as a simple list of topics for AI to choose from
            hierarchy_text = "AVAILABLE TOPICS (select ONE topic from this list for each question):\n\n"
            
            # Group topics by subject for readability
            for subject, chapters in tag_hierarchy.items():
                hierarchy_text += f"\n{subject}:\n"
                for chapter, topics in chapters.items():
                    for topic in topics:
                        hierarchy_text += f"  - {topic}\n"
            
            tag_instruction = """TAG SELECTION RULES:

1. You MUST select EXACTLY ONE topic from the list above for each question
2. Choose the CLOSEST matching topic even if it's not a perfect fit
3. DO NOT create new topics - ONLY use topics from the provided list
4. DO NOT use "None", "Other", "N/A" or any placeholder values

EXAMPLES OF CORRECT TOPIC SELECTION:

Example 1:
Question: "What is Newton's Second Law of Motion?"
Available topics include: "Force and inertia", "Newton's laws", "Impulse"
✅ CORRECT: Select "Newton's laws" (closest match)
❌ WRONG: "Newton's Second Law" (not in list)
❌ WRONG: "Laws of Motion" (not in list)

Example 2:
Question: "Find the derivative of x²"
Available topics include: "Differentiation of sum", "Differentiation of product", "Limits"
✅ CORRECT: Select "Differentiation of sum" (closest available topic about differentiation)
❌ WRONG: "Derivatives" (not in list)
❌ WRONG: "Calculus" (not in list)

Example 3:
Question: "What is the chemical formula for water?"
Available topics include: "Matter", "Atomic mass", "Mole concept"
✅ CORRECT: Select "Matter" (most general/closest topic about basic chemistry)
❌ WRONG: "Chemical formulas" (not in list)
❌ WRONG: "Water" (not in list)

Example 4:
Question: "If A = {1,2,3} and B = {2,3,4}, find A ∩ B"
Available topics include: "Sets and representation", "Union", "intersection", "complement"
✅ CORRECT: Select "intersection" (exact match!)
❌ WRONG: "Set intersection" (not in list)
❌ WRONG: "Sets" (too general when more specific option exists)

KEY PRINCIPLE: Always select from the provided list. If no perfect match exists, choose the closest or most general related topic.

Return format for each question:
- "topic": "exact topic name from the list" (REQUIRED)
- "difficulty_level": "easy" | "medium" | "hard" (REQUIRED)"""
        else:
            # No tags in database - cannot proceed
            hierarchy_text = "ERROR: No tags available in database. Cannot parse questions without tag hierarchy.\n\n"
            tag_instruction = """- ERROR: Tag hierarchy is required but not available"""
        
        # Debug: Log hierarchy text length
        print(f"[DEBUG] Has tags in database: {has_tags}")
        print(f"[DEBUG] Hierarchy text length: {len(hierarchy_text)} characters")
        if has_tags:
            print(f"[DEBUG] First 200 chars: {hierarchy_text[:200]}")
        
        system_prompt = f"""You are an expert question parser. Extract multiple-choice questions from raw text and convert them into structured JSON format.

{hierarchy_text}

IMPORTANT RULES:
1. Extract ALL questions found in the text
2. Each question must have:
   - question_text: The question itself
   - options: Array of {{id: "A"|"B"|"C"|"D"|"E", text: "option text"}}
   - correct_answer: The letter of the correct option (A, B, C, D, or E)
   - difficulty_level: "easy", "medium", or "hard" (infer if not specified, default to "medium")
   - topic: ONE topic selected from the available topics list (see tag selection rules below)

{tag_instruction}

3. Handle various formats flexibly:
   - Questions may start with "Q:", "Question:", numbers like "1.", or no prefix
   - Options may use A), a), A., (A), 1), or similar variations
   - Correct answers may be marked with "(correct)", "*", "✓", "Answer:", or stated separately
   - If difficulty is not mentioned, infer from question complexity or default to "medium"
   - Tags may be explicitly stated or need to be inferred from content

4. Normalize all output:
   - Option IDs must be uppercase letters: A, B, C, D, E (or more if needed)
   - Clean up extra whitespace and formatting
   - Preserve mathematical notation, formulas, and special characters in question/option text
   - Remove any markdown or formatting symbols

5. Tag Selection (CRITICAL - FOLLOW THE EXAMPLES):
   - Select EXACTLY ONE topic from the provided list that best matches the question
   - If no perfect match exists, choose the CLOSEST or most GENERAL related topic
   - NEVER create new topics - ONLY use topics from the list
   - NEVER use placeholders like "None", "Other", "N/A"
   - Review the examples above to understand how to select the closest match

6. Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "questions": [
    {{
      "question_text": "What is Newton's Second Law?",
      "options": [
        {{"id": "A", "text": "F = ma"}},
        {{"id": "B", "text": "E = mc²"}},
        {{"id": "C", "text": "V = IR"}},
        {{"id": "D", "text": "PV = nRT"}}
      ],
      "correct_answer": "A",
      "difficulty_level": "medium",
      "topic": "Newton's laws"
    }}
  ]
}}

Note: Only provide the "topic" field. Do NOT include "subject" or "chapter" fields.

7. If you cannot parse any valid questions, return: {{"questions": []}}

CRITICAL: 
- Return ONLY the JSON object, no other text, no markdown code blocks, no explanations
- For each question, provide ONLY the "topic" field (select from the list above)
- Do NOT include "subject" or "chapter" fields in your response
- Follow the examples provided - select the closest matching topic from the list
- NEVER create new topics or use placeholders"""

        # Debug: Verify hierarchy is in prompt
        print(f"[DEBUG] System prompt length: {len(system_prompt)} characters")
        print(f"[DEBUG] 'AVAILABLE TOPICS' in prompt: {'AVAILABLE TOPICS' in system_prompt}")
        print(f"[DEBUG] Number of topics in prompt: {system_prompt.count('  - ')}")
        
        user_prompt = f"Parse the following text and extract all questions with tags in JSON format:\n\n{text}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=4096,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json\n", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```\n", "").replace("```", "")
            
            # Parse JSON
            parsed = json.loads(content)
            
            # Validate structure
            if not isinstance(parsed, dict) or "questions" not in parsed:
                return []
            
            questions = parsed["questions"]
            if not isinstance(questions, list):
                return []
            
            # Validate and filter questions
            valid_questions = []
            for q in questions:
                if self._validate_question(q):
                    # Auto-fill subject and chapter based on topic
                    if topic_lookup and q.get('topic'):
                        topic_name = q.get('topic')
                        if topic_name in topic_lookup:
                            # Auto-fill from lookup (overwrite any AI-provided values)
                            q['subject'] = topic_lookup[topic_name]['subject']
                            q['chapter'] = topic_lookup[topic_name]['chapter']
                            q['topic'] = topic_lookup[topic_name]['topic']  # Ensure exact match
                            print(f"[DEBUG] ✓ Auto-filled hierarchy: {q['subject']}/{q['chapter']}/{q['topic']}")
                        else:
                            print(f"[DEBUG] ⚠ Topic '{topic_name}' not in database - keeping as is")
                            # Keep the topic but mark subject/chapter as None if not in DB
                            if 'subject' not in q or not q['subject']:
                                q['subject'] = None
                            if 'chapter' not in q or not q['chapter']:
                                q['chapter'] = None
                    
                    # Add all valid questions
                    valid_questions.append(q)
            
            return valid_questions
            
        except Exception as e:
            print(f"[DEBUG] Error parsing questions: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _validate_tags(self, question: Dict[str, Any], hierarchy: Dict[str, Any]) -> bool:
        """
        Validate that suggested tags exist in the hierarchy.
        Returns True if all tags match database, False otherwise.
        This is for logging purposes only - questions are not rejected based on this.
        """
        try:
            subject = question.get("subject")
            chapter = question.get("chapter")
            topic = question.get("topic")
            
            # If any tag is missing, it's not fully tagged
            if not subject or not chapter or not topic:
                return False
            
            # Subject must exist in hierarchy
            if subject not in hierarchy:
                return False
            
            # Chapter must exist under the subject
            if chapter not in hierarchy.get(subject, {}):
                return False
            
            # Topic must exist under the chapter
            topics = hierarchy.get(subject, {}).get(chapter, [])
            if topic not in topics:
                return False
            
            # All validations passed
            return True
            
        except Exception as e:
            return False
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate that a question has all required fields. Tags are optional but logged."""
        try:
            # Check required fields
            if not question.get("question_text"):
                print(f"[DEBUG] Question missing question_text")
                return False
            
            options = question.get("options", [])
            if not isinstance(options, list) or len(options) < 2:
                print(f"[DEBUG] Question has invalid options")
                return False
            
            # Validate options structure
            for opt in options:
                if not isinstance(opt, dict) or "id" not in opt or "text" not in opt:
                    print(f"[DEBUG] Question has malformed option")
                    return False
            
            # Check correct answer
            correct_answer = question.get("correct_answer")
            if not correct_answer:
                print(f"[DEBUG] Question missing correct_answer")
                return False
            
            # Verify correct answer exists in options
            option_ids = [opt["id"] for opt in options]
            if correct_answer not in option_ids:
                print(f"[DEBUG] Question correct_answer not in options")
                return False
            
            # Validate difficulty level
            difficulty = question.get("difficulty_level", "medium")
            if difficulty not in ["easy", "medium", "hard"]:
                question["difficulty_level"] = "medium"
            
            # Tags are not required for validation, just log if missing
            # (AI should provide them, but we don't reject questions without them)
            
            return True
            
        except Exception as e:
            print(f"[DEBUG] Question validation error: {e}")
            return False


# Singleton instance
ai_service = AIService() if settings.groq_api_key else None
