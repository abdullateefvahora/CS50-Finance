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
    user_id = session["user_id"]
    portfolio = {}
    
    # get list of each stock and number of shares for user
    stocks = db.execute("SELECT symbol, SUM(shares) FROM indexes WHERE id=:id GROUP BY symbol", id=user_id)
    
    # assign dict value of shares to each stock 
    for row in stocks:
        symbol, shares = row["symbol"], row["SUM(shares)"]
        if shares > 0:
            portfolio[symbol] = portfolio.setdefault(symbol, 0) + shares
    
    # get user cash value and declare total value  
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id=user_id)[0]["cash"]
    total = cash
    
    # assign name, price, etc to each symbol in dict
    for symbol, shares in portfolio.items():
        quote = lookup(symbol)
        name, price = quote["name"], quote["price"]
        stock_total = price * shares
        total += stock_total
        portfolio[symbol] = (name, shares, usd(price), usd(stock_total))
    
    return render_template("index.html", portfolio=portfolio, cash=usd(cash), total=usd(total))
    

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    user_id = session["user_id"]
    
    # when form submitted
    if request.method == "POST":
        
        # lookup info of stock
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        quote = lookup(symbol)
        
        # if symbol is blank or invalid
        if quote == None:
            return apology("Invalid stock symbol", 400)
        
        # if shares is blank or invalid
        try:
            shares = float(shares)
        except ValueError:
            return apology("Provide valid number of shares", 400)
        if not shares > 0:
            return apology("Must provide valid number of shares", 400)
        
        # can user afford 
        cost = shares * quote["price"]
        cash = db.execute("SELECT cash FROM users WHERE id=:id", id=user_id)[0]["cash"]
        if cost > cash:
            return apology("Insufficient Funds", 400)
        else:
            cash = cash - cost
            db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash, id=user_id) 
        
        # update info onto indexes table
        db.execute("INSERT INTO indexes (id, symbol, shares, price, type) VALUES(?, ?, ?, ?, ?)",
                   user_id, symbol, shares, quote["price"], "buy")
        
        # redirect to home page    
        return redirect("/")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")
    

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    
    orders = {}
    
    # get user's stock list ordered by recent transaction
    stocks = db.execute("SELECT * FROM indexes WHERE id=:id ORDER BY time DESC", id=user_id)
    
    # assign dict value of symbol, shares and price to each timestamp 
    for row in stocks:
        symbol, shares, price, time = row["symbol"], row["shares"], row["price"], row["time"]
        orders[time] = (symbol, shares, usd(price))

    return render_template("history.html", orders=orders)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

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
    # when form submitted
    if request.method == "POST":
        
        # lookup info of stock
        quote = lookup(request.form.get("symbol"))
        
        # if symbol is blank or invalid
        if quote == None:
            return apology("Invalid stock symbol", 400)
            
        return render_template("quoted.html", quote=quote)
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        password = request.form.get("password")
        if len(password) < 8:
            return apology("password must be 8 characters long", 400)
        
        # make sure password is confirmed
        elif not request.form.get("confirmation") or not request.form.get("confirmation") == request.form.get("password"):
            return apology("passwords do not match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        
        if len(rows) != 0:
            return apology("username already in use", 400)

        # insert new user into user table 
        username = request.form.get("username")
        password = request.form.get("password")
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username,
                   generate_password_hash(password, method='pbkdf2:sha256', salt_length=16))
        
        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
    

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    
    if request.method == "POST":
        
        # lookup info of stock
        shares = request.form.get("shares")
        symbol = request.form.get("symbol")
        
        if not symbol:
            return apology("select symbol", 400)
        elif not shares:
            return apology("add no of shares", 400)
        
        # if shares is blank or invalid
        try:
            shares = float(shares)
        except ValueError:
            return apology("Provide valid number of shares", 400)
        if not shares > 0:
            return apology("Must provide valid number of shares")
        shares_owned = db.execute("SELECT SUM(shares) FROM indexes WHERE id=:id AND symbol=:symbol GROUP BY symbol",
                                  id=user_id, symbol=symbol)[0]["SUM(shares)"]
        if not 0 < shares <= shares_owned:
            return apology("Number of shares is invalid or not owned", 400)
        
        # can user afford 
        quote = lookup(symbol)
        cost = shares * quote["price"]
        cash = db.execute("SELECT cash FROM users WHERE id=:id", id=user_id)[0]["cash"]
        cash = cash + cost
        db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash, id=user_id) 
        
        # update info onto indexes table
        shares = shares * -1
        db.execute("INSERT INTO indexes (id, symbol, shares, price, type) VALUES(?, ?, ?, ?, ?)",
                   user_id, symbol, shares, quote["price"], "sell")
        
        # redirect to home page    
        return redirect("/")    
    
    # when form is submitted
    if request.method == "GET":
        
        # create list of all stocks user owns
        stocks = []
        stock_info = db.execute("SELECT symbol, SUM(shares) FROM indexes WHERE id=:id GROUP BY symbol", id=user_id)
        
        for row in stock_info:
            symbol, shares = row["symbol"], row["SUM(shares)"]
            if shares > 0:
                stocks.append(symbol)
        num_stocks = len(stocks)
        
        return render_template("sell.html", stocks=stocks, num_stocks=num_stocks)
    

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
