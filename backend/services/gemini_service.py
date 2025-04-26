import os
import json
import re
from google import genai
from google.genai import types
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        try:
            # Initialize Gemini client using direct API key (not Vertex AI)
            api_key = os.getenv("GOOGLE_API_KEY")
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-2.5-flash-preview-04-17"  # Using standard model instead of Vertex preview
            logger.info("Gemini service initialized")
        except Exception as e:
            logger.error(f"Error initializing Gemini service: {e}")
            raise

    def _extract_json_from_response(self, response_text):
        """Extract JSON from response text, handling markdown code blocks."""
        # Check if response is wrapped in markdown code blocks
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(json_pattern, response_text)
        
        if match:
            # Extract the JSON part from inside the code block
            json_str = match.group(1)
        else:
            # Use the whole response if no code block is found
            json_str = response_text
            
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text was: {response_text}")
            raise

    async def analyze_company(self, company_name: str):
        """Analyze what the company does and generate a friendly message."""
        prompt = f"""
        Analyze the company named {company_name}. 
        Provide the following information in JSON format:
        1. A brief description of what the company does
        2. The industry it operates in
        3. A friendly welcome message for a user from this company
        
        Output in this exact JSON structure:
        {{
            "description": "...",
            "industry": "...",
            "welcome_message": "..."
        }}
        """
        
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ]
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain",
            )
            
            # Collect the full response from stream
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, 'text'):
                    response_text += chunk.text
            
            # Extract JSON from response
            try:
                return self._extract_json_from_response(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from response: {response_text}")
                # Fallback: create a basic structure
                return {
                    "description": f"{company_name} is a company we don't have detailed information about.",
                    "industry": "Unknown",
                    "welcome_message": f"Welcome, {company_name} user! We're gathering competitive intelligence for you."
                }
                
        except Exception as e:
            logger.error(f"Error analyzing company: {e}")
            raise

    async def identify_competitors(self, company_name: str, company_description: str, industry: str):
        """Identify competitors for the given company."""
        prompt = f"""
        Based on the following information about {company_name}:
        - Description: {company_description}
        - Industry: {industry}
        
        Identify the top 5 competitors for this company. For each competitor, provide:
        1. Company name
        2. Brief description of what they do
        3. Key strengths (bullet points)
        4. Key weaknesses (bullet points)
        
        Output in this exact JSON structure:
        {{
            "competitors": [
                {{
                    "name": "Competitor 1",
                    "description": "What they do",
                    "strengths": ["strength1", "strength2"],
                    "weaknesses": ["weakness1", "weakness2"]
                }},
                ...
            ]
        }}
        """
        
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ]
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain",
            )
            
            # Collect the full response from stream
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, 'text'):
                    response_text += chunk.text
            
            # Extract JSON from response
            try:
                return self._extract_json_from_response(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from competitors response: {response_text}")
                # Return empty competitors list as fallback
                return {"competitors": []}
                
        except Exception as e:
            logger.error(f"Error identifying competitors: {e}")
            raise

    async def generate_insights(self, company_name: str, competitors_data: dict, news_data: dict):
        """Generate insights based on competitor news."""
        # Prepare news context for the prompt
        news_context = ""
        for competitor_name, articles in news_data.items():
            news_context += f"\n===== NEWS FOR {competitor_name} =====\n"
            for article in articles:
                news_context += f"HEADLINE: {article['title']}\n"
                news_context += f"CONTENT: {article['content']}\n\n"
        
        prompt = f"""
        Based on the news about competitors of {company_name}, generate strategic insights.
        
        COMPANY: {company_name}
        
        COMPETITORS INFORMATION:
        {json.dumps(competitors_data, indent=2)}
        
        NEWS DATA:
        {news_context}
        
        Generate 5-10 strategic insights for {company_name} based on this competitive intelligence.
        Each insight should identify a competitive opportunity, threat, or market trend.
        
        Output in this exact JSON structure:
        {{
            "insights": [
                {{
                    "title": "Brief title",
                    "description": "Detailed insight explanation",
                    "type": "opportunity|threat|trend",
                    "related_competitors": ["competitor1", "competitor2"]
                }},
                ...
            ]
        }}
        """
        
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ]
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
            )
            
            # Collect the full response from stream
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, 'text'):
                    response_text += chunk.text
            
            # Extract JSON from response
            try:
                return self._extract_json_from_response(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from insights response: {response_text}")
                # Return empty insights list as fallback
                return {"insights": []}
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            raise 