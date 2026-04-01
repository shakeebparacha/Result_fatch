# Streamlit Version - Student Results Dashboard

This is a complete **Streamlit** version of your student results application, separate from the Flask app.

## 📁 Project Structure

```
streamlit_app/
├── app.py                 # Main Streamlit application
├── scraper.py             # Selenium scraper for BISE Lahore results
├── requirements.txt       # Python dependencies
├── Student_Results.csv    # Scraped results (auto-generated)
└── README.md             # This file
```

## 🚀 Installation & Setup

### 1. Install Dependencies

```bash
cd streamlit_app
pip install -r requirements.txt
```

### 2. Run the Application Locally

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📊 Features

### 1. **Dashboard Tab (📈)**
   - Total students metric
   - Pass/Fail statistics
   - Average and highest marks
   - Student performance scatter plot
   - Pass/Fail distribution (pie chart)
   - Marks distribution histogram
   - Top 5 and Bottom 5 performers

### 2. **Scrape Results Tab (🔍)**
   - Input multiple roll numbers (comma-separated)
   - Select exam year, course, and exam type
   - Automated Selenium scraper with CAPTCHA solving
   - Real-time progress tracking
   - Auto-saves results to CSV

### 3. **Data Analysis Tab (📋)**
   - Statistical summary (mean, median, std deviation)
   - Full student data table with filters
   - Filter by status (Pass/Fail)
   - Filter by marks range
   - Download filtered data as CSV
   - Key insights and statistics

## 🔧 Technologies Used

- **Streamlit** - Interactive web framework
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive visualizations
- **Selenium** - Web automation and scraping
- **ddddocr** - AI-based CAPTCHA solving
- **NumPy, Matplotlib, Seaborn, SciPy** - Data analysis libraries

## 📝 Usage Example

1. **For Scraping:**
   - Go to "🔍 Scrape Results" tab
   - Enter roll numbers: `503097,506578`
   - Select year and course
   - Click "🚀 Start Scraping"
   - Wait for results to be saved

2. **For Dashboard:**
   - Go to "📈 Dashboard" tab
   - View all visualizations and statistics
   - See top/bottom performers

3. **For Analysis:**
   - Go to "📋 Data Analysis" tab
   - Apply filters
   - Download filtered results

## 🌐 Deploy to Streamlit Cloud

1. Push this folder to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io)
3. Click "New App"
4. Paste your GitHub repo URL
5. Select this folder (`streamlit_app`)
6. Click "Deploy"

> **Note:** Scraper may not work on Streamlit Cloud due to Selenium browser limitations. It's best used for local testing.

## 📊 Data Format

The `Student_Results.csv` file has this structure:

```csv
Roll_Number,Name,Father_Name,Total_Marks,Status
503097,KHADIJA IQBAL,MUHAMMAD IQBAL,PASS 518,PASS
506578,ZOHA,MUHAMMAD ABRAR UL HAQ SHAKIR,PASS 488,PASS
```

## ⚠️ Notes

- The scraper requires Chrome or Edge to be installed
- CAPTCHA solving requires good internet connection
- For cloud deployment, use headless mode

## 💡 Tips

- Run locally for best experience with scraping
- Use filters in Data Analysis tab to find specific students
- Download your data regularly for backup
- Visualizations are interactive - hover over charts for details

---

Built with ❤️ using Streamlit
