import os
import json
import re
from google import genai
from google.genai import types
import logging
from typing import Optional
import time
import asyncio
from .prompts import GeminiPrompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        try:
            # Initialize Gemini client using direct API key (not Vertex AI)
            api_key = os.getenv("GOOGLE_API_KEY")
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-2.0-flash-001"  # Using standard model instead of flash preview
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
            json_str = match.group(1).strip() # Added strip
            logger.debug("Found JSON inside markdown block.")
        else:
            # 2. If no markdown block, try finding the first '{' that likely starts the JSON
            brace_index = response_text.find('{')
            if brace_index != -1:
                 # Try to find the corresponding closing brace (simple check)
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
            # Added basic check for empty string before parsing
            if not json_str or not json_str.strip():
                logger.error("Cannot parse empty JSON string.")
                raise json.JSONDecodeError("Cannot parse empty JSON string.", "", 0)
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
        prompt = GeminiPrompts.company_analysis(company_name)
        
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
        # This function uses generate_content (non-streaming), so it should be less prone
        # to the stream processing issues. We'll focus on ensuring JSON parsing is robust.
        logger.info(f"Identifying competitors for {company_name} using non-streaming call.")
        try:
            prompt = GeminiPrompts.identify_competitors(company_name)
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain", # Expecting JSON, but request plain text
                temperature=self.temperature,
            )

            max_attempts = 3
            response_text = "" # Initialize
            for attempt in range(max_attempts):
                logger.info(f"Attempt {attempt+1}/{max_attempts} to identify competitors for {company_name}")
                try:
                    # Use non-streaming call
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=generate_content_config,
                    )
                    response_text = response.text # Get the full text response

                    if not response_text or not response_text.strip():
                        logger.warning(f"Received empty response text on attempt {attempt+1}")
                        raise ValueError("Empty response text")

                    logger.debug(f"Raw response for competitor identification: {response_text[:500]}")

                    # Try to parse the JSON using the robust extractor
                    competitors_data = self._extract_json_from_response(response_text)

                    # Validate the expected structure
                    if not isinstance(competitors_data, dict) or "competitors" not in competitors_data or not isinstance(competitors_data["competitors"], list):
                        logger.error(f"Invalid JSON structure received: {competitors_data}")
                        raise ValueError("Response missing 'competitors' list or invalid structure")

                    logger.info(f"Successfully identified and parsed competitors for {company_name}")
                    return competitors_data # Success!

                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Attempt {attempt+1} failed: Error parsing JSON or validating structure: {str(e)}")
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for competitor identification.")
                        logger.error(f"Last raw response text: {response_text}")
                        return {"competitors": []} # Fallback
                    await asyncio.sleep(1) # Wait before retry

                except Exception as e:
                    logger.error(f"Attempt {attempt+1} failed: Unexpected error during Gemini call: {str(e)}")
                    if attempt == max_attempts - 1:
                         logger.error(f"All {max_attempts} attempts failed due to API errors.")
                         return {"competitors": []} # Fallback
                    await asyncio.sleep(1) # Wait before retry

            # Fallback if loop finishes unexpectedly
            return {"competitors": []}

        except Exception as e:
            logger.error(f"Critical error in identify_competitors function: {str(e)}")
            return {"competitors": []} # General fallback

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
        
        prompt = GeminiPrompts.generate_insights(company_name, competitors_data, news_context)
        
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

    async def deep_research_competitor(self, competitor_name: str, competitor_description: Optional[str], company_name: Optional[str] = None):
        """Generates an in-depth research report for a competitor using a Pro model."""
        logger.info(f"Starting deep research for: {competitor_name} using model {self.pro_model}")
        company_context = f"for {company_name}" if company_name else ""
        prompt = GeminiPrompts.deep_research_competitor(competitor_name, competitor_description, company_name)
        response_text = "" # Initialize

        try:
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain",
                temperature=0.65
            )

            logger.info(f"Generating deep research using model: {self.pro_model} for {competitor_name}")

            # --- CORRECTED STREAM HANDLING ---
            stream = self.client.models.generate_content_stream(
                model=self.pro_model,
                contents=contents,
                config=generate_content_config,
            )
            for chunk in stream:
                 # Use hasattr to check for text attribute directly on the chunk
                 if hasattr(chunk, 'text'):
                      response_text += chunk.text
            # --- END CORRECTION ---


            # --- VALIDATION and PREAMBLE STRIPPING ---
            if not response_text or len(response_text.strip()) < 100: # Basic check for empty or very short response
                logger.warning(f"Deep research for {competitor_name} returned empty or unexpectedly short content (Length: {len(response_text.strip())}).")
                logger.warning(f"Response snippet received: {response_text[:500]}")
                return f"## Error\n\nDeep research generation for {competitor_name} failed to produce sufficient content. The response was empty or too short."

            # --- START PREAMBLE STRIPPING ---
            cleaned_response_text = response_text.strip()
            # Keep error/warning markdown as is
            if cleaned_response_text.startswith("## Error") or cleaned_response_text.startswith("## Warning"):
                logger.warning(f"Deep research for {competitor_name} resulted in a warning or error message from the service.")
                # No stripping needed, return the error/warning markdown
            # Check if it *doesn't* start with '#' but *does* contain a likely markdown header start ('# ')
            elif not cleaned_response_text.startswith("#") and '# ' in cleaned_response_text:
                first_header_index = cleaned_response_text.find('# ')
                if first_header_index != -1:
                    # Find the beginning of that line
                    line_start_index = cleaned_response_text.rfind('\n', 0, first_header_index) + 1
                    cleaned_response_text = cleaned_response_text[line_start_index:]
                    logger.info(f"Stripped preamble from deep research for {competitor_name}.")
                else:
                    # Fallback if '# ' is present but logic fails - log warning
                    logger.warning(f"Could not reliably strip preamble for {competitor_name}, despite detecting '# '. Using original.")
            elif not cleaned_response_text.startswith("#"):
                 logger.warning(f"Deep research for {competitor_name} did not start with '#' and no clear header found. Returning potentially unformatted content.")
            # --- END PREAMBLE STRIPPING ---

            logger.info(f"Deep research final content generated for: {competitor_name} {company_context} (Length: {len(cleaned_response_text)})")
            logger.debug(f"Deep research content snippet after cleaning: {cleaned_response_text[:1000]}") # Log cleaned snippet

            return cleaned_response_text # Return the cleaned markdown
            # --- END VALIDATION ---

        except Exception as e:
            logger.error(f"Error during deep research API call for {competitor_name} {company_context}: {e}", exc_info=True)
            # Return a Markdown formatted error
            return f"## Error\n\nAn error occurred during the API call for deep research generation for {competitor_name}:\n\n```\n{str(e)}\n```" 