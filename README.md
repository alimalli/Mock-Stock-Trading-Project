# Mock-Stock-Trading-Project
Mock Stock Trading web app that allows users to manage a portfolio of stocks (similar to a practice trading account). 
This web app uses API calls to IEX in order to obtain real-time stock prices. It is designed with Bootstrap UI, Flask back-end, and SQLite3 database.
User credential validation is performed before allowing access to the web app and users can create new accounts or change their password as needed.
An SQL database stores user login information (username and password hash) as well as each user's portfolio.
Individual transactions are alse stored in the SQL database to allow for a history of each buy and sell performed by each user.
