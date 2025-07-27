class Account:
    def __init__(self, account_id: str, initial_deposit: float) -> None:
        """Initialize an account with a unique ID and initial deposit."""
        self.account_id = account_id
        self.initial_deposit = initial_deposit
        self.balance = initial_deposit
        self.holdings = {}  # {symbol: quantity}
        self.transactions = []  # List of transaction records

    def deposit_funds(self, amount: float) -> bool:
        """Deposit funds into the account."""
        if amount <= 0:
            return False
        self.balance += amount
        self.transactions.append({
            'action': 'deposit',
            'amount': amount,
            'balance': self.balance
        })
        return True

    def withdraw_funds(self, amount: float) -> bool:
        """Withdraw funds from the account."""
        if amount <= 0 or amount > self.balance:
            return False
        self.balance -= amount
        self.transactions.append({
            'action': 'withdraw',
            'amount': amount,
            'balance': self.balance
        })
        return True

    def buy_shares(self, symbol: str, quantity: int) -> bool:
        """Buy shares of a given symbol."""
        if quantity <= 0:
            return False
        
        price = get_share_price(symbol)
        total_cost = price * quantity
        
        if total_cost > self.balance:
            return False
        
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append({
            'action': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total_cost
        })
        return True

    def sell_shares(self, symbol: str, quantity: int) -> bool:
        """Sell shares of a given symbol."""
        if quantity <= 0:
            return False
        
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            return False
        
        price = get_share_price(symbol)
        total_proceeds = price * quantity
        
        self.balance += total_proceeds
        self.holdings[symbol] -= quantity
        
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        
        self.transactions.append({
            'action': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total_proceeds
        })
        return True

    def calculate_portfolio_value(self) -> float:
        """Calculate the total value of shares in the portfolio."""
        total_value = 0.0
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def report_holdings(self) -> dict:
        """Return current holdings."""
        return self.holdings.copy()

    def calculate_profit_loss(self) -> float:
        """Calculate profit/loss from initial deposit."""
        current_total = self.balance + self.calculate_portfolio_value()
        return current_total - self.initial_deposit

    def list_transactions(self) -> list:
        """Return list of all transactions."""
        return self.transactions.copy()


def get_share_price(symbol: str) -> float:
    """Get the current price of a share. Test implementation with fixed prices."""
    prices = {
        'AAPL': 150.0,
        'TSLA': 700.0,
        'GOOGL': 2800.0
    }
    return prices.get(symbol, 0.0)