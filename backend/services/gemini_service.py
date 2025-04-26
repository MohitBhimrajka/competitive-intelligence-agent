import os
import json
import re
from google import genai
from google.genai import types
import logging
from typing import Optional
import time
import asyncio

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
        """Extract JSON from response text, handling markdown code blocks and potential preamble."""
        logger.debug(f"Raw response text for JSON extraction:\n{response_text}")

        # 1. Try finding JSON within markdown code blocks first
        json_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```" # More specific pattern for object
        match = re.search(json_pattern, response_text)

        json_str = None
        if match:
            json_str = match.group(1)
            logger.debug("Found JSON inside markdown block.")
        else:
            # 2. If no markdown block, try finding the first '{' that likely starts the JSON
            brace_index = response_text.find('{')
            if brace_index != -1:
                 # Try to find the corresponding closing brace (simple check, might fail on nested)
                 # A more robust parser might be needed for complex cases, but this handles simple preamble
                 potential_json = response_text[brace_index:]
                 # Basic validation: does it start with { and end with }?
                 if potential_json.strip().endswith('}'):
                      json_str = potential_json
                      logger.debug("Found JSON by searching for first '{'.")
                 else:
                      logger.warning("Found '{' but text doesn't seem to end with '}'. Using full response.")
                      json_str = response_text # Fallback to whole text if unsure
            else:
                # 3. If no '{' found or markdown block, use the whole response
                logger.debug("No JSON block or starting '{' found. Using full response text.")
                json_str = response_text

        try:
            logger.info(f"Attempting to parse JSON string: {json_str[:200]}...") # Log more context
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Attempted to parse: {json_str}") # Log the string that failed
            raise # Re-raise exception
        except Exception as e: # Catch other potential errors
             logger.error(f"Unexpected error during JSON parsing: {e}")
             logger.error(f"Attempted to parse: {json_str}")
             raise json.JSONDecodeError(f"Unexpected error during JSON parsing: {e}", json_str or "", 0) # Raise standard error

    async def analyze_company(self, company_name: str, max_retries: int = 1):
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
        
        attempt = 0
        last_exception = None
        while attempt <= max_retries:
            attempt += 1
            logger.info(f"Analyzing company '{company_name}', attempt {attempt}/{max_retries+1}")
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
                        raise ValueError("Invalid result type") # Treat as error for retry
                    logger.info(f"Successfully parsed company analysis for {company_name}")
                    return result # Success!
                except json.JSONDecodeError as e:
                    logger.error(f"JSONDecodeError on attempt {attempt}: {e}")
                    last_exception = e
                    if attempt > max_retries:
                        logger.error(f"Max retries reached for company analysis JSON parsing.")
                        # Fallback after all retries failed
                        return {
                            "description": f"{company_name} is a company we don't have detailed information about.",
                            "industry": "Unknown",
                            "welcome_message": f"Welcome, {company_name} user! We're gathering competitive intelligence for you."
                        }
                    await asyncio.sleep(1) # Wait before retrying
                    
            except Exception as e:
                logger.error(f"Error during Gemini call for company analysis (attempt {attempt}): {e}")
                last_exception = e
                if attempt > max_retries:
                    logger.error(f"Max retries reached for company analysis Gemini call.")
                    # Return fallback rather than raising to ensure the process continues
                    return {
                        "description": f"{company_name} is a company we don't have detailed information about.",
                        "industry": "Unknown",
                        "welcome_message": f"Welcome, {company_name} user! We're gathering competitive intelligence for you."
                    }
                await asyncio.sleep(1) # Wait before retrying

        # Should only reach here if all retries failed parsing but didn't raise other exception
        logger.error(f"Exhausted retries for company analysis, returning fallback. Last error: {last_exception}")
        return {
            "description": f"{company_name} is a company we don't have detailed information about.",
            "industry": "Unknown",
            "welcome_message": f"Welcome, {company_name} user! We're gathering competitive intelligence for you."
        }

    async def identify_competitors(self, company_name: str) -> dict:
        """Identify competitors for a given company."""
        try:
            prompt = f"""You are a business analyst with expertise in competitive analysis.
Identify 3-5 main competitors for {company_name}.

For each competitor, provide:
1. Name
2. Brief description (1-2 sentences)
3. 3-5 key strengths as bullet points
4. 2-3 key weaknesses as bullet points

EXTREMELY IMPORTANT: Format your response as VALID JSON ONLY. No explanations or text outside of the JSON.
The valid JSON MUST be structured precisely as follows:
{{
    "competitors": [
        {{
            "name": "Competitor Name",
            "description": "Brief description of the competitor.",
            "strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "weaknesses": ["Weakness 1", "Weakness 2"]
        }},
        ...more competitors...
    ]
}}

IMPORTANT: Ensure valid JSON output with proper commas, brackets, and quotes. Do not include trailing commas. Your entire response must be valid parseable JSON and nothing else.
"""

            # Try up to 3 times to get valid JSON
            max_attempts = 3
            for attempt in range(max_attempts):
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
                    
                    # Collect the full response
                    response_text = ""
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=generate_content_config,
                    )
                    response_text = response.text
                    
                    # Clean the response before parsing
                    response_text = self._clean_json_response(response_text)
                    
                    # Try to parse the JSON
                    competitors_data = json.loads(response_text)
                    
                    # Validate the expected structure is present
                    if "competitors" not in competitors_data or not isinstance(competitors_data["competitors"], list):
                        raise ValueError("Response missing 'competitors' list")
                    
                    logging.info(f"Successfully identified competitors for {company_name}")
                    return competitors_data
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"Attempt {attempt+1}/{max_attempts} - Failed to parse JSON: {str(e)}")
                    if attempt == max_attempts - 1:  # If this was the last attempt
                        logging.error(f"All {max_attempts} attempts failed. Returning empty competitors list.")
                        logging.error(f"Last response: {response_text}")
                        return {"competitors": []}
                    # Wait briefly before retry
                    time.sleep(1)
            
            # This should not be reached due to the return in the loop, but just in case
            return {"competitors": []}
            
        except Exception as e:
            logging.error(f"Error identifying competitors: {str(e)}")
            return {"competitors": []}

    def _clean_json_response(self, text: str) -> str:
        """Clean and repair common JSON formatting issues in the model response."""
        # Extract JSON if it's wrapped in backticks, code blocks, etc.
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            text = json_match.group(1)
        
        # Try to fix common JSON formatting errors
        
        # Remove any non-JSON text before or after the JSON object
        text = re.sub(r'^[^{]*', '', text)
        text = re.sub(r'[^}]*$', '', text)
        
        # Fix missing commas in arrays
        text = re.sub(r'"\s*"', '", "', text)
        
        # Fix trailing commas before closing brackets
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        # Fix missing quotes around property names
        text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
        
        return text

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