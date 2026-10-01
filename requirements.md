A simple account management system for a trading simulation platform.

- Users can create an account, deposit funds, and withdraw funds.
- Users can record that they have bought or sold shares, with a quantity.
- The system calculates the total value of a user's portfolio, and the profit or loss
  against their initial deposit.
- The system can report a user's holdings at any point in time.
- The system can report a user's profit or loss at any point in time.
- The system can list every transaction a user has made over time.
- The system prevents a withdrawal that would leave a negative balance, a purchase the user
  cannot afford, and a sale of shares the user does not hold.
- The system has access to `get_share_price(symbol)` returning the current share price.
  Include a test implementation returning fixed prices for AAPL, TSLA and GOOGL.
