import os
import json
import re
from google import genai
from google.genai import types
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        try:
            # Initialize Gemini client using direct API key (not Vertex AI)
            api_key = os.getenv("GOOGLE_API_KEY")
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-2.5-flash-preview-04-17"  # Using standard model instead of flash preview
            self.pro_model = "gemini-2.5-pro-preview-03-25"  # For deep research
            self.temperature = 0.81  # Set temperature for all model calls
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
            logger.info(f"Attempting to parse JSON: {json_str[:100]}...")
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text was: {response_text}")
            # Re-raise exception to be handled by callers
            raise

    async def analyze_company(self, company_name: str):
        """Analyze what the company does and generate a friendly message."""
        prompt = f"""
        Analyze the company named {company_name}.
        Provide the following information in JSON format:
        1. A concise yet informative description (2-3 sentences) of what the company does, including its primary products/services and target audience.
        2. The main industry or sector it operates within.
        3. A friendly, professional, and slightly enthusiastic welcome message (1-2 sentences) tailored for a user from this specific company who is about to use a competitive intelligence platform. **Optionally, integrate a simple, non-offensive, lighthearted pun related to the company's name or main industry or their primary function into this welcome message.**
        
        IMPORTANT: Output ONLY the JSON object with the following exact structure.
        **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
        - All property names must be in double quotes
        - All string values must be in double quotes
        
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
                temperature=self.temperature,
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
                result = self._extract_json_from_response(response_text)
                # If result is not a dict, fallback to default response
                if not isinstance(result, dict):
                    logger.error(f"Invalid result type from Gemini: {type(result)}")
                    return {
                        "description": f"{company_name} is a company we don't have detailed information about.",
                        "industry": "Unknown",
                        "welcome_message": f"Welcome, {company_name} user! We're gathering competitive intelligence for you."
                    }
                return result
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
        Based on the following information about the company {company_name}:
        - Description: {company_description}
        - Industry: {industry}

        Identify **up to 10** *most relevant direct competitors* for this company.
        For each competitor, provide:
        1. The company name.
        2. A brief description (1-2 sentences) of their main focus.
        3. 2-3 key strengths *relative to the target company or market* (as bullet points).
        4. 2-3 key weaknesses *relative to the target company or market* (as bullet points).
        Prioritize competitors who are actively making moves in the market or directly compete with {company_name}'s core offerings.

        IMPORTANT: Output ONLY the JSON object with this exact structure.
        **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
        - Each object must end with a comma if it's not the last item in the list
        - All arrays and objects must be properly closed with ] or }}
        - No trailing commas after the last item in an array or object
        - All property names must be in double quotes
        - All string values must be in double quotes
        
        {{
            "competitors": [
                {{
                    "name": "Competitor 1",
                    "description": "...",
                    "strengths": ["...", "..."],
                    "weaknesses": ["...", "..."]
                }},
                ... (up to 10 competitors)
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
                temperature=self.temperature,
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
                result = self._extract_json_from_response(response_text)
                # Ensure result is a dict with competitors key
                if not isinstance(result, dict) or "competitors" not in result:
                    logger.error(f"Invalid result format from Gemini: {result}")
                    return {"competitors": []}
                return result
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
        As a competitive intelligence analyst, synthesize the provided information about {company_name}, its competitors, and recent news to generate 5-10 strategic insights.
        These insights should highlight competitive opportunities, threats, or significant market trends relevant to {company_name}.

        COMPANY: {company_name}

        COMPETITORS INFORMATION:
        {json.dumps(competitors_data, indent=2)}

        NEWS DATA:
        {news_context}

        Instructions:
        - Generate 5 to 10 distinct insights.
        - Each insight must be directly supported by the provided Competitor Information and/or News Data.
        - For each insight, provide:
            - A concise 'title'.
            - A 'description' that explains the insight and its potential implication for {company_name}. Reference the relevant information from the context (e.g., "Competitor X's recent acquisition...", "News about Trend Y...").
            - A 'type' labeled as either "opportunity", "threat", or "trend".
            - A list of 'related_competitors' (names from the provided list) that are most relevant to this insight.
        - If news data is limited, focus insights primarily on the provided competitor strengths/weaknesses and general industry trends.
        
        IMPORTANT: Output ONLY the JSON object with the following exact structure.
        **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
        - Each object must end with a comma if it's not the last item in the list
        - All arrays and objects must be properly closed with ] or }}
        - No trailing commas after the last item in an array or object
        - All property names must be in double quotes
        - All string values must be in double quotes
        
        {{
            "insights": [
                {{
                    "title": "...",
                    "description": "...",
                    "type": "opportunity|threat|trend",
                    "related_competitors": ["...", "..."]
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
                result = self._extract_json_from_response(response_text)
                # Ensure result is a dict with insights key
                if not isinstance(result, dict):
                    logger.error(f"Invalid result type from Gemini: {type(result)}")
                    return {"insights": []}
                insights = result.get('insights', [])
                return {"insights": insights}
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from insights response: {response_text}")
                # Return empty insights list as fallback
                return {"insights": []}
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            raise

    async def deep_research_competitor(self, competitor_name: str, competitor_description: Optional[str]):
        """Generates an in-depth research report for a competitor using a Pro model."""
        logger.info(f"Starting deep research for: {competitor_name} using model {self.pro_model}")

        # --- DETAILED PROMPT ---
        prompt = f"""
        Generate a comprehensive competitive analysis report in Markdown format for the company: **{competitor_name}**.
        Use its known description as a starting point: "{competitor_description or 'No initial description provided.'}"

        Structure the report with the following sections using appropriate Markdown headings (e.g., ## Section Title):

        1.  **Company Overview:**
            *   Detailed description of the company, its mission, vision, and core business.
            *   History and founding details (if available).
            *   Key locations, size (employee count estimates), and organizational structure highlights.

        2.  **Products & Services:**
            *   Detailed breakdown of major product lines and service offerings.
            *   Target customer segments for each offering.
            *   Key features, functionalities, and unique selling propositions (USPs).
            *   Pricing model overview (e.g., subscription tiers, enterprise pricing, freemium).

        3.  **Technology & Innovation:**
            *   Core technologies utilized (AI/ML models, platforms, infrastructure).
            *   Recent technological advancements or R&D focus areas.
            *   Patents or notable intellectual property (if discoverable).
            *   Approach to innovation (e.g., internal R&D, acquisitions, partnerships).

        4.  **Market Position & Strategy:**
            *   Estimated market share or standing within its primary industry segment(s).
            *   Key competitive advantages.
            *   Go-to-market strategy (sales channels, marketing approaches).
            *   Recent strategic moves (major partnerships, M&A activity, geographic expansion).

        5.  **Financial Health & Funding (if publicly available/discoverable):**
            *   Overview of financial performance (revenue trends, profitability if reported).
            *   Major funding rounds (dates, amounts, key investors).
            *   Stock performance overview (if public).

        6.  **SWOT Analysis:**
            *   Strengths: Internal capabilities that provide an advantage.
            *   Weaknesses: Internal limitations or disadvantages.
            *   Opportunities: External factors the company could leverage.
            *   Threats: External factors that could negatively impact the company.
            *   (Provide brief explanations for each point)

        7.  **Recent News & Developments (Summarized):**
            *   Summary of key news headlines, press releases, or significant announcements from the last 6-12 months. Focus on strategically relevant items.

        8.  **Key Personnel:**
            *   CEO and other key executives (names, roles, brief background if notable).

        **Instructions:**
        *   Conduct thorough research using available tools.
        *   Synthesize information into a coherent report.
        *   Use clear and professional language.
        *   Format the entire output strictly as Markdown.
        *   Do not include any preamble or explanation outside the Markdown report itself. Start directly with the first heading.
        """
        # --- END DETAILED PROMPT ---

        try:
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            # Use Google Search tool for grounding
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain", # Requesting Markdown, but API expects text
            )

            # Use the Pro model for this call
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.pro_model, # Use the Pro model here
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, 'text'):
                    response_text += chunk.text

            # Assume the response is the Markdown content
            logger.info(f"Deep research content generated for: {competitor_name}")
            return response_text

        except Exception as e:
            logger.error(f"Error during deep research for {competitor_name}: {e}")
            return f"## Error\n\nAn error occurred during deep research generation for {competitor_name}:\n\n```\n{str(e)}\n```" 