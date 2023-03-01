# Mock-Stock-Trading-Project

## Description: 
Mock Stock Trading is a web app that allows users to manage a portfolio of stocks (similar to a practice trading account). 

## Features: 
 User credential validation is performed before allowing access to the web app and users can create new accounts or change their password as needed. An SQL database stores user login information (username and password hash) as well as each user's portfolio. Individual transactions are also stored in the SQLite3 database to allow for a history of each buy and sell performed by each user. This web app uses API calls to IEX in order to obtain real-time stock prices for determining the price for each buy and sell operation.  

## How to use:
1. Create an account with IEX and obtain your API key to add to your environment
2. Once added, initialize flask and open the index.html file

## Technologies: 
Bootstrap UI, Flask back-end, and SQLite3 database

## License:
MIT License
