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
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(json_pattern, response_text)

        if match:
            # Extract the JSON part from inside the code block
            json_str = match.group(1).strip() # Added strip
        else:
            # If no code block, try to find the first '{' and last '}'
            start_brace = response_text.find('{')
            end_brace = response_text.rfind('}')
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                json_str = response_text[start_brace:end_brace+1]
            else:
             # Fallback to the whole response if no clear JSON structure is found
                json_str = response_text

        try:
            logger.debug(f"Attempting to parse JSON: {json_str[:100]}...") # Debug level
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text snippet causing error: {response_text[:300]}...") # Log more context
            raise # Re-raise exception

    async def get_news_with_gemini(self, competitor_name: str, days_back: int = 30):
        """
        Get recent relevant developments for a competitor using Gemini's search capability.
        Returns a list of article dictionaries or an empty list on error.
        """
        logger.info(f"Fetching news with Gemini for {competitor_name}")
        try:
            prompt = NewsPrompts.get_news_with_gemini(competitor_name, days_back)
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(tools=tools, response_mime_type="text/plain")

            response_text = ""
            # --- MODIFIED STREAM HANDLING ---
            # generate_content_stream seems to return a synchronous iterator here
            # Let's consume it synchronously within the async function
            stream = self.gemini_client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            for chunk in stream:
                 part = getattr(chunk, 'parts', [None])[0]
                 text = getattr(part, 'text', None) if part else None
                 if text:
                      response_text += text
            # --- END MODIFICATION ---

            # Check if response_text is empty after loop
            if not response_text:
                 logger.warning(f"Gemini news stream returned no text for {competitor_name}.")
                 return []

            result = self._extract_json_from_response(response_text)
            if not isinstance(result, dict):
                logger.error(f"Invalid result type from Gemini news fetch: {type(result)}. Raw text: {response_text[:200]}")
                return []

            gemini_articles = result.get('articles', [])
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
                    'publishedAt': article.get('publishedAt', '') or '',
                    'content': article.get('content', 'No content available.') or 'No content available.'
                })

            logger.info(f"Gemini found {len(sanitized_articles)} relevant developments for {competitor_name}")
            return sanitized_articles

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini news response for {competitor_name}.")
            logger.error(f"Raw response text snippet: {response_text[:500]}") # Log more context on parse error
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
            response = self.news_api.get_everything(
                q=f'"{competitor_name}"',
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='relevancy',
                page_size=20 # Fetch a reasonable number
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
                        'content': article.get('content', article.get('description', 'No content available.')),
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
                    base_date_str = date_str.split('.')[0]
                    # Attempt ISO format parsing
                    return datetime.fromisoformat(base_date_str)
                except ValueError:
                    # Fallback for other unexpected formats
                    logger.warning(f"Could not parse date: '{date_str}' for sorting. Using fallback.")
                    return datetime.min # Fallback for unparseable dates
                except Exception as dt_err:
                    logger.error(f"Unexpected error parsing date '{date_str}': {dt_err}")
                    return datetime.min

            all_items.sort(key=sort_key, reverse=True)

            return all_items
        except Exception as e:
            # Catch errors during the gather/processing phase
            logger.error(f"Error during concurrent news fetch processing for {competitor_name}: {e}", exc_info=True)
            return [] # Return empty list on failure 