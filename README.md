# 📈 CS50 Finance: Stock Portfolio Tracker

This web application is a virtual stock trading platform, created for Harvard's **CS50x: Introduction to Computer Science** course. It simulates a real-world stock trading environment where users can manage a portfolio with virtual cash.

The application is built using Python and the Flask web framework, demonstrating core concepts of web development, database management, and interaction with third-party APIs.

---
## Key Features

* **User Authentication:** Basic user registration and login system to ensure data separation.
* **Real-time Stock Quotes:** Fetch and display up-to-date stock prices using an external API.
* **Portfolio Management:** View a dynamic table of owned stocks, including the number of shares, current price, and total value.
* **Stock Trading:** A simple interface to "buy" and "sell" stocks, which updates the user's portfolio and cash balance accordingly.
* **Transaction History:** A dedicated page to review all past transactions (buys and sells).

---
## Tech Stack

* **Backend:** Python with the Flask framework.
* **Database:** SQLite for user data, portfolios, and transaction history.
* **Frontend:** HTML, CSS, and Jinja for templating.
* **API:** Integrates with the IEX Cloud API to fetch real-time stock data.

---
## 🎥 Video Demonstration

For a basic walkthrough of the website's front-end and features, **please watch the video included in this repository.**

---
## Usage

* Navigate to the homepage and register for a new account.
* Log in to access your personal dashboard, which starts with a default cash balance.
* Use the **Quote** page to look up the current price of any public stock.
* Use the **Buy** and **Sell** pages to manage your holdings.
* The homepage will always display your current portfolio and its total value.
