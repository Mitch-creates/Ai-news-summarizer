# AI News Summarizer

## Project Overview

The AI News Summarizer is a Python-based application that fetches AI-related newsletter emails from Gmail(Used a mail address 'mitchcreatessubs@gmail.com to subscribe to various newsletters), summarizes their content using OpenAI's GPT-3.5 model, and displays the summarized content on my blogging website in an automated process. The goal of this project is to provide concise summaries of AI newsletters to help users stay updated with the latest developments in the field but also for myself to have one place to read the latest news as the amount of sources and news in general can be very overwhelming.

## Project Goals

1. **Fetch AI Newsletters**: Retrieve AI-related newsletter emails from Gmail.
2. **Have OpenAI make a blogpost out of all provided newsletters**: Use OpenAI's GPT-3.5 model to summarize the content of the emails.
3. **Have an automated process of publishing the post on the blogging website**: Display the blogpost on the website.

1. **Fetch the AI newsletters using the Gmail api**
2. **Filter the newsletters from other emails**
3. **Structure them and send them in one request to OpenAI**
4. **Have OpenAI create an engaging but precise blogpost out of the provided newsletters**
5. **Automate the process of publishing the blogpost to the blogging website**

## Project Structure

- `main.py`: The main entry point of the application.
- `fetch_emails.py`: Contains functions to fetch and summarize emails.
- `gmail_auth.py`: Handles Gmail authentication.
- `summarizer.py`: Contains functions to summarize email content.
- `.env`: Environment variables file (should be listed in `.gitignore`).
- `.gitignore`: Specifies files and directories to be ignored by Git.
- `README.md`: Project overview and documentation.

## Setup and Usage

