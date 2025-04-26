import os
import json
import re
import logging
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from .prompts import NewsPrompts

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
            self.model = "gemini-2.5-flash-preview-04-17"
            
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
            
            prompt = NewsPrompts.get_news_with_gemini(competitor_name, days_back)
            
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
                
                # Validate articles and ensure all fields have safe defaults
                sanitized_articles = []
                for article in gemini_articles:
                    if not isinstance(article, dict):
                        logger.warning(f"Skipping non-dict article: {type(article)}")
                        continue
                        
                    sanitized_article = {
                        'title': article.get('title', '') or '',
                        'source': article.get('source', 'Unknown') or 'Unknown',
                        'url': article.get('url') if article.get('url') else None,
                        'publishedAt': article.get('publishedAt', '') or '',
                        'content': article.get('content', '') or ''
                    }
                    sanitized_articles.append(sanitized_article)
                
                logger.info(f"Gemini found {len(sanitized_articles)} relevant developments for {competitor_name}")
                return sanitized_articles
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
        try:
            news_api_articles = await self._get_news_api_articles(competitor_name, days_back)
            gemini_developments = await self.get_news_with_gemini(competitor_name, days_back)
            
            # Combine articles, deduplicate based on URL
            all_items = []
            seen_urls = set()
            
            # Process NewsAPI articles first
            for article in news_api_articles:
                if not isinstance(article, dict):
                    logger.warning(f"Skipping non-dict NewsAPI article: {type(article)}")
                    continue
                    
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    processed_article = {
                        'title': article.get('title', '') or '',
                        'source': article.get('source', 'Unknown') or 'Unknown',
                        'url': url,
                        'published_at': article.get('published_at', '') or '',
                        'content': article.get('content', '') or ''
                    }
                    all_items.append(processed_article)
                elif not url:  # Handle NewsAPI articles potentially missing URL
                    processed_article = {
                        'title': article.get('title', '') or '',
                        'source': article.get('source', 'Unknown') or 'Unknown',
                        'url': None,
                        'published_at': article.get('published_at', '') or '',
                        'content': article.get('content', '') or ''
                    }
                    all_items.append(processed_article)
            
            # Then add Gemini items that don't duplicate URLs
            for item in gemini_developments:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict Gemini item: {type(item)}")
                    continue
                    
                url = item.get('url', '')
                if url:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        processed_item = {
                            'title': item.get('title', '') or '',
                            'source': item.get('source', 'Unknown') or 'Unknown',
                            'url': url,
                            'published_at': item.get('publishedAt', '') or '',
                            'content': item.get('content', '') or ''
                        }
                        all_items.append(processed_item)
                else:
                    # Add items without URL
                    processed_item = {
                        'title': item.get('title', '') or '',
                        'source': item.get('source', 'Unknown Source') or 'Unknown Source',
                        'url': None,
                        'published_at': item.get('publishedAt', '') or '',
                        'content': item.get('content', '') or ''
                    }
                    all_items.append(processed_item)
            
            logger.info(f"Retrieved {len(all_items)} total items for {competitor_name} (NewsAPI: {len(news_api_articles)}, Gemini: {len(gemini_developments)})")
            
            # Sort by publication date, newest first (with a fallback for missing dates)
            # Ensure sort key never returns None to prevent TypeError
            all_items.sort(key=lambda x: (x.get('published_at') or '0000-00-00'), reverse=True)
            
            return all_items
        except Exception as e:
            logger.error(f"Error in get_competitor_news for {competitor_name}: {e}")
            return []

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