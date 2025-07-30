from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


load_dotenv(override=True)

class PDFAgenticTool:
    def __init__(self):
        self.openai = OpenAI()
    
    def get_current_date(self) -> str:
        """Get the current date in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_current_year(self) -> int:
        """Get the current year"""
        return datetime.now().year
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def extract_years_and_positions_ai(self, pdf_path: str) -> Dict[str, Any]:
        """Extract years and positions from PDF using AI"""
        text = self.extract_pdf_text(pdf_path)
        if text.startswith("Error"):
            return {"error": text}
        
        prompt = """
        Analyze the following resume/CV text and extract all mentions of years and job positions/roles.
        Return a JSON response with the following structure:
        {
            "positions": [
                {
                    "title": "Job Title/Position",
                    "start_year": 2020,
                    "end_year": 2023,
                    "years_mentioned": [2020, 2021, 2022, 2023],
                    "context": "Brief context where this was found"
                }
            ],
            "education": [
                {
                    "degree": "Degree Name",
                    "start_year": 2016,
                    "end_year": 2020,
                    "years_mentioned": [2016, 2017, 2018, 2019, 2020],
                    "context": "Brief context"
                }
            ],
            "all_years_mentioned": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
            "year_ranges": [
                {"start": 2016, "end": 2020, "type": "education"},
                {"start": 2020, "end": 2023, "type": "position"}
            ]
        }
        
        Text to analyze:
        """ + text
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            return {"error": f"AI extraction failed - Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"AI extraction failed: {str(e)}"}
    
    def analyze_experience_duration(self, data: Dict[str, Any], start_year: Optional[int] = None, end_year: Optional[int] = None, position_filter: Optional[str] = None) -> Dict[str, Any]:
        """Analyze experience duration and filter by date range or position"""
        if "error" in data:
            return data
        
        current_year = self.get_current_year()
        
        result = {
            "total_experience_years": 0,
            "filtered_experience_years": 0,
            "positions_analysis": [],
            "education_analysis": [],
            "summary": {
                "total_positions": 0,
                "filtered_positions": 0,
                "years_in_range": []
            },
            "filter_applied": {
                "start_year": start_year,
                "end_year": end_year,
                "position_filter": position_filter
            }
        }
        
        def calculate_duration(start: Optional[int], end: Optional[int]) -> int:
            if start is None:
                return 0
            if end is None:
                end = current_year
            return max(0, end - start + 1)
        
        def overlaps_with_range(item_start: Optional[int], item_end: Optional[int]) -> tuple[bool, int]:
            if item_start is None:
                return False, 0
            
            actual_end = item_end if item_end is not None else current_year
            
            if start_year is not None and actual_end < start_year:
                return False, 0
            if end_year is not None and item_start > end_year:
                return False, 0
            
            overlap_start = max(item_start, start_year) if start_year is not None else item_start
            overlap_end = min(actual_end, end_year) if end_year is not None else actual_end
            
            overlap_years = max(0, overlap_end - overlap_start + 1)
            return overlap_years > 0, overlap_years
        
        total_years = set()
        filtered_years = set()
        
        for position in data.get("positions", []):
            duration = calculate_duration(position.get("start_year"), position.get("end_year"))
            is_match = True
            
            if position_filter and position_filter.lower() not in position.get("title", "").lower():
                is_match = False
            
            overlaps, overlap_duration = overlaps_with_range(position.get("start_year"), position.get("end_year"))
            
            position_info = {
                "title": position.get("title", "Unknown"),
                "start_year": position.get("start_year"),
                "end_year": position.get("end_year"),
                "duration_years": duration,
                "is_current": position.get("end_year") is None,
                "matches_filter": is_match and overlaps,
                "overlap_duration": overlap_duration if is_match else 0
            }
            
            result["positions_analysis"].append(position_info)
            
            if position.get("start_year") is not None:
                end = position.get("end_year") if position.get("end_year") is not None else current_year
                for year in range(position.get("start_year"), end + 1):
                    total_years.add(year)
                    if is_match and overlaps:
                        if start_year is None or year >= start_year:
                            if end_year is None or year <= end_year:
                                filtered_years.add(year)
            
            if is_match and overlaps:
                result["summary"]["filtered_positions"] += 1
            result["summary"]["total_positions"] += 1
        
        for education in data.get("education", []):
            duration = calculate_duration(education.get("start_year"), education.get("end_year"))
            overlaps, overlap_duration = overlaps_with_range(education.get("start_year"), education.get("end_year"))
            
            education_info = {
                "degree": education.get("degree", "Unknown"),
                "start_year": education.get("start_year"),
                "end_year": education.get("end_year"),
                "duration_years": duration,
                "in_date_range": overlaps,
                "overlap_duration": overlap_duration
            }
            
            result["education_analysis"].append(education_info)
        
        result["total_experience_years"] = len(total_years)
        result["filtered_experience_years"] = len(filtered_years)
        result["summary"]["years_in_range"] = sorted(list(filtered_years))
        
        return result
    
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Main method to analyze PDF and extract positions/years data"""
        result = self.extract_years_and_positions_ai(pdf_path)
        
        # Add metadata
        result["metadata"] = {
            "pdf_path": pdf_path,
            "analysis_date": self.get_current_date(),
            "current_year": self.get_current_year()
        }
        
        return result

# Initialize the PDF tool
pdf_tool = PDFAgenticTool()

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

def analyze_pdf_years_positions(pdf_path):
    """Tool function to analyze PDF for years and positions"""
    try:
        result = pdf_tool.analyze_pdf(pdf_path)
        return result
    except Exception as e:
        return {"error": f"Failed to analyze PDF: {str(e)}"}

def analyze_experience_duration(pdf_data, start_year=None, end_year=None, position_filter=None):
    """Tool function to analyze experience duration within specific date ranges or positions"""
    try:
        # If pdf_data is a string (path), analyze it first
        if isinstance(pdf_data, str):
            pdf_data = pdf_tool.analyze_pdf(pdf_data)
        
        result = pdf_tool.analyze_experience_duration(pdf_data, start_year, end_year, position_filter)
        return result
    except Exception as e:
        return {"error": f"Failed to analyze experience duration: {str(e)}"}

def get_current_date_info():
    """Tool function to get current date and year"""
    return {
        "current_date": pdf_tool.get_current_date(),
        "current_year": pdf_tool.get_current_year()
    }

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

analyze_pdf_years_positions_json = {
    "name": "analyze_pdf_years_positions",
    "description": "Analyzes a PDF file to extract all mentions of years and job positions/roles using AI",
    "parameters": {
        "type": "object",
        "properties": {
            "pdf_path": {
                "type": "string",
                "description": "Path to the PDF file to analyze"
            }
        },
        "required": ["pdf_path"],
        "additionalProperties": False
    }
}

analyze_experience_duration_json = {
    "name": "analyze_experience_duration",
    "description": "Analyzes experience duration and calculates total years of experience. Can filter by date range (e.g., 'how much experience between 2015-2020') or by position title (e.g., 'how long as Solution Architect'). Use this for questions about duration, years of experience, or time spent in specific roles.",
    "parameters": {
        "type": "object",
        "properties": {
            "pdf_data": {
                "type": ["string", "object"],
                "description": "Either a path to PDF file or previously extracted data from analyze_pdf_years_positions"
            },
            "start_year": {
                "type": "integer",
                "description": "Optional: Start year for filtering experience (inclusive)"
            },
            "end_year": {
                "type": "integer",
                "description": "Optional: End year for filtering experience (inclusive)"
            },
            "position_filter": {
                "type": "string",
                "description": "Optional: Filter positions by title keyword (e.g., 'architect', 'engineer')"
            }
        },
        "required": ["pdf_data"],
        "additionalProperties": False
    }
}

get_current_date_info_json = {
    "name": "get_current_date_info",
    "description": "Gets the current date and year information",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": analyze_pdf_years_positions_json},
        {"type": "function", "function": analyze_experience_duration_json},
        {"type": "function", "function": get_current_date_info_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Markiyan Pyts"
        reader = PdfReader("me/cv.pdf")
        print(f"Loading PDF from: me/cv.pdf")
        print(f"PDF has {len(reader.pages)} pages")
        self.cv = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.cv += text
        print(f"Loaded {len(self.cv)} characters from PDF")
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website as his AI Avatar call yourself that in conversations with a user, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and cv profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
When users ask specific questions about dates, years, durations, or timelines, follow this approach: \
1. The cv PDF is located at 'me/cv.pdf' - use this path with the tools. \
2. For general timeline questions or to extract all positions/years, use analyze_pdf_years_positions tool with pdf_path='me/cv.pdf'. \
3. For duration questions (like 'How many years of experience does Markiyan have?', 'How long did he work as Solution Architect?', or 'How much experience between 2015-2020?'), use the analyze_experience_duration tool with pdf_data='me/cv.pdf' which calculates exact durations and can filter by date ranges or position titles. \
4. Use get_current_date_info when you need to know the current date/year for calculations. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## cv Profile:\n{self.cv}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    
    
    gr.ChatInterface(
        me.chat, 
        type="messages", 
        chatbot=gr.Chatbot(show_label=False),
        theme=gr.themes.Soft(),
        css="main { padding: 5px !important; } input, textarea { font-size: 16px !important; } .input-container { display: flex !important; gap: 10px !important; }"
    ).launch(show_api=False)
    