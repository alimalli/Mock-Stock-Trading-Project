import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Get stocks information from tables
    userinfo = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    username = userinfo[0]["username"]
    portfolio = db.execute("SELECT * FROM stockownership WHERE username = ?", username)

    # Initialize a blank stockinfo dictionary to fill with stock info
    stockinfo = {}

    # Iterate over rows in the portfolio list and store the info in the stock info dictionary
    for stock in portfolio:
        symbol, shares = stock["symbol"], stock["shares"]
        stockinfo[symbol] = stockinfo.setdefault(symbol, 0) + shares

    # Initialize total variable to sum up the value of shares owned
    total = 0

    # Update stockinfo dictionary with name, number of shares owned, current price, and current value of holding for each stock
    for symbol, shares in stockinfo.items():
        result = lookup(symbol)
        name, price = result["name"], result["price"]
        stockvalue = shares * price
        total += stockvalue
        stockinfo[symbol] = (name, shares, usd(price), usd(stockvalue))

    # Cash on hand and total cash value of portfolio
    usercash = userinfo[0]["cash"]
    total += usercash

    return render_template("index.html", stockinfo=stockinfo, cash=usd(usercash), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock symbol field is not blank
        if not request.form.get("symbol"):
            return apology("Stock symbol cannot be blank.", 400)

        # Ensure shares field is not blank and is a positive integer
        shares = request.form.get("shares")
        if not shares or not shares.isdigit():
            return apology("Share amount must be a positive integer.", 400)

        # Ensure stock symbol is valid
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Stock symbol not valid.", 400)

        # Calculate the price of the puchase
        cashneeded = stock['price'] * float(shares)

        # Check is user has enough cash in account
        userinfo = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = userinfo[0]["username"]
        usercash = userinfo[0]["cash"]

        # Update records in table to record purchase
        if usercash > cashneeded:
            cashafterbuy = usercash - cashneeded
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cashafterbuy, session["user_id"])
            db.execute("INSERT INTO transactions (username, type, symbol, shares, price) VALUES (?, ?, ? ,?, ?)",
                       username, 'BUY', stock['symbol'], shares, stock['price'])

            # Check if stock not already owned and insert new entry
            sharesownedforbuy = db.execute(
                "SELECT * FROM stockownership WHERE username = ? AND symbol = ?", username, stock['symbol'])
            if len(sharesownedforbuy) != 1:
                db.execute("INSERT INTO stockownership (username, symbol, shares) VALUES (? ,?, ?)",
                           username, stock['symbol'], shares)

            # Check if stock already owned and update entry to new amount
            else:
                updatedsharecount = int(sharesownedforbuy[0]["shares"]) + int(shares)
                db.execute("UPDATE stockownership SET shares = ? WHERE username = ? AND symbol = ?",
                           updatedsharecount, username, stock['symbol'])

        # If user does not have enough cash in account
        else:
            return apology("Not enough cash at hand to complete purchase", 400)

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Get stocks information from tables
    userinfo = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    username = userinfo[0]["username"]

    usertransactions = db.execute("SELECT * FROM transactions WHERE username = ?", username)

    for transaction in usertransactions:
        transaction["price"] = usd(transaction["price"])

    return render_template("history.html", usertransactions=usertransactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock symbol is not blank
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        # Run lookup function on stock ticker provided by user
        symbol = request.form.get("symbol")
        stockquote = lookup(symbol)

        if not stockquote:
            return apology("stock symbol not valid", 400)

        # return to user the current quote for the stock query
        return render_template("quoted.html", stockquote=stockquote)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Check if username already exists
        if len(rows) == 1:
            return apology("username already exists", 400)

        # add user to database if registration is valid
        username = request.form.get("username")
        password_hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, password_hash)

        # Return user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Change password"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure current password was submitted
        if not request.form.get("currentpassword"):
            return apology("must provide current password", 400)

        # Ensure current password submitted is the correct current password
        userinfo = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = userinfo[0]["username"]
        if not check_password_hash(userinfo[0]["hash"], request.form.get("currentpassword")):
            return apology("Incorrect current password", 400)

        # Ensure new password is not blank
        elif not request.form.get("newpassword") or not request.form.get("newpasswordconfirmation"):
            return apology("must provide new password", 400)

        # Ensure new password matches confirmation password
        elif request.form.get("newpassword") != request.form.get("newpasswordconfirmation"):
            return apology("new passwords do not match", 400)

        # Change user password if fields are valid
        new_password_hash = generate_password_hash(request.form.get("newpassword"))
        db.execute("UPDATE users SET hash = ? WHERE username = ?", new_password_hash, username)

        # Return user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepassword.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock symbol selection is not blank
        if not request.form.get("symbol"):
            return apology("No stock symbol must be selected.", 400)

        # Ensure shares field is not blank and is a positive integer
        shares = request.form.get("shares")
        if not shares or not shares.isdigit():
            return apology("Share amount must be a positive integer.", 400)

        # Check stock price
        stock = lookup(request.form.get("symbol"))

        # Calculate the gain from sale
        cashgain = stock['price'] * float(shares)

        # Get stocks information from tables
        userinfo = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = userinfo[0]["username"]
        usercash = userinfo[0]["cash"]
        portfolio = db.execute("SELECT * FROM stockownership WHERE username = ?", username)

        # Check if user owns that many shares
        sharesownedforsell = db.execute(
            "SELECT shares FROM stockownership WHERE username = ? AND symbol = ?", username, stock['symbol'])
        if int(sharesownedforsell[0]["shares"]) >= int(shares):

            # Update records in table to record purchase
            cashaftersell = usercash + cashgain
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cashaftersell, session["user_id"])
            db.execute("INSERT INTO transactions (username, type, symbol, shares, price) VALUES (?, ?, ? ,?, ?)",
                       username, 'SELL', stock['symbol'], shares, stock['price'])

            # Update stock ownership in stock ownership table
            updatedsharecount = int(sharesownedforsell[0]["shares"]) - int(shares)
            if updatedsharecount > 0:
                db.execute("UPDATE stockownership SET shares = ? WHERE username = ? AND symbol = ?",
                           updatedsharecount, username, stock['symbol'])

            # Remove row from table if 0 shares is the resulting number of shares
            else:
                db.execute("DELETE FROM stockownership WHERE username = ? AND symbol = ?", username, stock['symbol'])

            return redirect("/")

        else:
            return apology("You do not own enough shares to complete this transaction", 400)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Get Stocks info from tables
        userinfo = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        username = userinfo[0]["username"]
        portfolio = db.execute("SELECT * FROM stockownership WHERE username = ?", username)

        # Initialize a blank symbolsavailable list to fill with stock info
        symbolsavailable = []

        # Iterate over rows in the portfolio list and store the info in the stock info dictionary
        for i in range(len(portfolio)):
            tempsymbol = portfolio[i]["symbol"]
            symbolsavailable.append(tempsymbol)

        return render_template("sell.html", symbolsavailable=symbolsavailable)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
