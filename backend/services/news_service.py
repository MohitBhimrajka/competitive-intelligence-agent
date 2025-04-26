import os
import json
import re
import logging
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import asyncio # Import asyncio
from .prompts import NewsPrompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        try:
            # Initialize News API client only if key exists
            news_api_key = os.getenv("NEWS_API_KEY")
            if news_api_key:
                 self.news_api = NewsApiClient(api_key=news_api_key)
                 logger.info("News API client initialized.")
            else:
                 self.news_api = None
                 logger.warning("NEWS_API_KEY not set. NewsAPI fetching will be skipped.")

            # Initialize Gemini API client
            api_key = os.getenv("GOOGLE_API_KEY")
            # Add error handling for missing Google API key
            if not api_key:
                 logger.error("GOOGLE_API_KEY not set. Cannot initialize Gemini client for News Service.")
                 raise ValueError("GOOGLE_API_KEY environment variable not set.")
            self.gemini_client = genai.Client(api_key=api_key)
            self.model = "gemini-2.5-flash-preview-04-17" # Or your chosen model

            logger.info("Gemini client for News Service initialized")
        except Exception as e:
            logger.error(f"Error initializing News Service components: {e}")
            raise

    def _extract_json_from_response(self, response_text):
        """Extract JSON from response text, handling markdown code blocks."""
        # Check if response is wrapped in markdown code blocks
        json_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```" # More specific pattern for object
        match = re.search(json_pattern, response_text)

        json_str = None
        if match:
            json_str = match.group(1).strip()
            logger.debug("Found JSON inside markdown block.")
        else:
            # If no markdown block, try finding the first '{' that likely starts the JSON
            brace_index = response_text.find('{')
            if brace_index != -1:
                 # Try to find the corresponding closing brace (simple check)
                 potential_json = response_text[brace_index:]
                 if potential_json.strip().endswith('}'):
                      json_str = potential_json
                      logger.debug("Found JSON by searching for first '{'.")
                 else:
                      logger.warning("Found '{' but text doesn't seem to end with '}'. Using full response.")
                      json_str = response_text # Fallback to whole text if unsure
            else:
                logger.debug("No JSON block or starting '{' found. Using full response text.")
                json_str = response_text

        try:
            logger.debug(f"Attempting to parse JSON: {json_str[:100]}...") # Debug level
            # Added basic check for empty string before parsing
            if not json_str or not json_str.strip():
                logger.error("Cannot parse empty JSON string.")
                raise json.JSONDecodeError("Cannot parse empty JSON string.", "", 0)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text snippet causing error: {response_text[:300]}...") # Log more context
            raise # Re-raise exception
        except Exception as e: # Catch other potential errors
             logger.error(f"Unexpected error during JSON parsing: {e}")
             logger.error(f"Attempted to parse: {json_str}")
             raise json.JSONDecodeError(f"Unexpected error during JSON parsing: {e}", json_str or "", 0) # Raise standard error

    async def get_news_with_gemini(self, competitor_name: str, days_back: int = 30):
        """
        Get recent relevant developments for a competitor using Gemini's search capability.
        Returns a list of article dictionaries or an empty list on error.
        """
        logger.info(f"Fetching news with Gemini for {competitor_name}")
        response_text = "" # Initialize response_text here
        try:
            prompt = NewsPrompts.get_news_with_gemini(competitor_name, days_back)
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            tools = [types.Tool(google_search=types.GoogleSearch())]
            # Ensure temperature is set if desired, otherwise defaults apply
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain"
                # temperature=0.7 # Optional: Add temperature if needed
            )

            # --- CORRECTED STREAM HANDLING ---
            stream = self.gemini_client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            for chunk in stream:
                 # Use hasattr to check for text attribute directly on the chunk
                 if hasattr(chunk, 'text'):
                      response_text += chunk.text
                 # Optional: Log if chunks are received but don't have text
                 # else:
                 #    logger.debug(f"Received chunk without text attribute: {chunk}")
            # --- END CORRECTION ---

            # Check if response_text is empty after loop
            if not response_text or not response_text.strip(): # Added strip check
                 logger.warning(f"Gemini news stream returned no usable text for {competitor_name}.")
                 return []

            # Log the raw response before parsing
            logger.debug(f"Raw response text from Gemini news stream for {competitor_name}: {response_text[:500]}")

            result = self._extract_json_from_response(response_text)

            # Validate the result structure after parsing
            if not isinstance(result, dict):
                logger.error(f"Invalid result type after JSON parsing: {type(result)}. Raw text: {response_text[:200]}")
                return []
            if 'articles' not in result or not isinstance(result['articles'], list):
                logger.error(f"Parsed JSON missing 'articles' list or wrong type. Parsed: {result}. Raw text: {response_text[:200]}")
                return []

            gemini_articles = result.get('articles', []) # Safe get just in case
            sanitized_articles = []
            for article in gemini_articles:
                if not isinstance(article, dict):
                    logger.warning(f"Skipping non-dict article from Gemini: {type(article)}")
                    continue
                # Standardize keys and provide safe defaults
                sanitized_articles.append({
                    'title': article.get('title', 'Untitled') or 'Untitled',
                    'source': article.get('source', 'Unknown Source') or 'Unknown Source',
                    'url': article.get('url') if article.get('url') else None,
                    # Standardize publishedAt key if needed
                    'publishedAt': article.get('publishedAt', article.get('published_at', '')) or '',
                    'content': article.get('content', 'No content available.') or 'No content available.'
                })

            logger.info(f"Gemini found {len(sanitized_articles)} relevant developments for {competitor_name}")
            return sanitized_articles

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini news response for {competitor_name}.")
            # Log the full response text that failed parsing
            logger.error(f"Raw response text that failed JSON parsing: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Error getting news with Gemini for {competitor_name}: {e}", exc_info=True)
            return [] # Return empty list on any error

    async def _get_news_api_articles(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles for a competitor from NewsAPI.
        Returns a list of article dictionaries or an empty list on error.
        """
        if not self.news_api:
             logger.info(f"Skipping NewsAPI fetch for {competitor_name} as API key is not configured.")
             return []

        logger.info(f"Fetching news with NewsAPI for {competitor_name}")
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')

            # Using a simpler query might yield broader but potentially relevant results
            # Run the synchronous NewsAPI call in an executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,  # Use default executor
                lambda: self.news_api.get_everything(
                    q=f'"{competitor_name}"',
                    from_param=from_date,
                    to=to_date,
                    language='en',
                    sort_by='relevancy',
                    page_size=20 # Fetch a reasonable number
                )
            )

            articles = []
            if response and response.get('status') == 'ok':
                for article in response.get('articles', []):
                    # Standardize keys and provide safe defaults
                    articles.append({
                        'title': article.get('title', 'Untitled') or 'Untitled',
                        'source': article.get('source', {}).get('name', 'Unknown Source') or 'Unknown Source',
                        'url': article.get('url'),
                        'publishedAt': article.get('publishedAt') or "",
                        # Use description if content is missing or empty
                        'content': article.get('content') or article.get('description', 'No content available.') or 'No content available.',
                    })
            logger.info(f"NewsAPI retrieved {len(articles)} news articles for {competitor_name}")
            return articles
        except Exception as e:
            logger.error(f"Error getting news from NewsAPI for {competitor_name}: {e}", exc_info=True)
            return [] # Return empty list on error

    async def get_competitor_news(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles and developments for a competitor from NewsAPI and Gemini CONCURRENTLY.
        """
        logger.info(f"Initiating concurrent news fetch for {competitor_name}")
        tasks = [
            self.get_news_with_gemini(competitor_name, days_back),
            self._get_news_api_articles(competitor_name, days_back) # This will return [] if NewsAPI is not configured
        ]

        try:
            # Run tasks concurrently and capture results or exceptions
            results = await asyncio.gather(*tasks, return_exceptions=True)

            gemini_developments = []
            news_api_articles = []

            # Safely process Gemini results
            if isinstance(results[0], Exception):
                logger.error(f"Gemini news fetch task failed for {competitor_name}: {results[0]}")
            elif isinstance(results[0], list):
                gemini_developments = results[0]
            else:
                logger.error(f"Unexpected result type from Gemini fetch task for {competitor_name}: {type(results[0])}")

            # Safely process NewsAPI results
            if isinstance(results[1], Exception):
                logger.error(f"NewsAPI fetch task failed for {competitor_name}: {results[1]}")
            elif isinstance(results[1], list):
                news_api_articles = results[1]
            else:
                logger.error(f"Unexpected result type from NewsAPI fetch task for {competitor_name}: {type(results[1])}")

            # Combine and deduplicate results
            all_items = []
            seen_urls = set()
            combined_raw = gemini_developments + news_api_articles

            for item in combined_raw:
                # Skip if item is not a dictionary (handles potential malformed data)
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item during combination: {type(item)}")
                    continue

                # Standardize dictionary keys before processing
                processed_item = {
                    'title': item.get('title', 'Untitled') or 'Untitled',
                    'source': item.get('source', 'Unknown Source') or 'Unknown Source',
                    'url': item.get('url') if item.get('url') else None,
                    'published_at': item.get('publishedAt', item.get('published_at', '')) or '', # Check both keys
                    'content': item.get('content', 'No content available.') or 'No content available.'
                }

                url = processed_item['url']
                if url:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_items.append(processed_item)
                    # else: logger.debug(f"Skipping duplicate URL: {url}") # Optional: Log duplicates
                else:
                    # Always add items without a URL, maybe add basic title check for duplicates later if needed
                    # Let's add a simple check for duplicates based on title and source for URL-less items
                    item_key = (processed_item['title'].lower(), processed_item['source'].lower())
                    if item_key not in seen_urls: # Re-using seen_urls for title/source pairs
                        seen_urls.add(item_key)
                        all_items.append(processed_item)


            logger.info(f"Retrieved {len(all_items)} unique items for {competitor_name} (Gemini results: {len(gemini_developments)}, NewsAPI results: {len(news_api_articles)})")

            # Sort by publication date, newest first
            def sort_key(item):
                date_str = item.get('published_at', '')
                if not date_str: return datetime.min # Handle empty strings
                try:
                    # Handle 'Z' timezone designator
                    if date_str.endswith('Z'):
                        date_str = date_str[:-1] + '+00:00'
                    # Handle potential fractional seconds by splitting
                    # Handle potential timezone offsets like +09:00 by removing them if isoformat fails initially
                    base_date_str = date_str.split('.')[0].split('+')[0].split('-')[0:3] # Keep only YYYY-MM-DD
                    base_date_str = '-'.join(base_date_str) # Rejoin date part

                    # Attempt ISO format parsing on date part only if full parsing fails
                    return datetime.fromisoformat(base_date_str)

                except ValueError:
                     # Fallback for other unexpected formats
                    logger.warning(f"Could not parse date: '{date_str}' for sorting. Using fallback.")
                    return datetime.min # Fallback for unparseable dates
                except Exception as dt_err:
                    logger.error(f"Unexpected error parsing date '{date_str}': {dt_err}")
                    return datetime.min

            # Sort safely
            try:
                all_items.sort(key=sort_key, reverse=True)
            except Exception as sort_err:
                 logger.error(f"Error sorting news items for {competitor_name}: {sort_err}")
                 # Proceed with unsorted items if sorting fails

            return all_items
        except Exception as e:
            # Catch errors during the gather/processing phase
            logger.error(f"Error during concurrent news fetch processing for {competitor_name}: {e}", exc_info=True)
            return [] # Return empty list on failure 