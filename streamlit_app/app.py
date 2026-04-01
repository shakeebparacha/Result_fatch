import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os
import sys

# Add parent directory to path to import scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper import scrape_bise_lahore_selenium

# Set page configuration
st.set_page_config(
    page_title="Student Results Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("📊 Student Results Dashboard")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("---")
    
    selected_tab = st.radio(
        "Select View:",
        ["📈 Dashboard", "🔍 Scrape Results", "📋 Data Analysis"],
        label_visibility="visible"
    )

# Load existing results
@st.cache_data
def load_results():
    try:
        df = pd.read_csv("../Student_Results.csv")
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status'])

# Process Total_Marks to extract numeric values
def process_marks(status_text):
    """Extract numeric marks from status text like 'PASS 518'"""
    try:
        parts = str(status_text).split()
        for part in parts:
            if part.isdigit():
                return int(part)
        return 0
    except:
        return 0

# ============ DASHBOARD TAB ============
if selected_tab == "📈 Dashboard":
    st.header("Student Performance Dashboard")
    st.markdown("---")
    
    df = load_results()
    
    if len(df) > 0:
        # Process marks
        df['Marks'] = df['Total_Marks'].apply(process_marks)
        df['Status'] = df['Total_Marks'].apply(lambda x: 'PASS' if 'PASS' in str(x) else 'FAIL')
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="Total Students",
                value=len(df),
                delta=None
            )
        with col2:
            passed = len(df[df['Status'] == 'PASS'])
            st.metric(
                label="Passed",
                value=passed,
                delta=f"{(passed/len(df)*100):.1f}%" if len(df) > 0 else "0%"
            )
        with col3:
            avg_marks = df['Marks'].mean()
            st.metric(
                label="Average Marks",
                value=f"{avg_marks:.1f}",
                delta=None
            )
        with col4:
            max_marks = df['Marks'].max()
            st.metric(
                label="Highest Marks",
                value=max_marks,
                delta=None
            )
        
        st.markdown("---")
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Student Performance Scatter Plot")
            scatter_fig = px.scatter(
                df,
                x='Roll_Number',
                y='Marks',
                color='Status',
                size='Marks',
                hover_data=['Name', 'Father_Name', 'Marks'],
                title="Roll Number vs Marks Distribution",
                color_discrete_map={'PASS': '#2ecc71', 'FAIL': '#e74c3c'},
                labels={'Roll_Number': 'Roll Number', 'Marks': 'Total Marks'}
            )
            scatter_fig.update_layout(height=500, hovermode='closest')
            st.plotly_chart(scatter_fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Pass/Fail Distribution")
            status_counts = df['Status'].value_counts()
            pie_fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color_discrete_map={'PASS': '#2ecc71', 'FAIL': '#e74c3c'},
                title="Pass vs Fail Statistics"
            )
            pie_fig.update_layout(height=500)
            st.plotly_chart(pie_fig, use_container_width=True)
        
        # Marks Distribution
        st.subheader("📊 Marks Distribution (Histogram)")
        hist_fig = px.histogram(
            df,
            x='Marks',
            nbins=20,
            color='Status',
            color_discrete_map={'PASS': '#2ecc71', 'FAIL': '#e74c3c'},
            title="Distribution of Student Marks",
            labels={'Marks': 'Total Marks', 'count': 'Number of Students'}
        )
        hist_fig.update_layout(height=400)
        st.plotly_chart(hist_fig, use_container_width=True)
        
        # Top Performers
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 5 Performers")
            top_5 = df.nlargest(5, 'Marks')[['Roll_Number', 'Name', 'Marks']]
            st.dataframe(top_5, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("⚠️ Lowest 5 Performers")
            bottom_5 = df.nsmallest(5, 'Marks')[['Roll_Number', 'Name', 'Marks']]
            st.dataframe(bottom_5, use_container_width=True, hide_index=True)
    else:
        st.warning("📌 No data available. Please scrape results first!")

# ============ SCRAPER TAB ============
elif selected_tab == "🔍 Scrape Results":
    st.header("Scrape BISE Lahore Results")
    st.markdown("---")
    
    st.info("🔔 **Note:** This tool uses Selenium to automate browser and scrape student results from BISE Lahore website.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        roll_numbers_input = st.text_area(
            "Enter Roll Numbers (comma-separated):",
            placeholder="Example: 503097,506578,506579",
            height=100
        )
    
    with col2:
        exam_year = st.selectbox("Select Exam Year:", ["2024", "2023", "2022", "2021"])
        course = st.selectbox("Select Course:", ["HSSC", "SSC"])
        exam_type = st.selectbox("Exam Type:", ["2", "1"])
    
    st.markdown("---")
    
    if st.button("🚀 Start Scraping", use_container_width=True, type="primary"):
        if roll_numbers_input.strip():
            roll_numbers = [x.strip() for x in roll_numbers_input.split(',')]
            
            st.warning(f"⏳ Scraping {len(roll_numbers)} roll number(s)... This may take a minute...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_list = []
            
            for idx, roll_no in enumerate(roll_numbers):
                try:
                    status_text.write(f"Scraping roll number: **{roll_no}**...")
                    result = scrape_bise_lahore_selenium(roll_no, course, exam_type, exam_year)
                    if result:
                        results_list.append(result)
                    progress_bar.progress((idx + 1) / len(roll_numbers))
                except Exception as e:
                    st.error(f"❌ Error scraping {roll_no}: {str(e)}")
            
            if results_list:
                # Create DataFrame from results
                results_df = pd.DataFrame(results_list)
                
                # Save to CSV
                results_df.to_csv("../Student_Results.csv", index=False)
                
                st.success(f"✅ Successfully scraped {len(results_list)} result(s)!")
                st.dataframe(results_df, use_container_width=True)
                
                st.info("💾 Results saved to Student_Results.csv")
            else:
                st.error("❌ No results were scraped. Please check the roll numbers.")
        else:
            st.warning("⚠️ Please enter at least one roll number!")

# ============ DATA ANALYSIS TAB ============
elif selected_tab == "📋 Data Analysis":
    st.header("Detailed Data Analysis")
    st.markdown("---")
    
    df = load_results()
    
    if len(df) > 0:
        # Process marks
        df['Marks'] = df['Total_Marks'].apply(process_marks)
        df['Status'] = df['Total_Marks'].apply(lambda x: 'PASS' if 'PASS' in str(x) else 'FAIL')
        
        # Statistics Section
        st.subheader("📊 Statistical Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Mean Marks", f"{df['Marks'].mean():.2f}")
        with col2:
            st.metric("Median Marks", f"{df['Marks'].median():.2f}")
        with col3:
            st.metric("Std Deviation", f"{df['Marks'].std():.2f}")
        
        # Show statistics table
        st.subheader("Statistical Details")
        stats_df = df['Marks'].describe().to_frame().T
        st.dataframe(stats_df, use_container_width=True)
        
        st.markdown("---")
        
        # Full Data Display
        st.subheader("📋 Complete Student Data")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status:",
                ["PASS", "FAIL"],
                default=["PASS", "FAIL"]
            )
        with col2:
            marks_range = st.slider(
                "Filter by Marks Range:",
                0,
                int(df['Marks'].max()),
                (0, int(df['Marks'].max()))
            )
        
        # Apply filters
        filtered_df = df[
            (df['Status'].isin(status_filter)) &
            (df['Marks'] >= marks_range[0]) &
            (df['Marks'] <= marks_range[1])
        ]
        
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"student_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Correlation Analysis
        st.markdown("---")
        st.subheader("📈 Data Insights")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Total Students:** {len(filtered_df)}")
            st.write(f"**Passed:** {len(filtered_df[filtered_df['Status'] == 'PASS'])}")
            st.write(f"**Failed:** {len(filtered_df[filtered_df['Status'] == 'FAIL'])}")
        
        with col2:
            if len(filtered_df) > 0:
                st.write(f"**Highest Score:** {filtered_df['Marks'].max()}")
                st.write(f"**Lowest Score:** {filtered_df['Marks'].min()}")
                st.write(f"**Average Score:** {filtered_df['Marks'].mean():.2f}")
    
    else:
        st.warning("📌 No data available. Please scrape results first!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "<p>Student Results Dashboard | Built with Streamlit 🎈</p>"
    "</div>",
    unsafe_allow_html=True
)
