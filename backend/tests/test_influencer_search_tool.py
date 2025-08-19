"""
Comprehensive tests for the influencer_search_tool.

Tests cover normal operation, error handling, parameter validation,
and API response parsing with mocked HTTP requests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add the source directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent.influencer_search.prompts import influencer_search_tool


class TestInfluencerSearchTool:
    """Test suite for influencer_search_tool functionality."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'INFLUENCER_API_BASE_URL': 'http://test-api.com',
            'INFLUENCER_API_UID': 'test-uid-123'
        }):
            yield

    @pytest.fixture
    def sample_api_response(self):
        """Sample API response for testing."""
        return {
            "errorNum": 0,
            "errorMsg": "",
            "retDataList": [
                {
                    "nickName": "BeautyGuru123",
                    "followers": 250000,
                    "country": "US",
                    "interactiveRate": 0.045,
                    "estimateVideoViews": 50000,
                    "noxScore": 85.5
                },
                {
                    "nickName": "MakeupMaster",
                    "followers": 180000,
                    "country": "UK",
                    "interactiveRate": 0.038,
                    "estimateVideoViews": 35000,
                    "noxScore": 78.2
                },
                {
                    "nickName": "SkincarePro",
                    "followers": 320000,
                    "country": "CA",
                    "interactiveRate": 0.052,
                    "estimateVideoViews": 65000,
                    "noxScore": 92.1
                }
            ]
        }

    @pytest.fixture  
    def empty_api_response(self):
        """Empty API response for testing."""
        return {
            "errorNum": 0,
            "errorMsg": "",
            "retDataList": []
        }

    @pytest.fixture
    def error_api_response(self):
        """Error API response for testing."""
        return {
            "errorNum": 1,
            "errorMsg": "Invalid request parameters"
        }

    @pytest.mark.asyncio
    async def test_basic_functionality(self, mock_env_vars, sample_api_response):
        """Test basic tool functionality with successful API response."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the async context manager
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['beauty', 'makeup'],
                'platform': 'youtube',
                'min_followers': 100000,
                'max_followers': 500000,
                'limit': 10
            })

            # Verify the result contains expected information
            assert "Found 3 youtube influencers" in result
            assert "BeautyGuru123" in result
            assert "MakeupMaster" in result
            assert "SkincarePro" in result
            assert "Followers: 250,000" in result
            assert "Engagement: 4.50%" in result

    @pytest.mark.asyncio
    async def test_keyword_formatting(self, mock_env_vars, sample_api_response):
        """Test that keywords are properly formatted with ,5, delimiter."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            await influencer_search_tool.ainvoke({
                'keywords': ['beauty', 'makeup', 'skincare'],
                'platform': 'youtube'
            })

            # Verify the API was called with properly formatted keywords
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['searchWords'] == 'beauty,5,makeup,5,skincare,5'

    @pytest.mark.asyncio
    async def test_platform_validation(self, mock_env_vars):
        """Test platform parameter validation."""
        # Test invalid platform
        result = await influencer_search_tool.ainvoke({
            'keywords': ['test'],
            'platform': 'invalid_platform'
        })
        assert "Unsupported platform: invalid_platform" in result

        # Test valid platforms
        valid_platforms = ['youtube', 'instagram', 'tiktok', 'YouTube', 'INSTAGRAM', 'TikTok']
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'errorNum': 0, 'retDataList': []})
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            for platform in valid_platforms:
                result = await influencer_search_tool.ainvoke({
                    'keywords': ['test'],
                    'platform': platform
                })
                assert "Unsupported platform" not in result

    @pytest.mark.asyncio
    async def test_limit_parameter(self, mock_env_vars, sample_api_response):
        """Test limit parameter functionality."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            # Test default limit (200)
            await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['pageSize'] == 200

            # Test custom limit within bounds
            await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube',
                'limit': 50
            })
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['pageSize'] == 50

            # Test limit exceeding maximum (should be capped at 200)
            await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube',
                'limit': 300
            })
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['pageSize'] == 200

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_env_vars, empty_api_response):
        """Test handling of empty API results."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=empty_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['nonexistent'],
                'platform': 'youtube'
            })

            assert "No youtube influencers found for 'nonexistent'" in result

    @pytest.mark.asyncio
    async def test_api_error_response(self, mock_env_vars, error_api_response):
        """Test handling of API error responses."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=error_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })

            assert "No results found" in result

    @pytest.mark.asyncio
    async def test_http_error_status(self, mock_env_vars):
        """Test handling of HTTP error status codes."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })

            assert "API error: 500" in result

    @pytest.mark.asyncio
    async def test_network_exception(self, mock_env_vars):
        """Test handling of network exceptions."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network connection failed")

            result = await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })

            assert "Search failed: Network connection failed" in result

    @pytest.mark.asyncio
    async def test_url_construction(self, mock_env_vars, sample_api_response):
        """Test proper URL construction for different platforms."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            # Test YouTube URL
            await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })
            call_args = mock_get.call_args
            assert call_args[0][0] == 'http://test-api.com/ws/youtube/star/search'

            # Test Instagram URL
            await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'instagram'
            })
            call_args = mock_get.call_args
            assert call_args[0][0] == 'http://test-api.com/ws/instagram/star/search'

            # Test TikTok URL
            await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'tiktok'
            })
            call_args = mock_get.call_args
            assert call_args[0][0] == 'http://test-api.com/ws/tiktok/star/search'

    @pytest.mark.asyncio
    async def test_headers_and_params(self, mock_env_vars, sample_api_response):
        """Test that proper headers and parameters are sent."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            await influencer_search_tool.ainvoke({
                'keywords': ['beauty', 'fashion'],
                'platform': 'youtube',
                'min_followers': 50000,
                'max_followers': 500000,
                'countries': 'US,UK,CA',
                'language': 'en',
                'limit': 100
            })

            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            params = call_args[1]['params']

            # Check headers
            assert headers['uid'] == 'test-uid-123'

            # Check parameters
            assert params['followerGte'] == 50000
            assert params['followerLte'] == 500000
            assert params['country'] == 'US,UK,CA'
            assert params['language'] == 'en'
            assert params['pageNum'] == 1
            assert params['pageSize'] == 100
            assert params['searchWords'] == 'beauty,5,fashion,5'

    @pytest.mark.asyncio
    async def test_result_formatting(self, mock_env_vars, sample_api_response):
        """Test that results are properly formatted."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['beauty'],
                'platform': 'youtube'
            })

            # Check that all influencers are included
            assert "1. BeautyGuru123" in result
            assert "2. MakeupMaster" in result
            assert "3. SkincarePro" in result

            # Check formatting of details
            assert "Platform: youtube" in result
            assert "Followers: 250,000" in result
            assert "Location: US" in result
            assert "Engagement: 4.50%" in result
            assert "Average Views: 50,000" in result
            assert "Nox Score: 85.50" in result

    @pytest.mark.asyncio
    async def test_missing_data_handling(self, mock_env_vars):
        """Test handling of missing or null data in API response."""
        incomplete_response = {
            "errorNum": 0,
            "retDataList": [
                {
                    "nickName": "TestUser",
                    "followers": None,
                    "country": None,
                    "interactiveRate": None,
                    "estimateVideoViews": None,
                    "noxScore": None
                }
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=incomplete_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })

            # Should handle missing data gracefully
            assert "TestUser" in result
            assert "Followers: 0" in result
            assert "Location: Unknown" in result
            assert "Engagement: 0.00%" in result
            assert "Average Views: 0" in result
            assert "Nox Score: 0.00" in result

    @pytest.mark.asyncio
    async def test_zero_values_preservation(self, mock_env_vars):
        """Test that valid 0 values are preserved (not replaced by defaults)."""
        zero_values_response = {
            "errorNum": 0,
            "retDataList": [
                {
                    "nickName": "ZeroFollowersUser",
                    "followers": 0,  # Valid 0 should be preserved
                    "country": "US",
                    "interactiveRate": 0.0,  # Valid 0.0 should be preserved
                    "estimateVideoViews": 0,  # Valid 0 should be preserved
                    "noxScore": 0.0  # Valid 0.0 should be preserved
                }
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=zero_values_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await influencer_search_tool.ainvoke({
                'keywords': ['test'],
                'platform': 'youtube'
            })

            # Verify that 0 values are preserved, not replaced
            assert "ZeroFollowersUser" in result
            assert "Followers: 0" in result  # Should show 0, not default
            assert "Engagement: 0.00%" in result  # Should show 0.00%, not default
            assert "Average Views: 0" in result  # Should show 0, not default
            assert "Nox Score: 0.00" in result  # Should show 0.00, not default

    @pytest.mark.asyncio
    async def test_default_parameters(self, mock_env_vars, sample_api_response):
        """Test that default parameters are applied correctly."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_api_response)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            # Test with minimal parameters
            await influencer_search_tool.ainvoke({
                'keywords': ['test']
            })

            call_args = mock_get.call_args
            params = call_args[1]['params']

            # Check default values
            assert params['followerGte'] == 50000
            assert params['followerLte'] == 1000000
            assert params['country'] == 'US,UK'
            assert params['language'] == 'en'
            assert params['pageSize'] == 200

            # Check URL uses default platform
            assert call_args[0][0].endswith('/ws/youtube/star/search')


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v"])