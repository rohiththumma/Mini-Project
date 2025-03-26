# Mini-Project
CV & JOB DESCRIPTION ANALYSIS DASHBOARD USING GEN AI INTEGRATION OF API
# CV/Resume Analysis Dashboard 🚀

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A smart tool to analyze resumes against job descriptions using AI-powered insights. Features relevance scoring, skill gap analysis, course recommendations, and automated cover letter generation.

![Dashboard Demo](assets/demo-screenshot.png) *(Add your screenshot after uploading)*

## ✨ Key Features
- **Resume Parsing**: Supports PDF, DOCX, DOC, and TXT formats
- **AI-Powered Analysis**: 
  - Relevance score visualization (gauge chart)
  - Missing skills/keywords identification
  - Personalized improvement recommendations
- **Course Suggestions**: Curated learning resources from top platforms
- **Cover Letter Generator**: Auto-generated tailored cover letters
- **Interactive GUI**: User-friendly dashboard with visual analytics

## 🛠️ Technologies Used
- Python 3.8+
- Google Gemini API (AI backbone)
- Tkinter (GUI)
- Matplotlib (Data visualization)
- pandas, NumPy (Data processing)
- pdfplumber/docx2txt (Document parsing)

## ⚡ Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key ([Get from Google AI Studio](https://aistudio.google.com/))

### Installation
```bash
# Clone repository
git clone https://github.com/<your-username>/cv-analysis-dashboard.git
cd cv-analysis-dashboard

# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "GEMINI_API_KEY=your_api_key_here" > .env

1.Paste job description in the text area
2.Upload your resume (PDF/DOCX/DOC/TXT)
3.Click "Submit" for instant analysis
4.View recommendations and generate cover letters
