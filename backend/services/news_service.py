import os
from newsapi import NewsApiClient
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        try:
            self.news_api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
            logger.info("News API service initialized")
        except Exception as e:
            logger.error(f"Error initializing News API service: {e}")
            raise

    async def get_competitor_news(self, competitor_name: str, days_back: int = 30):
        """
        Get news articles for a competitor from the last specified days.
        
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
                    
            logger.info(f"Retrieved {len(articles)} news articles for {competitor_name}")
            return articles
        
        except Exception as e:
            logger.error(f"Error getting news for {competitor_name}: {e}")
            # Return empty list on error
            return [] 