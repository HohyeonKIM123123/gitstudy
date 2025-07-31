# Customer Email Assistant

AI-powered customer service email assistant that automatically classifies incoming emails and generates appropriate replies.

## Features

- 📧 Gmail integration for email reading
- 🤖 AI-powered email classification
- ✍️ Automatic reply generation
- 📊 Dashboard for email management
- 🎯 Priority-based email sorting
- 📝 Manual reply editing and approval

## Tech Stack

### Frontend

- React 18
- Tailwind CSS
- Axios for API calls
- React Router for navigation

### Backend

- FastAPI (Python)
- Gmail API
- OpenAI API
- MongoDB/Firebase for data storage

## Setup

### 1. Install Dependencies

```bash
npm run install-all
```

### 2. Environment Configuration

Copy `.env` and fill in your API keys:

- Gmail API credentials
- OpenAI API key
- Database connection string

### 3. Gmail API Setup

1. Go to Google Cloud Console
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs

### 4. Database Setup

Choose either MongoDB or Firebase and update the configuration in `.env`

### 5. Run the Application

```bash
npm run dev
```

This will start both the React frontend (port 3000) and FastAPI backend (port 8000).

## Project Structure

```
customer-email-assistant/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/         # Main pages
│   │   ├── api/           # API calls
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── tailwind.config.js
├── server/                # FastAPI backend
│   ├── gmail_reader.py    # Gmail API integration
│   ├── reply_generator.py # AI reply generation
│   ├── classifier.py      # Email classification
│   ├── main.py           # API server
│   └── db.py             # Database operations
├── .env                  # Environment variables
└── package.json         # Root configuration
```

## API Endpoints

- `GET /emails` - Fetch emails from Gmail
- `POST /classify` - Classify email type
- `POST /generate-reply` - Generate AI reply
- `PUT /emails/{id}` - Update email status
- `POST /send-reply` - Send reply via Gmail

## Email Classification Types

- 🔴 Urgent - Requires immediate attention
- 🟡 Support - Technical support requests
- 🟢 General - General inquiries
- 🔵 Sales - Sales-related emails
- ⚪ Spam - Spam or irrelevant emails
