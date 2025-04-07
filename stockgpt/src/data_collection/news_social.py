import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import logging
import os
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
import newspaper
from newspaper import Article
import praw

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsSocialCollector:
    def __init__(self, config_path='config/data_sources.json'):
        """Initialize the news and social media collector with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data_dir = Path('data/raw/news_social')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize Reddit API if credentials are provided
        reddit_config = self.config.get('reddit', {})
        if all(k in reddit_config for k in ['client_id', 'client_secret', 'user_agent']):
            self.reddit = praw.Reddit(
                client_id=reddit_config['client_id'],
                client_secret=reddit_config['client_secret'],
                user_agent=reddit_config['user_agent']
            )
        else:
            self.reddit = None
            logger.warning("Reddit API credentials not provided. Reddit data collection will be unavailable.")
        
    def get_company_news(self, symbol, days_back=30):
        """Collect recent news articles about a company."""
        try:
            articles = []
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get news from MoneyControl
            mc_articles = self._get_moneycontrol_news(symbol, start_date, end_date)
            if mc_articles:
                articles.extend(mc_articles)
            
            # Get news from Economic Times
            et_articles = self._get_economic_times_news(symbol, start_date, end_date)
            if et_articles:
                articles.extend(et_articles)
            
            # Convert to DataFrame
            if articles:
                news_df = pd.DataFrame(articles)
                logger.info(f"Collected {len(news_df)} news articles for {symbol}")
                return news_df
            else:
                logger.warning(f"No news articles found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error collecting news for {symbol}: {str(e)}")
            return None
    
    def _get_moneycontrol_news(self, symbol, start_date, end_date):
        """Get news articles from MoneyControl."""
        try:
            articles = []
            
            # Map stock symbol to MoneyControl URL
            symbol_map = self.config.get('moneycontrol_symbols', {})
            mc_symbol = symbol_map.get(symbol)
            
            if not mc_symbol:
                logger.warning(f"No mapping found for {symbol} in MoneyControl")
                return []
                
            url = f"https://www.moneycontrol.com/stocks/company_info/stock_news.php?sc_id={mc_symbol}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch news from MoneyControl for {symbol}: Status code {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract news articles
            news_items = soup.find_all('div', {'class': 'MT15'})
            
            for item in news_items:
                try:
                    headline_elem = item.find('h2')
                    if not headline_elem:
                        continue
                        
                    headline = headline_elem.text.strip()
                    link = headline_elem.find('a')['href']
                    
                    # Extract date
                    date_elem = item.find('span', {'class': 'gray10'})
                    if date_elem:
                        date_str = date_elem.text.strip()
                        try:
                            article_date = datetime.strptime(date_str, "%b %d, %Y")
                            
                            # Check if article is within our date range
                            if article_date < start_date or article_date > end_date:
                                continue
                        except:
                            # If we can't parse the date, include it anyway
                            article_date = None
                    else:
                        article_date = None
                    
                    # Download and parse the full article
                    article = self._parse_article(link)
                    
                    if article:
                        articles.append({
                            'Symbol': symbol,
                            'Headline': headline,
                            'Date': article_date,
                            'Source': 'MoneyControl',
                            'URL': link,
                            'Content': article.get('text', ''),
                            'Summary': article.get('summary', '')
                        })
                except Exception as e:
                    logger.error(f"Error processing news item: {str(e)}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting MoneyControl news for {symbol}: {str(e)}")
            return []
    
    def _get_economic_times_news(self, symbol, start_date, end_date):
        """Get news articles from Economic Times."""
        # Similar implementation for Economic Times
        # ...
        return []
    
    def _parse_article(self, url):
        """Download and parse a news article."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()  # This generates summary and keywords
            
            return {
                'text': article.text,
                'summary': article.summary,
                'keywords': article.keywords,
                'publish_date': article.publish_date
            }
            
        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None
    
    def get_social_media_sentiment(self, symbol, days_back=7, platform='reddit'):
        """Collect social media posts about a company."""
        if platform == 'reddit':
            return self._get_reddit_posts(symbol, days_back)
        # Add other platforms as needed
        
        return None
    
    def _get_reddit_posts(self, symbol, days_back):
        """Get Reddit posts about a company."""
        try:
            if self.reddit is None:
                logger.warning("Reddit API not initialized")
                return None
                
            posts = []
            subreddit = self.reddit.subreddit('IndiaInvestments+indiainvesting+DalalStreetTalks')
            
            # Calculate date threshold
            threshold = int((datetime.now() - timedelta(days=days_back)).timestamp())
            
            # Search for posts containing the symbol
            search_query = f"{symbol} OR {symbol}.NS OR {symbol}.BO"
            for post in subreddit.search(search_query, limit=100):
                if post.created_utc >= threshold:
                    posts.append({
                        'Symbol': symbol,
                        'Title': post.title,
                        'Content': post.selftext,
                        'Score': post.score,
                        'Comments': post.num_comments,
                        'Date': datetime.fromtimestamp(post.created_utc),
                        'URL': f"https://www.reddit.com{post.permalink}",
                        'Platform': 'Reddit'
                    })
            
            if posts:
                posts_df = pd.DataFrame(posts)
                logger.info(f"Collected {len(posts_df)} Reddit posts for {symbol}")
                return posts_df
            else:
                logger.warning(f"No Reddit posts found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error collecting Reddit posts for {symbol}: {str(e)}")
            return None
    
    def save_news_social_data(self, data, symbol, data_type, file_format='csv'):
        """Save news and social media data to a file."""
        try:
            file_path = self.data_dir / f"{symbol}_{data_type}_{datetime.now().strftime('%Y%m%d')}.{file_format}"
            
            if file_format == 'csv':
                data.to_csv(file_path, index=False)
            elif file_format == 'json':
                data.to_json(file_path, orient='records')
            else:
                logger.error(f"Unsupported file format: {file_format}")
                return False
                
            logger.info(f"News/social data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving news/social data: {str(e)}")
            return False 