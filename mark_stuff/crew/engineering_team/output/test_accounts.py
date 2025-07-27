import unittest
from accounts import Account, get_share_price


class TestAccount(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.account = Account("TEST123", 10000.0)
    
    def test_init(self):
        """Test account initialization."""
        account = Account("ACC001", 5000.0)
        self.assertEqual(account.account_id, "ACC001")
        self.assertEqual(account.initial_deposit, 5000.0)
        self.assertEqual(account.balance, 5000.0)
        self.assertEqual(account.holdings, {})
        self.assertEqual(account.transactions, [])
    
    def test_deposit_funds_valid(self):
        """Test depositing valid amounts."""
        # Test normal deposit
        result = self.account.deposit_funds(1000.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 11000.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0]['action'], 'deposit')
        self.assertEqual(self.account.transactions[0]['amount'], 1000.0)
        self.assertEqual(self.account.transactions[0]['balance'], 11000.0)
        
        # Test another deposit
        result = self.account.deposit_funds(500.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 11500.0)
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_deposit_funds_invalid(self):
        """Test depositing invalid amounts."""
        # Test zero deposit
        result = self.account.deposit_funds(0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(len(self.account.transactions), 0)
        
        # Test negative deposit
        result = self.account.deposit_funds(-100)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(len(self.account.transactions), 0)
    
    def test_withdraw_funds_valid(self):
        """Test withdrawing valid amounts."""
        # Test normal withdrawal
        result = self.account.withdraw_funds(2000.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 8000.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0]['action'], 'withdraw')
        self.assertEqual(self.account.transactions[0]['amount'], 2000.0)
        self.assertEqual(self.account.transactions[0]['balance'], 8000.0)
        
        # Test withdrawing entire balance
        result = self.account.withdraw_funds(8000.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_withdraw_funds_invalid(self):
        """Test withdrawing invalid amounts."""
        # Test zero withdrawal
        result = self.account.withdraw_funds(0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        
        # Test negative withdrawal
        result = self.account.withdraw_funds(-100)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        
        # Test withdrawal more than balance
        result = self.account.withdraw_funds(15000.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(len(self.account.transactions), 0)
    
    def test_buy_shares_valid(self):
        """Test buying shares with valid parameters."""
        # Buy AAPL shares
        result = self.account.buy_shares('AAPL', 10)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 8500.0)  # 10000 - (150 * 10)
        self.assertEqual(self.account.holdings['AAPL'], 10)
        self.assertEqual(len(self.account.transactions), 1)
        
        transaction = self.account.transactions[0]
        self.assertEqual(transaction['action'], 'buy')
        self.assertEqual(transaction['symbol'], 'AAPL')
        self.assertEqual(transaction['quantity'], 10)
        self.assertEqual(transaction['price'], 150.0)
        self.assertEqual(transaction['total'], 1500.0)
        
        # Buy more AAPL shares
        result = self.account.buy_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings['AAPL'], 15)
        self.assertEqual(self.account.balance, 7750.0)
        
        # Buy TSLA shares
        result = self.account.buy_shares('TSLA', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings['TSLA'], 5)
        self.assertEqual(self.account.balance, 4250.0)  # 7750 - (700 * 5)
    
    def test_buy_shares_invalid(self):
        """Test buying shares with invalid parameters."""
        # Test zero quantity
        result = self.account.buy_shares('AAPL', 0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        
        # Test negative quantity
        result = self.account.buy_shares('AAPL', -5)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        
        # Test insufficient funds
        result = self.account.buy_shares('GOOGL', 5)  # 2800 * 5 = 14000 > 10000
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        
        # Test unknown symbol (price = 0)
        result = self.account.buy_shares('UNKNOWN', 100)
        self.assertTrue(result)  # Should succeed as cost is 0
        self.assertEqual(self.account.balance, 10000.0)
    
    def test_sell_shares_valid(self):
        """Test selling shares with valid parameters."""
        # First buy some shares
        self.account.buy_shares('AAPL', 10)
        self.account.buy_shares('TSLA', 5)
        
        # Sell some AAPL shares
        result = self.account.sell_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings['AAPL'], 5)
        self.assertEqual(self.account.balance, 5750.0)  # 4250 + (150 * 5)
        
        # Sell all remaining AAPL shares
        result = self.account.sell_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertNotIn('AAPL', self.account.holdings)
        self.assertEqual(self.account.balance, 6500.0)
        
        # Check transaction records
        sell_transactions = [t for t in self.account.transactions if t['action'] == 'sell']
        self.assertEqual(len(sell_transactions), 2)
    
    def test_sell_shares_invalid(self):
        """Test selling shares with invalid parameters."""
        # Buy some shares first
        self.account.buy_shares('AAPL', 10)
        
        # Test zero quantity
        result = self.account.sell_shares('AAPL', 0)
        self.assertFalse(result)
        
        # Test negative quantity
        result = self.account.sell_shares('AAPL', -5)
        self.assertFalse(result)
        
        # Test selling more than owned
        result = self.account.sell_shares('AAPL', 15)
        self.assertFalse(result)
        self.assertEqual(self.account.holdings['AAPL'], 10)
        
        # Test selling shares not owned
        result = self.account.sell_shares('TSLA', 1)
        self.assertFalse(result)
    
    def test_calculate_portfolio_value(self):
        """Test calculating portfolio value."""
        # Empty portfolio
        self.assertEqual(self.account.calculate_portfolio_value(), 0.0)
        
        # Buy some shares
        self.account.buy_shares('AAPL', 10)  # 10 * 150 = 1500
        self.assertEqual(self.account.calculate_portfolio_value(), 1500.0)
        
        # Buy more shares
        self.account.buy_shares('TSLA', 5)   # 5 * 700 = 3500
        self.account.buy_shares('GOOGL', 2)  # 2 * 2800 = 5600
        self.assertEqual(self.account.calculate_portfolio_value(), 10600.0)
        
        # Sell some shares
        self.account.sell_shares('AAPL', 5)  # Remaining: 5 * 150 = 750
        self.assertEqual(self.account.calculate_portfolio_value(), 9850.0)
    
    def test_report_holdings(self):
        """Test reporting holdings."""
        # Empty holdings
        holdings = self.account.report_holdings()
        self.assertEqual(holdings, {})
        
        # Add some holdings
        self.account.buy_shares('AAPL', 10)
        self.account.buy_shares('TSLA', 5)
        
        holdings = self.account.report_holdings()
        self.assertEqual(holdings, {'AAPL': 10, 'TSLA': 5})
        
        # Verify it's a copy, not reference
        holdings['AAPL'] = 999
        self.assertEqual(self.account.holdings['AAPL'], 10)
    
    def test_calculate_profit_loss(self):
        """Test calculating profit/loss."""
        # No transactions - should be 0
        self.assertEqual(self.account.calculate_profit_loss(), 0.0)
        
        # Buy shares - should show loss due to cash->shares conversion
        self.account.buy_shares('AAPL', 10)  # Spend 1500
        # Balance: 8500, Portfolio: 1500, Total: 10000
        self.assertEqual(self.account.calculate_profit_loss(), 0.0)
        
        # Deposit more funds - should show profit
        self.account.deposit_funds(5000.0)
        # Balance: 13500, Portfolio: 1500, Total: 15000, Initial: 10000
        self.assertEqual(self.account.calculate_profit_loss(), 5000.0)
        
        # Withdraw funds - profit should decrease
        self.account.withdraw_funds(3000.0)
        # Balance: 10500, Portfolio: 1500, Total: 12000, Initial: 10000
        self.assertEqual(self.account.calculate_profit_loss(), 2000.0)
    
    def test_list_transactions(self):
        """Test listing transactions."""
        # No transactions
        self.assertEqual(self.account.list_transactions(), [])
        
        # Add various transactions
        self.account.deposit_funds(1000.0)
        self.account.buy_shares('AAPL', 5)
        self.account.sell_shares('AAPL', 2)
        self.account.withdraw_funds(500.0)
        
        transactions = self.account.list_transactions()
        self.assertEqual(len(transactions), 4)
        self.assertEqual(transactions[0]['action'], 'deposit')
        self.assertEqual(transactions[1]['action'], 'buy')
        self.assertEqual(transactions[2]['action'], 'sell')
        self.assertEqual(transactions[3]['action'], 'withdraw')
        
        # Verify it's a copy, not reference
        transactions[0]['action'] = 'modified'
        self.assertEqual(self.account.transactions[0]['action'], 'deposit')
    
    def test_integration_scenario(self):
        """Test a complete trading scenario."""
        # Start with initial deposit of 10000
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.calculate_profit_loss(), 0.0)
        
        # Buy diversified portfolio
        self.account.buy_shares('AAPL', 20)   # 3000
        self.account.buy_shares('TSLA', 5)    # 3500
        self.account.buy_shares('GOOGL', 1)   # 2800
        
        # Check balance and portfolio
        self.assertEqual(self.account.balance, 700.0)
        self.assertEqual(self.account.calculate_portfolio_value(), 9300.0)
        self.assertEqual(self.account.calculate_profit_loss(), 0.0)
        
        # Sell some shares for profit
        self.account.sell_shares('AAPL', 10)  # Get 1500
        self.assertEqual(self.account.balance, 2200.0)
        
        # Add more funds
        self.account.deposit_funds(5000.0)
        self.assertEqual(self.account.balance, 7200.0)
        
        # Final profit/loss check
        # Balance: 7200, Portfolio: 7800 (AAPL:10*150 + TSLA:5*700 + GOOGL:1*2800)
        # Total: 15000, Initial: 10000
        self.assertEqual(self.account.calculate_profit_loss(), 5000.0)
        
        # Verify transaction count
        self.assertEqual(len(self.account.list_transactions()), 5)


class TestGetSharePrice(unittest.TestCase):
    def test_known_symbols(self):
        """Test getting prices for known symbols."""
        self.assertEqual(get_share_price('AAPL'), 150.0)
        self.assertEqual(get_share_price('TSLA'), 700.0)
        self.assertEqual(get_share_price('GOOGL'), 2800.0)
    
    def test_unknown_symbol(self):
        """Test getting price for unknown symbol."""
        self.assertEqual(get_share_price('UNKNOWN'), 0.0)
        self.assertEqual(get_share_price(''), 0.0)
        self.assertEqual(get_share_price('MSFT'), 0.0)


if __name__ == '__main__':
    unittest.main()