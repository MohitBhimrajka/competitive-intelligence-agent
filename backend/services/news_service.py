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
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text was: {response_text}")
            raise

    async def get_news_with_gemini(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles for a competitor using Gemini's search capability.
        
        Args:
            competitor_name (str): Name of the competitor
            days_back (int): Number of days to look back for news
            
        Returns:
            list: List of news articles
        """
        try:
            # Calculate date range for consistency with NewsAPI
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            prompt = f"""
            Using search tools, find recent business and industry news articles specifically about the company "{competitor_name}".
            Focus on articles published between {from_date} and {to_date}.

            Look for news covering topics like:
            - Significant business announcements (product launches, strategy shifts)
            - Financial updates (earnings, funding, stock)
            - Major partnerships, mergers, or acquisitions
            - Competitive actions or market positioning changes
            - Leadership changes or company structure updates

            For each relevant article found, provide the following information. Prioritize articles focused on business impact.
            - "title": The exact title of the article.
            - "source": The name of the publication.
            - "url": The direct link to the article.
            - "publishedAt": The publication date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ), if available. If not, provide the date in YYYY-MM-DD format.
            - "content": A summary or excerpt from the article (a few sentences) that captures the main point. Note: Providing the full article content via this method may not be possible, so a good summary is expected.

            Return up to 10 of the most relevant articles found. If fewer than 10 relevant articles exist, return all that were found. If no relevant articles are found, return an empty array.

            Output ONLY the JSON object with the following exact structure:
            {{
                "articles": [
                    {{
                        "title": "...",
                        "source": "...",
                        "url": "...",
                        "publishedAt": "...",
                        "content": "..."
                    }},
                    ... (up to 10 articles)
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
                gemini_articles = result.get('articles', [])
                logger.info(f"Gemini found {len(gemini_articles)} news articles for {competitor_name}")
                return gemini_articles
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Gemini response: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting news with Gemini for {competitor_name}: {e}")
            return []

    async def get_competitor_news(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles for a competitor from both NewsAPI and Gemini.
        
        Args:
            competitor_name (str): Name of the competitor
            days_back (int): Number of days to look back for news
            
        Returns:
            list: List of news articles
        """
        news_api_articles = await self._get_news_api_articles(competitor_name, days_back)
        gemini_articles = await self.get_news_with_gemini(competitor_name, days_back)
        
        # Combine articles, deduplicate based on URL
        all_articles = []
        seen_urls = set()
        
        # Process NewsAPI articles first
        for article in news_api_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(article)
        
        # Then add Gemini articles that don't duplicate URLs
        for article in gemini_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                
                # Normalize field names to match NewsAPI format
                processed_article = {
                    'title': article.get('title', ''),
                    'source': article.get('source', 'Unknown'),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),  # Map publishedAt to published_at
                    'content': article.get('content', '')
                }
                all_articles.append(processed_article)
        
        logger.info(f"Retrieved {len(all_articles)} total news articles for {competitor_name} (NewsAPI: {len(news_api_articles)}, Gemini: {len(gemini_articles)})")
        return all_articles

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
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'content': article.get('content', article.get('description', '')),
                    }
                    articles.append(processed_article)
                    
            logger.info(f"NewsAPI retrieved {len(articles)} news articles for {competitor_name}")
            return articles
        
        except Exception as e:
            logger.error(f"Error getting news from NewsAPI for {competitor_name}: {e}")
            # Return empty list on error
            return [] 