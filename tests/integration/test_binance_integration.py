"""
Integration tests for Binance client

Tests the complete Binance integration including:
- Connection and authentication
- Order placement and management
- Market data retrieval
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Import the Binance client
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from exchanges.binanceClient.binanceClient import Binance
from market.order import Order, TradeRequest


class TestBinanceConnection:
    """Test Binance connection and initialization"""
    
    @pytest.fixture
    def binance_config(self):
        """Provide test configuration"""
        return {
            'config': 'config/binance.yml',
            'candle_interval': 300,
            'backfill': {
                'enabled': True,
                'period': 7
            }
        }
    
    @patch('exchanges.binanceClient.binanceClient.Client')
    @patch('exchanges.binanceClient.binanceClient.readConf')
    def test_binance_initialization(self, mock_readConf, mock_client, binance_config):
        """Test Binance client initialization"""
        # Mock configuration
        mock_readConf.return_value = {
            'exchange': {
                'apiKey': 'test_key',
                'apiSecret': 'test_secret',
                'test_mode': True,
                'products': [{'BTCUSDT': {'id': 'BTC-USD'}}],
                'backfill_enabled': True,
                'backfill_period': 7,
                'backfill_interval': '5m'
            }
        }
        
        # Mock Binance client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_exchange_info.return_value = {
            'serverTime': 1234567890000,
            'symbols': [
                {
                    'symbol': 'BTCUSDT',
                    'baseAsset': 'BTC',
                    'quoteAsset': 'USDT'
                }
            ]
        }
        
        # Initialize Binance
        binance = Binance(binance_config)
        
        # Assertions
        assert binance is not None
        assert binance.name == "binanceClient"
        assert len(binance.binance_products) > 0


class TestBinanceTrading:
    """Test Binance trading operations"""
    
    @pytest.fixture
    def mock_binance(self):
        """Create a mock Binance instance"""
        with patch('exchanges.binanceClient.binanceClient.Client'):
            with patch('exchanges.binanceClient.binanceClient.readConf') as mock_conf:
                mock_conf.return_value = {
                    'exchange': {
                        'apiKey': 'test_key',
                        'apiSecret': 'test_secret',
                        'test_mode': True,
                        'products': [{'BTCUSDT': {'id': 'BTC-USD'}}],
                        'backfill_enabled': False
                    }
                }
                config = {
                    'config': 'config/binance.yml',
                    'candle_interval': 300,
                    'backfill': {'enabled': False, 'period': 7}
                }
                binance = Binance(config)
                binance.binance_products = [{
                    'id': 'BTC-USD',
                    'symbol': 'BTCUSDT',
                    'baseAsset': 'BTC',
                    'quoteAsset': 'USDT'
                }]
                return binance
    
    def test_buy_order(self, mock_binance):
        """Test placing a buy order"""
        # Mock product
        mock_product = Mock()
        mock_product.get_name.return_value = 'BTC-USD'
        
        # Mock trade request
        trade_req = Mock()
        trade_req.product = mock_product
        trade_req.size = 0.1
        trade_req.price = 50000
        trade_req.type = 'MARKET'
        
        # Mock auth client response
        mock_binance.auth_client = Mock()
        mock_binance.auth_client.order_market_buy.return_value = {
            'orderId': '12345',
            'status': 'FILLED',
            'executedQty': '0.1',
            'price': '50000',
            'transactTime': 1234567890
        }
        
        # Place buy order
        order = mock_binance.buy(trade_req)
        
        # Assertions
        assert order is not None
        assert order.id == '12345'
        assert order.side == 'buy'
        assert order.status == 'filled'
    
    def test_sell_order(self, mock_binance):
        """Test placing a sell order"""
        # Mock product
        mock_product = Mock()
        mock_product.get_name.return_value = 'BTC-USD'
        
        # Mock trade request
        trade_req = Mock()
        trade_req.product = mock_product
        trade_req.size = 0.1
        trade_req.price = 51000
        trade_req.type = 'MARKET'
        
        # Mock auth client response
        mock_binance.auth_client = Mock()
        mock_binance.auth_client.order_market_sell.return_value = {
            'orderId': '12346',
            'status': 'FILLED',
            'executedQty': '0.1',
            'price': '51000',
            'transactTime': 1234567891
        }
        
        # Place sell order
        order = mock_binance.sell(trade_req)
        
        # Assertions
        assert order is not None
        assert order.id == '12346'
        assert order.side == 'sell'
        assert order.status == 'filled'
    
    def test_cancel_order(self, mock_binance):
        """Test canceling an order"""
        # Mock auth client response
        mock_binance.auth_client = Mock()
        mock_binance.auth_client.cancel_order.return_value = {
            'orderId': '12345',
            'status': 'CANCELED'
        }
        
        # Cancel order
        result = mock_binance.cancel_order('BTC-USD', '12345')
        
        # Assertions
        assert result is True
    
    def test_get_order(self, mock_binance):
        """Test getting order status"""
        # Mock auth client response
        mock_binance.auth_client = Mock()
        mock_binance.auth_client.get_order.return_value = {
            'orderId': '12345',
            'status': 'FILLED',
            'type': 'MARKET',
            'side': 'BUY',
            'origQty': '0.1',
            'executedQty': '0.1',
            'price': '50000',
            'time': 1234567890,
            'updateTime': 1234567891
        }
        
        # Get order
        order = mock_binance.get_order('BTC-USD', '12345')
        
        # Assertions
        assert order is not None
        assert order.id == '12345'
        assert order.status == 'filled'


class TestBinanceMarketData:
    """Test Binance market data operations"""
    
    @pytest.fixture
    def mock_binance(self):
        """Create a mock Binance instance"""
        with patch('exchanges.binanceClient.binanceClient.Client'):
            with patch('exchanges.binanceClient.binanceClient.readConf') as mock_conf:
                mock_conf.return_value = {
                    'exchange': {
                        'apiKey': 'test_key',
                        'apiSecret': 'test_secret',
                        'products': [{'BTCUSDT': {'id': 'BTC-USD'}}],
                        'backfill_enabled': False
                    }
                }
                config = {
                    'config': 'config/binance.yml',
                    'candle_interval': 300,
                    'backfill': {'enabled': False, 'period': 7}
                }
                binance = Binance(config)
                binance.binance_products = [{
                    'id': 'BTC-USD',
                    'symbol': 'BTCUSDT'
                }]
                return binance
    
    def test_get_ticker(self, mock_binance):
        """Test getting ticker data"""
        # Mock public client response
        mock_binance.public_client = Mock()
        mock_binance.public_client.get_ticker.return_value = {
            'symbol': 'BTCUSDT',
            'lastPrice': '50000',
            'volume': '1000'
        }
        
        # Get ticker
        ticker = mock_binance.get_ticker('BTC-USD')
        
        # Assertions
        assert ticker is not None
        assert ticker['symbol'] == 'BTCUSDT'
    
    def test_get_order_book(self, mock_binance):
        """Test getting order book"""
        # Mock public client response
        mock_binance.public_client = Mock()
        mock_binance.public_client.get_order_book.return_value = {
            'bids': [['50000', '1.0']],
            'asks': [['50100', '1.0']]
        }
        
        # Get order book
        order_book = mock_binance.get_order_book_depth('BTC-USD', 100)
        
        # Assertions
        assert order_book is not None
        assert 'bids' in order_book
        assert 'asks' in order_book


@pytest.mark.integration
class TestBinanceLiveIntegration:
    """
    Live integration tests (requires actual Binance testnet credentials)
    Run with: pytest -m integration
    """
    
    @pytest.mark.skip(reason="Requires live Binance testnet credentials")
    def test_live_connection(self):
        """Test live connection to Binance testnet"""
        # This would test actual connection to Binance testnet
        pass
    
    @pytest.mark.skip(reason="Requires live Binance testnet credentials")
    def test_live_market_data(self):
        """Test retrieving live market data"""
        # This would test actual market data retrieval
        pass
