# AI News Summarizer

## Project Overview

The AI News Summarizer is a Python-based application that fetches AI-related newsletter emails from Gmail (using the email address 'mitchcreatessubs@gmail.com to subscribe to various newsletters), summarizes their content using OpenAI's GPT-3.5 model, and displays the summarized content on my blogging website in an automated process. The goal of this project is to provide concise summaries of AI newsletters to help users stay updated with the latest developments in the field but also for myself to have one place to read the latest news as the amount of sources and news in general can be very overwhelming.

## Project Goals

1. **Fetch AI Newsletters**: Retrieve AI-related newsletter emails from Gmail.
2. **Have OpenAI make a blogpost out of all provided newsletters**: Use OpenAI's GPT-3.5 model to summarize the content of the emails.
3. **Have an automated process of publishing the post on the blogging website**: Display the blogpost on the website.

## Project Structure

- `main.py`: The main entry point of the application.
- `fetch_emails.py`: Contains functions to fetch and summarize emails.
- `gmail_auth.py`: Handles Gmail authentication.
- `summarizer.py`: Contains functions to summarize email content.
- `database/`: Contains database models and operations.
- `entities/`: Contains data transfer objects (DTOs) and entity definitions.
- `enums/`: Contains enumerations used in the project.
- `.env`: Environment variables file (should be listed in `.gitignore`).
- `.gitignore`: Specifies files and directories to be ignored by Git.
- `README.md`: Project overview and documentation.

## Setup and Usage

### Prerequisites

- Python 3.8 or higher
- A Gmail account with API access
- OpenAI API key

### Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/ai-news-summarizer.git
   cd ai-news-summarizer
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. **Install the required packages:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the root directory of the project and add the following variables:

   ```env
   GMAIL_CLIENT_ID=your_gmail_client_id
   GMAIL_CLIENT_SECRET=your_gmail_client_secret
   GMAIL_REFRESH_TOKEN=your_gmail_refresh_token
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=sqlite:///your_database.db
   ```

### Usage

1. **Fetch and summarize emails:**

   Run the main script to fetch AI-related newsletters from Gmail, summarize their content using OpenAI's GPT-3.5 model, and publish the summarized content on the blogging website:

   ```sh
   python main.py
   ```

### Current State of the Project

- The project is able to fetch AI-related newsletters from Gmail.
- The content of the emails is summarized using OpenAI's GPT-3.5 model.
- The summarized content is published on the blogging website in an automated process.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.


## Rewinding the creaton of the markdownfile in the blog repository

rm C:\Users\michi\Projects\blogtest\content\post\weekly-ai-news-1.md
git add C:\Users\michi\Projects\blogtest\content\post\weekly-ai-news-1.md
git commit -m "Remove test blog post file"
git push origin develop

## Automatically update the requirements.txt file with the following command
pipreqs . --force