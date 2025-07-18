"""
Data models for Influencer Marketing Campaign.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Creator:
    """Influencer/Creator profile"""
    id: str
    username: str
    platform: str
    followers: int
    engagement_rate: float
    niche: str
    audience_demographics: Dict[str, Any]
    contact_info: str
    historical_performance: Dict[str, float]
    fraud_score: float
    match_score: float = 0.0


@dataclass
class Contract:
    """Contract details with influencer"""
    id: str
    creator_id: str
    terms: Dict[str, Any]
    compensation: float
    deliverables: List[str]
    timeline: Dict[str, datetime]
    status: str  # draft, negotiating, signed, completed
    discount_code: Optional[str] = None


@dataclass
class Script:
    """Content script for campaign"""
    id: str
    creator_id: str
    platform: str
    content: str
    brand_story: str
    compliance_status: str  # pending, approved, rejected
    version: int
    created_at: datetime


@dataclass
class PostLink:
    """Published post information"""
    id: str
    creator_id: str
    platform: str
    url: str
    published_at: datetime
    content_type: str  # post, story, reel, video
    status: str  # scheduled, published, boosted


@dataclass
class Metric:
    """Performance metrics"""
    post_id: str
    views: int
    likes: int
    shares: int
    comments: int
    engagement_rate: float
    cpm: float
    cpa: float
    roas: float
    timestamp: datetime


@dataclass
class Invoice:
    """Settlement invoice"""
    id: str
    creator_id: str
    amount: float
    currency: str
    status: str  # pending, paid, failed
    payment_method: str
    created_at: datetime
    paid_at: Optional[datetime] = None