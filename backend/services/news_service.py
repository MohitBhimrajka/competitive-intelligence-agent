import os
import json
import re
import logging
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        try:
            # Initialize News API client
            self.news_api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
            
            # Initialize Gemini API client
            api_key = os.getenv("GOOGLE_API_KEY")
            self.gemini_client = genai.Client(api_key=api_key)
            self.model = "gemini-2.5-pro-preview-03-25"
            
            logger.info("News API service initialized")
        except Exception as e:
            logger.error(f"Error initializing News API service: {e}")
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

    async def get_news_with_gemini(self, competitor_name: str, days_back: int = 30):
        """
        Get recent relevant developments for a competitor using Gemini's search capability.
        """
        try:
            # Calculate date range for logging purposes, but don't strictly enforce in prompt
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            prompt = f"""
            Using search tools, find recent (roughly within the last {days_back} days) significant developments, announcements, or discussions about the company "{competitor_name}".
            This could include news articles, major blog posts, press releases, or significant website updates related to:
            - Business strategy, product launches, or partnerships
            - Financial news (funding, earnings reports if significant)
            - Mergers, acquisitions, or leadership changes
            - Major competitive actions or market positioning statements

            For each relevant item found, provide the following information. Prioritize items with clear business impact.
            - "title": The title or a concise description of the development.
            - "source": The name of the publication, website, or source type (e.g., "Company Blog", "TechCrunch", "Press Release").
            - "url": The direct link if available.
            - "publishedAt": The publication date/time (ISO 8601 format YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD preferred). If unavailable, use null or omit.
            - "content": A brief summary (a few sentences) explaining the development and its significance.

            Return up to 5-7 of the most relevant items found. If fewer relevant items exist, return all that were found. If no relevant items are found, return an empty array.

            IMPORTANT: Output ONLY the JSON object with the following exact structure.
            **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
            - Each object must end with a comma if it's not the last item in the list
            - All arrays and objects must be properly closed with ] or }}
            - No trailing commas after the last item in an array or object
            - All property names must be in double quotes
            - All string values must be in double quotes
            
            {{
                "articles": [
                    {{
                        "title": "...",
                        "source": "...",
                        "url": "...",
                        "publishedAt": "...",
                        "content": "..."
                    }},
                    ... (up to 5-7 items)
                ]
            }}
            """
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ]
            
            # Enable Google Search for grounding
            tools = [types.Tool(google_search=types.GoogleSearch())]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain",
            )
            
            # Collect the full response from stream
            response_text = ""
            for chunk in self.gemini_client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, 'text'):
                    response_text += chunk.text
            
            # Extract JSON from response
            try:
                result = self._extract_json_from_response(response_text)
                if not isinstance(result, dict):
                    logger.error(f"Invalid result type from Gemini: {type(result)}")
                    return []
                gemini_articles = result.get('articles', [])
                logger.info(f"Gemini found {len(gemini_articles)} relevant developments for {competitor_name}")
                return gemini_articles
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Gemini response: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting news with Gemini for {competitor_name}: {e}")
            return []

    async def get_competitor_news(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles and relevant developments for a competitor from both NewsAPI and Gemini.
        
        Args:
            competitor_name (str): Name of the competitor
            days_back (int): Number of days to look back for news
            
        Returns:
            list: List of news articles and relevant developments
        """
        news_api_articles = await self._get_news_api_articles(competitor_name, days_back)
        gemini_developments = await self.get_news_with_gemini(competitor_name, days_back)
        
        # Combine articles, deduplicate based on URL
        all_items = []
        seen_urls = set()
        
        # Process NewsAPI articles first
        for article in news_api_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                processed_article = {
                    'title': article.get('title', ''),
                    'source': article.get('source', 'Unknown'),
                    'url': url,
                    'published_at': article.get('published_at') or "",  # Ensure string
                    'content': article.get('content', '')
                }
                all_items.append(processed_article)
            elif not url:  # Handle NewsAPI articles potentially missing URL
                processed_article = {
                    'title': article.get('title', ''),
                    'source': article.get('source', 'Unknown'),
                    'url': None,
                    'published_at': article.get('published_at') or "",  # Ensure string
                    'content': article.get('content', '')
                }
                all_items.append(processed_article)
        
        # Then add Gemini items that don't duplicate URLs
        for item in gemini_developments:
            url = item.get('url', '')
            if url:
                if url not in seen_urls:
                    seen_urls.add(url)
                    processed_item = {
                        'title': item.get('title', ''),
                        'source': item.get('source', 'Unknown'),
                        'url': url,
                        'published_at': item.get('publishedAt') or "",  # Ensure string
                        'content': item.get('content', '')
                    }
                    all_items.append(processed_item)
            else:
                # Add items without URL
                processed_item = {
                    'title': item.get('title', ''),
                    'source': item.get('source', 'Unknown Source'),
                    'url': None,
                    'published_at': item.get('publishedAt') or "",  # Ensure string
                    'content': item.get('content', '')
                }
                all_items.append(processed_item)
        
        logger.info(f"Retrieved {len(all_items)} total items for {competitor_name} (NewsAPI: {len(news_api_articles)}, Gemini: {len(gemini_developments)})")
        
        # Sort by publication date, newest first (with a fallback for missing dates)
        all_items.sort(key=lambda x: x.get('published_at') or '0000-00-00', reverse=True)
        
        return all_items

    async def _get_news_api_articles(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles for a competitor from NewsAPI.
        
        Args:
            competitor_name (str): Name of the competitor
            days_back (int): Number of days to look back for news
            
        Returns:
            list: List of news articles
        """
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get articles from News API
            response = self.news_api.get_everything(
                q=f'"{competitor_name}" (company OR business OR industry)',
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='relevancy',
                page_size=10
            )
            
            articles = []
            if response and response.get('status') == 'ok':
                for article in response.get('articles', []):
                    # Process each article
                    processed_article = {
                        'title': article.get('title', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': article.get('url'),
                        'published_at': article.get('publishedAt') or "",  # Ensure string
                        'content': article.get('content', article.get('description', '')),
                    }
                    articles.append(processed_article)
                    
            logger.info(f"NewsAPI retrieved {len(articles)} news articles for {competitor_name}")
            return articles
        
        except Exception as e:
            logger.error(f"Error getting news from NewsAPI for {competitor_name}: {e}")
            # Return empty list on error
            return [] 