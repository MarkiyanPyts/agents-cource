import gradio as gr
from accounts import Account, get_share_price

# Create a single user account
account = None

def create_account(initial_deposit):
    global account
    try:
        deposit = float(initial_deposit)
        if deposit <= 0:
            return "Error: Initial deposit must be positive", "", "", "", ""
        account = Account("user001", deposit)
        balance, holdings, portfolio, transactions = get_account_info()
        return f"Account created with initial deposit: ${deposit:.2f}", balance, holdings, portfolio, transactions
    except ValueError:
        return "Error: Invalid deposit amount", "", "", "", ""

def deposit(amount):
    if account is None:
        return "Error: Please create an account first", "", "", "", ""
    try:
        amt = float(amount)
        if account.deposit_funds(amt):
            balance, holdings, portfolio, transactions = get_account_info()
            return f"Successfully deposited ${amt:.2f}", balance, holdings, portfolio, transactions
        else:
            balance, holdings, portfolio, transactions = get_account_info()
            return "Error: Invalid deposit amount", balance, holdings, portfolio, transactions
    except ValueError:
        balance, holdings, portfolio, transactions = get_account_info()
        return "Error: Invalid amount", balance, holdings, portfolio, transactions

def withdraw(amount):
    if account is None:
        return "Error: Please create an account first", "", "", "", ""
    try:
        amt = float(amount)
        if account.withdraw_funds(amt):
            balance, holdings, portfolio, transactions = get_account_info()
            return f"Successfully withdrew ${amt:.2f}", balance, holdings, portfolio, transactions
        else:
            balance, holdings, portfolio, transactions = get_account_info()
            return "Error: Insufficient funds or invalid amount", balance, holdings, portfolio, transactions
    except ValueError:
        balance, holdings, portfolio, transactions = get_account_info()
        return "Error: Invalid amount", balance, holdings, portfolio, transactions

def buy_shares(symbol, quantity):
    if account is None:
        return "Error: Please create an account first", "", "", "", ""
    try:
        qty = int(quantity)
        symbol = symbol.upper()
        if symbol not in ['AAPL', 'TSLA', 'GOOGL']:
            balance, holdings, portfolio, transactions = get_account_info()
            return "Error: Invalid symbol. Available: AAPL, TSLA, GOOGL", balance, holdings, portfolio, transactions
        if account.buy_shares(symbol, qty):
            price = get_share_price(symbol)
            balance, holdings, portfolio, transactions = get_account_info()
            return f"Successfully bought {qty} shares of {symbol} at ${price:.2f}/share", balance, holdings, portfolio, transactions
        else:
            balance, holdings, portfolio, transactions = get_account_info()
            return "Error: Insufficient funds or invalid quantity", balance, holdings, portfolio, transactions
    except ValueError:
        balance, holdings, portfolio, transactions = get_account_info()
        return "Error: Invalid quantity", balance, holdings, portfolio, transactions

def sell_shares(symbol, quantity):
    if account is None:
        return "Error: Please create an account first", "", "", "", ""
    try:
        qty = int(quantity)
        symbol = symbol.upper()
        if account.sell_shares(symbol, qty):
            price = get_share_price(symbol)
            balance, holdings, portfolio, transactions = get_account_info()
            return f"Successfully sold {qty} shares of {symbol} at ${price:.2f}/share", balance, holdings, portfolio, transactions
        else:
            balance, holdings, portfolio, transactions = get_account_info()
            return "Error: Insufficient shares or invalid quantity", balance, holdings, portfolio, transactions
    except ValueError:
        balance, holdings, portfolio, transactions = get_account_info()
        return "Error: Invalid quantity", balance, holdings, portfolio, transactions

def get_account_info():
    if account is None:
        return "", "", "", ""
    
    # Balance
    balance_str = f"${account.balance:.2f}"
    
    # Holdings
    holdings = account.report_holdings()
    holdings_str = ""
    if holdings:
        for symbol, qty in holdings.items():
            price = get_share_price(symbol)
            value = price * qty
            holdings_str += f"{symbol}: {qty} shares @ ${price:.2f} = ${value:.2f}\n"
    else:
        holdings_str = "No holdings"
    
    # Portfolio value and P/L
    portfolio_value = account.calculate_portfolio_value()
    total_value = account.balance + portfolio_value
    profit_loss = account.calculate_profit_loss()
    portfolio_str = f"Cash Balance: ${account.balance:.2f}\n"
    portfolio_str += f"Portfolio Value: ${portfolio_value:.2f}\n"
    portfolio_str += f"Total Value: ${total_value:.2f}\n"
    portfolio_str += f"Profit/Loss: ${profit_loss:.2f} ({profit_loss/account.initial_deposit*100:.1f}%)"
    
    # Transactions
    transactions = account.list_transactions()
    trans_str = ""
    for trans in transactions[-10:]:  # Show last 10 transactions
        if trans['action'] == 'deposit':
            trans_str += f"Deposit: ${trans['amount']:.2f}\n"
        elif trans['action'] == 'withdraw':
            trans_str += f"Withdraw: ${trans['amount']:.2f}\n"
        elif trans['action'] == 'buy':
            trans_str += f"Buy: {trans['quantity']} {trans['symbol']} @ ${trans['price']:.2f} = ${trans['total']:.2f}\n"
        elif trans['action'] == 'sell':
            trans_str += f"Sell: {trans['quantity']} {trans['symbol']} @ ${trans['price']:.2f} = ${trans['total']:.2f}\n"
    
    return balance_str, holdings_str, portfolio_str, trans_str

def get_price_info():
    return "AAPL: $150.00 | TSLA: $700.00 | GOOGL: $2,800.00"

# Create Gradio interface
with gr.Blocks(title="Trading Simulation Account") as demo:
    gr.Markdown("# Trading Simulation Account Management")
    gr.Markdown("### Current Stock Prices")
    gr.Markdown(get_price_info())
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Account Setup")
            initial_deposit_input = gr.Number(label="Initial Deposit ($)", value=10000)
            create_btn = gr.Button("Create Account")
            
            gr.Markdown("### Transactions")
            with gr.Tab("Deposit/Withdraw"):
                deposit_amount = gr.Number(label="Amount ($)")
                deposit_btn = gr.Button("Deposit")
                withdraw_btn = gr.Button("Withdraw")
            
            with gr.Tab("Buy/Sell Shares"):
                trade_symbol = gr.Textbox(label="Symbol (AAPL, TSLA, GOOGL)")
                trade_quantity = gr.Number(label="Quantity", precision=0)
                buy_btn = gr.Button("Buy Shares")
                sell_btn = gr.Button("Sell Shares")
            
            status_output = gr.Textbox(label="Status", lines=2)
        
        with gr.Column():
            gr.Markdown("### Account Information")
            balance_output = gr.Textbox(label="Cash Balance", interactive=False)
            holdings_output = gr.Textbox(label="Holdings", lines=5, interactive=False)
            portfolio_output = gr.Textbox(label="Portfolio Summary", lines=5, interactive=False)
            transactions_output = gr.Textbox(label="Recent Transactions", lines=10, interactive=False)
    
    # Event handlers
    def update_with_status(func):
        def wrapper(*args):
            result = func(*args)
            if isinstance(result, tuple):
                return result
            else:
                return result, get_account_info()
        return wrapper
    
    create_btn.click(
        create_account,
        inputs=[initial_deposit_input],
        outputs=[status_output, balance_output, holdings_output, portfolio_output, transactions_output]
    )
    
    deposit_btn.click(
        deposit,
        inputs=[deposit_amount],
        outputs=[status_output, balance_output, holdings_output, portfolio_output, transactions_output]
    )
    
    withdraw_btn.click(
        withdraw,
        inputs=[deposit_amount],
        outputs=[status_output, balance_output, holdings_output, portfolio_output, transactions_output]
    )
    
    buy_btn.click(
        buy_shares,
        inputs=[trade_symbol, trade_quantity],
        outputs=[status_output, balance_output, holdings_output, portfolio_output, transactions_output]
    )
    
    sell_btn.click(
        sell_shares,
        inputs=[trade_symbol, trade_quantity],
        outputs=[status_output, balance_output, holdings_output, portfolio_output, transactions_output]
    )

if __name__ == "__main__":
    demo.launch()