import pandas as pd
import numpy as np
import logging
from pathlib import Path
import os
import json
import re
from datetime import datetime, timedelta
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import random
from typing import Dict, List, Optional
import yfinance as yf
from bs4 import BeautifulSoup
import requests
from textblob import TextBlob
import tweepy
import praw
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentimentAnalysis:
    def __init__(self, cache_dir: str = "data/processed/news_social"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=6)  # Cache TTL of 6 hours
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize social media APIs
        self._init_twitter_api()
        self._init_reddit_api()

    def _init_twitter_api(self):
        """Initialize Twitter API client."""
        try:
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.twitter_api = tweepy.API(auth)
        except Exception as e:
            self.logger.error(f"Error initializing Twitter API: {str(e)}")
            self.twitter_api = None

    def _init_reddit_api(self):
        """Initialize Reddit API client."""
        try:
            self.reddit_api = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent='StockGPT/1.0'
            )
        except Exception as e:
            self.logger.error(f"Error initializing Reddit API: {str(e)}")
            self.reddit_api = None

    def get_sentiment_data(self, symbol: str) -> Dict:
        """Get comprehensive sentiment data for a stock."""
        try:
            # Check cache first
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                return cached_data

            # Get news sentiment
            news_sentiment = self._get_news_sentiment(symbol)
            
            # Get social media sentiment
            twitter_sentiment = self._get_twitter_sentiment(symbol)
            reddit_sentiment = self._get_reddit_sentiment(symbol)
            
            # Calculate overall sentiment score
            overall_sentiment = self._calculate_overall_sentiment(
                news_sentiment,
                twitter_sentiment,
                reddit_sentiment
            )
            
            # Combine all data
            sentiment_data = {
                "news": news_sentiment,
                "twitter": twitter_sentiment,
                "reddit": reddit_sentiment,
                "overall": overall_sentiment
            }
            
            # Cache the results
            self._save_to_cache(symbol, sentiment_data)
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Error getting sentiment data for {symbol}: {str(e)}")
            return self._get_mock_data()

    def _get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment from various sources."""
        try:
            # Get news from Yahoo Finance
            stock = yf.Ticker(symbol)
            news = stock.news
            
            # Analyze sentiment for each news item
            news_sentiment = []
            for item in news:
                title = item.get('title', '')
                summary = item.get('summary', '')
                
                # Calculate sentiment
                title_sentiment = TextBlob(title).sentiment.polarity
                summary_sentiment = TextBlob(summary).sentiment.polarity
                
                news_sentiment.append({
                    "title": title,
                    "summary": summary,
                    "title_sentiment": title_sentiment,
                    "summary_sentiment": summary_sentiment,
                    "date": item.get('date', ''),
                    "source": item.get('source', '')
                })
            
            # Calculate average sentiment
            avg_sentiment = np.mean([item['title_sentiment'] for item in news_sentiment])
            
            return {
                "articles": news_sentiment,
                "average_sentiment": avg_sentiment
            }
            
        except Exception as e:
            self.logger.error(f"Error getting news sentiment: {str(e)}")
            return {"articles": [], "average_sentiment": 0.0}

    def _get_twitter_sentiment(self, symbol: str) -> Dict:
        """Get sentiment from Twitter."""
        if not self.twitter_api:
            return {"tweets": [], "average_sentiment": 0.0}
            
        try:
            # Search for tweets about the stock
            tweets = self.twitter_api.search_tweets(
                q=f"${symbol} OR {symbol}",
                lang="en",
                count=100
            )
            
            # Analyze sentiment for each tweet
            tweet_sentiment = []
            for tweet in tweets:
                sentiment = TextBlob(tweet.text).sentiment.polarity
                tweet_sentiment.append({
                    "text": tweet.text,
                    "sentiment": sentiment,
                    "date": tweet.created_at.isoformat(),
                    "retweets": tweet.retweet_count,
                    "likes": tweet.favorite_count
                })
            
            # Calculate average sentiment
            avg_sentiment = np.mean([tweet['sentiment'] for tweet in tweet_sentiment])
            
            return {
                "tweets": tweet_sentiment,
                "average_sentiment": avg_sentiment
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Twitter sentiment: {str(e)}")
            return {"tweets": [], "average_sentiment": 0.0}

    def _get_reddit_sentiment(self, symbol: str) -> Dict:
        """Get sentiment from Reddit."""
        if not self.reddit_api:
            return {"posts": [], "average_sentiment": 0.0}
            
        try:
            # Search for posts about the stock
            posts = []
            for subreddit in ['stocks', 'investing', 'wallstreetbets']:
                for post in self.reddit_api.subreddit(subreddit).search(symbol, limit=10):
                    sentiment = TextBlob(post.title + " " + post.selftext).sentiment.polarity
                    posts.append({
                        "title": post.title,
                        "text": post.selftext,
                        "sentiment": sentiment,
                        "date": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "upvotes": post.ups,
                        "subreddit": subreddit
                    })
            
            # Calculate average sentiment
            avg_sentiment = np.mean([post['sentiment'] for post in posts])
            
            return {
                "posts": posts,
                "average_sentiment": avg_sentiment
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit sentiment: {str(e)}")
            return {"posts": [], "average_sentiment": 0.0}

    def _calculate_overall_sentiment(self, news: Dict, twitter: Dict, reddit: Dict) -> Dict:
        """Calculate overall sentiment score."""
        try:
            # Weight different sources
            weights = {
                "news": 0.4,
                "twitter": 0.3,
                "reddit": 0.3
            }
            
            # Calculate weighted average
            overall_score = (
                news["average_sentiment"] * weights["news"] +
                twitter["average_sentiment"] * weights["twitter"] +
                reddit["average_sentiment"] * weights["reddit"]
            )
            
            # Determine sentiment category
            if overall_score > 0.2:
                category = "Bullish"
            elif overall_score < -0.2:
                category = "Bearish"
            else:
                category = "Neutral"
            
            return {
                "score": overall_score,
                "category": category,
                "confidence": min(abs(overall_score) * 2, 1.0)  # Scale to 0-1
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating overall sentiment: {str(e)}")
            return {"score": 0.0, "category": "Neutral", "confidence": 0.0}

    def _get_from_cache(self, symbol: str) -> Optional[Dict]:
        """Get data from cache if available and not expired."""
        cache_file = self.cache_dir / f"{symbol}_sentiment.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    cache_time = datetime.fromisoformat(data['timestamp'])
                    
                    if datetime.now() - cache_time < self.cache_ttl:
                        return data['data']
            except Exception as e:
                self.logger.error(f"Error reading cache for {symbol}: {str(e)}")
        
        return None

    def _save_to_cache(self, symbol: str, data: Dict):
        """Save data to cache."""
        cache_file = self.cache_dir / f"{symbol}_sentiment.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f)
        except Exception as e:
            self.logger.error(f"Error saving cache for {symbol}: {str(e)}")

    def _get_mock_data(self) -> Dict:
        """Generate mock data for development purposes."""
        return {
            "news": {
                "articles": [
                    {
                        "title": "Company Reports Strong Earnings",
                        "summary": "The company reported better than expected earnings...",
                        "title_sentiment": 0.5,
                        "summary_sentiment": 0.6,
                        "date": datetime.now().isoformat(),
                        "source": "Financial Times"
                    }
                ],
                "average_sentiment": 0.55
            },
            "twitter": {
                "tweets": [
                    {
                        "text": "Great earnings report from $SYMBOL!",
                        "sentiment": 0.7,
                        "date": datetime.now().isoformat(),
                        "retweets": 100,
                        "likes": 500
                    }
                ],
                "average_sentiment": 0.7
            },
            "reddit": {
                "posts": [
                    {
                        "title": "Why I'm bullish on SYMBOL",
                        "text": "Detailed analysis of the company...",
                        "sentiment": 0.8,
                        "date": datetime.now().isoformat(),
                        "upvotes": 1000,
                        "subreddit": "stocks"
                    }
                ],
                "average_sentiment": 0.8
            },
            "overall": {
                "score": 0.65,
                "category": "Bullish",
                "confidence": 0.8
            }
        }

    def analyze(self, symbol, days=30):
        """
        Analyze sentiment for a stock based on news and social media
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to analyze
            
        Returns:
            dict: Sentiment analysis results
        """
        try:
            # In a real implementation, this would:
            # 1. Fetch news articles and social media posts about the stock
            # 2. Analyze sentiment using NLP models
            # 3. Return structured results
            
            # For now, generate mock data
            return self._get_mock_sentiment_analysis(symbol, days)
        except Exception as e:
            logger.error(f"Error in sentiment analysis for {symbol}: {str(e)}")
            return self._get_mock_sentiment_analysis(symbol, days)
    
    def _get_mock_sentiment_analysis(self, symbol, days):
        """Generate mock sentiment analysis data for development"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate mock sentiment data for each day
        dates = []
        sentiment_scores = []
        news_count = []
        social_count = []
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            
            # Generate sentiment score between -1 and 1
            sentiment_scores.append(random.uniform(-0.8, 0.8))
            
            # Generate mock counts
            news_count.append(random.randint(5, 50))
            social_count.append(random.randint(50, 500))
            
            current_date += timedelta(days=1)
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # Determine sentiment label
        if avg_sentiment > 0.3:
            sentiment_label = "Very Positive"
        elif avg_sentiment > 0.1:
            sentiment_label = "Positive"
        elif avg_sentiment > -0.1:
            sentiment_label = "Neutral"
        elif avg_sentiment > -0.3:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Very Negative"
        
        # Generate mock news articles
        news_articles = []
        for i in range(5):  # Top 5 news articles
            sentiment = random.uniform(-1, 1)
            if sentiment > 0.2:
                sentiment_class = "positive"
            elif sentiment < -0.2:
                sentiment_class = "negative"
            else:
                sentiment_class = "neutral"
                
            days_ago = random.randint(0, days-1)
            article_date = (end_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            news_articles.append({
                'title': f"Mock news title about {symbol} #{i+1}",
                'source': random.choice(['Financial Times', 'Bloomberg', 'CNBC', 'Reuters', 'Economic Times']),
                'date': article_date,
                'url': f"https://example.com/news/{i}",
                'sentiment': sentiment,
                'sentiment_class': sentiment_class
            })
        
        # Generate mock social media posts
        social_posts = []
        for i in range(5):  # Top 5 social media posts
            sentiment = random.uniform(-1, 1)
            if sentiment > 0.2:
                sentiment_class = "positive"
            elif sentiment < -0.2:
                sentiment_class = "negative"
            else:
                sentiment_class = "neutral"
                
            hours_ago = random.randint(1, 24 * days)
            post_date = (end_date - timedelta(hours=hours_ago)).strftime('%Y-%m-%d %H:%M')
            
            social_posts.append({
                'content': f"Mock social media post about {symbol} #{i+1}",
                'platform': random.choice(['Twitter', 'Reddit', 'StockTwits']),
                'user': f"user{random.randint(1000, 9999)}",
                'date': post_date,
                'likes': random.randint(5, 500),
                'sentiment': sentiment,
                'sentiment_class': sentiment_class
            })
        
        # Generate overall analysis
        if avg_sentiment > 0.3:
            analysis = [
                f"Overall sentiment for {symbol} is very positive over the past {days} days.",
                "News coverage has been consistently favorable, highlighting strong performance.",
                "Social media discussion shows high investor confidence."
            ]
        elif avg_sentiment > 0.1:
            analysis = [
                f"Overall sentiment for {symbol} is positive over the past {days} days.",
                "News coverage has been generally favorable with some mixed reports.",
                "Social media discussion leans positive with growing interest."
            ]
        elif avg_sentiment > -0.1:
            analysis = [
                f"Overall sentiment for {symbol} is neutral over the past {days} days.",
                "News coverage has been mixed with balanced positive and negative aspects.",
                "Social media discussion shows diverse opinions without strong consensus."
            ]
        elif avg_sentiment > -0.3:
            analysis = [
                f"Overall sentiment for {symbol} is negative over the past {days} days.",
                "News coverage has raised some concerns about performance or outlook.",
                "Social media discussion trends toward caution and skepticism."
            ]
        else:
            analysis = [
                f"Overall sentiment for {symbol} is very negative over the past {days} days.",
                "News coverage has highlighted significant concerns or problems.",
                "Social media discussion shows strong pessimism among investors."
            ]
        
        return {
            'average_sentiment': avg_sentiment,
            'sentiment_label': sentiment_label,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'daily_data': {
                'dates': dates,
                'sentiment_scores': sentiment_scores,
                'news_count': news_count,
                'social_count': social_count
            },
            'news_articles': news_articles,
            'social_posts': social_posts,
            'analysis': analysis
        }
    
    def analyze_news_sentiment(self, symbol, days_back=30):
        """Analyze sentiment from news articles for a company."""
        try:
            # Load preprocessed news data
            file_path = self.processed_data_dir / 'news_social' / f"{symbol}_news_processed.csv"
            if not file_path.exists():
                logger.error(f"Processed news data file not found for {symbol}")
                return None
                
            df = pd.read_csv(file_path)
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Filter for recent news within days_back
                cutoff_date = datetime.now() - timedelta(days=days_back)
                df = df[df['Date'] >= cutoff_date]
            
            if df.empty:
                logger.warning(f"No recent news data found for {symbol}")
                return None
            
            # Analyze sentiment for each article
            if self.model_loaded:
                # Use FinBERT for sentiment analysis
                df['Sentiment_Score'] = df.apply(lambda row: self._analyze_text_sentiment(row['Clean_Content']), axis=1)
                
                # Classify sentiment
                df['Sentiment'] = df['Sentiment_Score'].apply(self._classify_sentiment)
            else:
                # Fallback to simple lexicon-based approach
                df['Sentiment_Score'] = df['Clean_Content'].apply(self._lexicon_sentiment)
                df['Sentiment'] = df['Sentiment_Score'].apply(self._classify_sentiment)
            
            # Aggregate sentiment analysis
            sentiment_counts = df['Sentiment'].value_counts().to_dict()
            total_articles = len(df)
            sentiment_distribution = {k: v / total_articles for k, v in sentiment_counts.items()}
            
            avg_sentiment = df['Sentiment_Score'].mean()
            
            # Analyze sentiment trend (if we have dates)
            sentiment_trend = None
            if 'Date' in df.columns:
                df = df.sort_values('Date')
                df['Rolling_Sentiment'] = df['Sentiment_Score'].rolling(window=min(5, len(df)), min_periods=1).mean()
                
                if len(df) >= 3:
                    first_half = df.iloc[:(len(df)//2)]['Sentiment_Score'].mean()
                    second_half = df.iloc[(len(df)//2):]['Sentiment_Score'].mean()
                    
                    if second_half > first_half + 0.1:
                        sentiment_trend = "Improving"
                    elif second_half < first_half - 0.1:
                        sentiment_trend = "Deteriorating"
                    else:
                        sentiment_trend = "Stable"
            
            # Get most positive and negative headlines
            if not df.empty:
                most_positive = df.loc[df['Sentiment_Score'].idxmax()]
                most_negative = df.loc[df['Sentiment_Score'].idxmin()]
                
                positive_headline = most_positive['Headline'] if 'Headline' in most_positive else None
                negative_headline = most_negative['Headline'] if 'Headline' in most_negative else None
            else:
                positive_headline = None
                negative_headline = None
            
            # Generate insights based on sentiment analysis
            insights = self._generate_sentiment_insights(
                avg_sentiment, 
                sentiment_distribution, 
                sentiment_trend, 
                positive_headline, 
                negative_headline
            )
            
            # Combine all analyses
            sentiment_analysis = {
                'Symbol': symbol,
                'Analysis_Date': datetime.now().strftime('%Y-%m-%d'),
                'Articles_Analyzed': total_articles,
                'Average_Sentiment': avg_sentiment,
                'Sentiment_Distribution': sentiment_distribution,
                'Sentiment_Trend': sentiment_trend,
                'Most_Positive_Headline': positive_headline,
                'Most_Negative_Headline': negative_headline,
                'Insights': insights
            }
            
            # Save analysis
            output_path = self.processed_data_dir / 'analysis' / f"{symbol}_sentiment_analysis.json"
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(sentiment_analysis, f, indent=4)
                
            logger.info(f"Sentiment analysis completed for {symbol} based on {total_articles} articles")
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"Error performing sentiment analysis for {symbol}: {str(e)}")
            return None
    
    def _analyze_text_sentiment(self, text):
        """Analyze sentiment of a piece of text using FinBERT."""
        try:
            if not text or pd.isna(text) or text == "":
                return 0  # Neutral for empty text
                
            # Truncate text if too long (FinBERT has token limits)
            max_length = 512
            if len(text) > max_length * 4:  # Approximate character to token ratio
                text = text[:max_length * 4]
            
            # Tokenize and get sentiment
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT classes: negative (0), neutral (1), positive (2)
            # Convert to a score between -1 and 1
            negative_prob = probabilities[0, 0].item()
            neutral_prob = probabilities[0, 1].item()
            positive_prob = probabilities[0, 2].item()
            
            # Calculate a weighted score (-1 to 1)
            score = positive_prob - negative_prob
            
            return score
            
        except Exception as e:
            logger.error(f"Error in FinBERT sentiment analysis: {str(e)}")
            return 0  # Return neutral on error
    
    def _lexicon_sentiment(self, text):
        """Simple lexicon-based sentiment analysis as a fallback."""
        if not text or pd.isna(text) or text == "":
            return 0  # Neutral for empty text
            
        # Simple financial sentiment lexicon
        positive_words = [
            'up', 'rise', 'rising', 'rose', 'high', 'higher', 'highest', 'bull', 'bullish',
            'outperform', 'outperformed', 'outperforming', 'beat', 'beats', 'beating',
            'exceed', 'exceeds', 'exceeded', 'exceeding', 'expectations', 'strong', 'strength',
            'positive', 'profit', 'profitable', 'gain', 'gains', 'gained', 'growth',
            'growing', 'grew', 'expand', 'expands', 'expanded', 'expanding', 'dividend',
            'dividends', 'upgrade', 'upgraded', 'buy', 'buying', 'recommend', 'recommended'
        ]
        
        negative_words = [
            'down', 'fall', 'falling', 'fell', 'low', 'lower', 'lowest', 'bear', 'bearish',
            'underperform', 'underperformed', 'underperforming', 'miss', 'misses', 'missing',
            'missed', 'weak', 'weakness', 'negative', 'loss', 'losses', 'decline', 'declines',
            'declining', 'declined', 'shrink', 'shrinks', 'shrinking', 'shrank', 'cut', 'cuts',
            'cutting', 'downgrade', 'downgraded', 'sell', 'selling', 'avoid', 'avoided'
        ]
        
        # Convert to lowercase and tokenize naively
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Count sentiment words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate score between -1 and 1
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0  # Neutral if no sentiment words found
            
        score = (positive_count - negative_count) / total_count
        return score
    
    def _classify_sentiment(self, score):
        """Classify sentiment score into categories."""
        if score > 0.3:
            return 'Positive'
        elif score < -0.3:
            return 'Negative'
        else:
            return 'Neutral'
    
    def _generate_sentiment_insights(self, avg_sentiment, sentiment_distribution, sentiment_trend, positive_headline, negative_headline):
        """Generate insights based on sentiment analysis results."""
        insights = []
        
        # Overall sentiment insight
        if avg_sentiment > 0.5:
            insights.append("News sentiment is strongly positive, which often correlates with positive price movement.")
        elif avg_sentiment > 0.2:
            insights.append("News sentiment is moderately positive, suggesting a favorable outlook.")
        elif avg_sentiment < -0.5:
            insights.append("News sentiment is strongly negative, which often correlates with negative price movement.")
        elif avg_sentiment < -0.2:
            insights.append("News sentiment is moderately negative, suggesting potential concerns.")
        else:
            insights.append("News sentiment is relatively neutral, without strong positive or negative bias.")
        
        # Sentiment distribution insight
        if sentiment_distribution:
            pos_pct = sentiment_distribution.get('Positive', 0) * 100
            neg_pct = sentiment_distribution.get('Negative', 0) * 100
            
            if pos_pct > 60:
                insights.append(f"A high percentage ({pos_pct:.1f}%) of news articles are positive, indicating strong bullish sentiment.")
            elif neg_pct > 60:
                insights.append(f"A high percentage ({neg_pct:.1f}%) of news articles are negative, indicating strong bearish sentiment.")
            elif pos_pct > neg_pct + 20:
                insights.append(f"Positive news ({pos_pct:.1f}%) significantly outweighs negative news ({neg_pct:.1f}%), suggesting positive bias.")
            elif neg_pct > pos_pct + 20:
                insights.append(f"Negative news ({neg_pct:.1f}%) significantly outweighs positive news ({pos_pct:.1f}%), suggesting negative bias.")
        
        # Sentiment trend insight
        if sentiment_trend:
            if sentiment_trend == "Improving":
                insights.append("News sentiment is improving over time, which may signal a positive shift in market perception.")
            elif sentiment_trend == "Deteriorating":
                insights.append("News sentiment is deteriorating over time, which may signal increasing concerns.")
            else:  # "Stable"
                insights.append("News sentiment has remained stable over the analyzed period.")
        
        # Headline insights
        if positive_headline:
            insights.append(f"Most positive headline: \"{positive_headline}\"")
        if negative_headline:
            insights.append(f"Most negative headline: \"{negative_headline}\"")
        
        return insights
    
    def analyze_social_sentiment(self, symbol, days_back=7):
        """Analyze sentiment from social media posts for a company."""
        # Similar implementation as analyze_news_sentiment but for social media data
        # ...
        return None 