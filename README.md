# 💇🏽‍♀️ HairHQ – AI Hair Information & Styling Assistant

HairHQ is a web-based application that educates users about hair care and provides helpful, personalized style tips using AI-powered responses.

---

## Overview

HairHQ helps users better understand their hair type, texture, and styling options through clear explanations and general guidance. It is designed as an educational tool and does not replace professional advice.

---

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn  
- **Frontend:** HTML, CSS, JavaScript  
- **AI:** OpenAI API  

---

## Project Structure

```
hairhq/
├── backend/
│   ├── main.py
│   ├── info_men.json
│   └── info_women.json
│
├── frontend/
│   ├── css/
│   │   └── style.css
│   │
│   ├── images/
│   │
│   ├── men/
│   │   ├── hairchat.html
│   │   ├── hairinfo.html
│   │   ├── hairplan.html
│   │   └── hairprofile.html
│   │
│   └── women/
│       ├── hairchat.html
│       ├── hairinfo.html
│       ├── hairplan.html
│       └── hairprofile.html
│
├── .gitignore
└── README.md
```



---

## Setup Instructions

All setup steps — including **beginner-friendly OpenAI API key instructions** — are documented in the project Wiki:

👉 **[Go to the HairHQ Setup Guide (Wiki)](../../wiki)**

---

## Notes

- API keys are not included in this repository.
- Each user must create their own OpenAI API key.
- Local environment files (such as `.env` and virtual environments) are excluded from version control.

