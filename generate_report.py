import os
import re
import sys
import tempfile
import uuid

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def derive_status_value(status_value, marks_value):
    status_raw = str(status_value or "").strip()
    marks_raw = str(marks_value or "").strip()
    source = status_raw if status_raw else marks_raw
    if not source:
        return ""

    upper = source.upper()
    if "PASS" in upper:
        return "PASS"
    if upper.isdigit():
        return "PASS"
    if "FAIL" in upper:
        return "FAIL"
    if "ABSENT" in upper:
        return "ABSENT"
    if "SUPPLY" in upper:
        return "SUPPLY"
    return upper

def build_subject_stats(subject_pass_series):
    stats = {}
    for raw in subject_pass_series.dropna():
        text = str(raw).strip()
        if not text or text.lower() == "all pass" or ":" not in text:
            continue

        for part in text.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            pieces = part.split(":")
            subject_name = pieces[0].strip().upper()
            mark_raw = pieces[1].strip() if len(pieces) > 2 else ""
            status_str = pieces[-1].strip().upper()
            if not subject_name:
                continue
            if subject_name not in stats:
                stats[subject_name] = {"pass": 0, "fail": 0, "min_mark": None, "max_mark": None}
            if "PASS" in status_str:
                stats[subject_name]["pass"] += 1
            else:
                stats[subject_name]["fail"] += 1

            if mark_raw:
                mark_match = re.findall(r"\d+", mark_raw)
                if mark_match:
                    mark_value = float(mark_match[0])
                    current_min = stats[subject_name]["min_mark"]
                    current_max = stats[subject_name]["max_mark"]
                    stats[subject_name]["min_mark"] = mark_value if current_min is None else min(current_min, mark_value)
                    stats[subject_name]["max_mark"] = mark_value if current_max is None else max(current_max, mark_value)

    return stats

def parse_critical_subjects(row, subject_numeric_cols):
    if subject_numeric_cols:
        weak_subjs = []
        for col in subject_numeric_cols:
            mark = pd.to_numeric(row.get(col, 100), errors='coerce')
            if pd.notna(mark) and mark < 40:
                weak_subjs.append(str(col).title())
        return weak_subjs

    subject_pass = str(row.get('Subject_Pass', '')).strip()
    if not subject_pass or subject_pass.lower() == 'all pass' or ':' not in subject_pass:
        return []

    weak_subjs = []
    for part in subject_pass.split(','):
        part = part.strip()
        if not part or ':' not in part:
            continue
        pieces = part.split(':')
        subject_name = pieces[0].strip()
        status_str = pieces[-1].strip().upper()
        if subject_name and 'PASS' not in status_str:
            weak_subjs.append(subject_name.title())

    return weak_subjs

def generate_report(csv_file="Student_Results.csv", output_pdf="Academic_Performance_Report.pdf", institute_name="INSTITUTE OF EXCELLENCE", class_name=""):
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    try:
        df = pd.read_csv(csv_file)
        # Drop rows where Roll_Number is missing or empty
        if 'Roll_Number' in df.columns:
            df = df.dropna(subset=['Roll_Number'])
            df = df[df['Roll_Number'].astype(str).str.strip() != '']
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Check if df is empty
    if df.empty:
        print("Dataframe is empty, adding sample data for demonstration.")
        data = {
            'Roll_Number': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Judy'],
            'Father_Name': ['A_F', 'B_F', 'C_F', 'D_F', 'E_F', 'F_F', 'G_F', 'H_F', 'I_F', 'J_F'],
            'Total_Marks': [85, 40, 92, 35, 78, 65, 55, 88, 45, 95],
            'Status': ['PASS', 'FAIL', 'PASS', 'FAIL', 'PASS', 'PASS', 'PASS', 'PASS', 'FAIL', 'PASS'],
            'Math': [90, 45, 95, 30, 80, 60, 50, 85, 40, 95],
            'Science': [80, 35, 89, 40, 76, 70, 60, 91, 50, 95]
        }
        df = pd.DataFrame(data)

    # Convert status to proper case
    df['Status'] = df['Status'].astype(str).str.upper()
    df['Derived_Status'] = df.apply(
        lambda row: derive_status_value(row.get('Status', ''), row.get('Total_Marks', '')),
        axis=1
    )

    # Calculate Metrics
    total_students = len(df)
    total_passed = len(df[df['Derived_Status'] == 'PASS'])
    total_failed = total_students - total_passed
    pass_rate = (total_passed / total_students * 100) if total_students > 0 else 0
    fail_rate = (total_failed / total_students * 100) if total_students > 0 else 0
    marks_text = df['Total_Marks'].astype(str).str.extract(r'(\d+)')[0]
    df['Total_Marks'] = pd.to_numeric(marks_text, errors='coerce').fillna(0)
    
    passed_df = df[df['Derived_Status'] == 'PASS']
    avg_score_passed = passed_df['Total_Marks'].mean() if not passed_df.empty else 0
    highest_score = df['Total_Marks'].max() if len(df) > 0 else 0
    
    valid_passed = passed_df[passed_df['Total_Marks'] > 0]
    lowest_score_passed = valid_passed['Total_Marks'].min() if not valid_passed.empty else 0

    # Identify subject columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    # Exclude non-subject generic numeric columns like S.No
    exclude_cols = ['Roll_Number', 'Total_Marks', 'S.No', 'S.No.', 'S_No', 'Sr.No', 'Sr. No.', 'Unnamed: 0']
    subject_numeric_cols = [c for c in numeric_cols if c not in exclude_cols and not str(c).lower().startswith('s.n')]
    subject_stats = build_subject_stats(df['Subject_Pass']) if 'Subject_Pass' in df.columns else {}
    subject_chart_cols = subject_numeric_cols if subject_numeric_cols else sorted(subject_stats.keys())

    chart_paths = []
    chart_dir = tempfile.gettempdir()
    chart_id = uuid.uuid4().hex

    # --- Generate Charts ---
    # 1. Pass/Fail Distribution Pie Chart
    plt.figure(figsize=(5, 4))
    plt.pie([total_passed, total_failed], labels=['Passed', 'Failed'], colors=['#4CAF50', '#F44336'], autopct='%1.1f%%', startangle=140)
    plt.title('Overall Pass/Fail Distribution')
    plt.tight_layout()
    pie_chart_path = os.path.join(chart_dir, f"pass_fail_chart_{chart_id}.png")
    plt.savefig(pie_chart_path)
    plt.close()
    chart_paths.append(pie_chart_path)

    # Subject based charts if subjects exist
    if subject_chart_cols:
        # Instead of hardcoded pass mark, parse the Subject_Pass column if available, 
        # or fall back to 33% of 100 as a rough estimate if it's not.
        if subject_numeric_cols:
            subj_passes = pd.Series(0, index=subject_numeric_cols)
            subj_fails = pd.Series(0, index=subject_numeric_cols)

            if 'Subject_Pass' in df.columns:
                for row in df['Subject_Pass'].dropna():
                    parts = [p.strip() for p in row.split(',')]
                    for part in parts:
                        sub_parts = part.split(':')
                        if len(sub_parts) >= 3:
                            subj_name = sub_parts[0].strip().upper()
                            status_str = sub_parts[-1].strip().upper()
                            matching_col = next((c for c in subject_numeric_cols if str(c).strip().upper() == subj_name), None)
                            if matching_col:
                                if 'PASS' in status_str:
                                    subj_passes[matching_col] += 1
                                else:
                                    subj_fails[matching_col] += 1

                for c in subject_numeric_cols:
                    if subj_passes[c] == 0 and subj_fails[c] == 0:
                        subj_passes[c] = (pd.to_numeric(df[c], errors='coerce') >= 33).sum()
                        subj_fails[c] = (pd.to_numeric(df[c], errors='coerce') < 33).sum()
            else:
                pass_mark = 33
                for c in subject_numeric_cols:
                    subj_passes[c] = (pd.to_numeric(df[c], errors='coerce') >= pass_mark).sum()
                    subj_fails[c] = (pd.to_numeric(df[c], errors='coerce') < pass_mark).sum()
        else:
            subj_passes = pd.Series({k: v['pass'] for k, v in subject_stats.items()})
            subj_fails = pd.Series({k: v['fail'] for k, v in subject_stats.items()})

        # Subject-wise Pass Ratio 
        subj_pass_pct = (subj_passes / (subj_passes + subj_fails)) * 100
        
        # Sort in ascending order
        sorted_indices = subj_pass_pct.sort_values(ascending=True).index
        sorted_subject_cols = list(sorted_indices)
        sorted_subj_pass_pct = subj_pass_pct[sorted_indices]
        sorted_subj_passes = subj_passes[sorted_indices]
        sorted_subj_fails = subj_fails[sorted_indices]

        # 4. Subject-wise Pass Ratio (Horizontal Bar Chart)
        plt.figure(figsize=(6, 4))
        plt.barh(sorted_subject_cols, sorted_subj_pass_pct, color='#00BCD4')
        plt.title('Subject-wise Pass Ratio (%)')
        plt.xlabel('Pass Percentage (%)')
        plt.xlim(0, 105)
        plt.tight_layout()
        subj_avg_chart = os.path.join(chart_dir, f"subj_avg_chart_{chart_id}.png")
        plt.savefig(subj_avg_chart)
        plt.close()
        chart_paths.append(subj_avg_chart)
        
        # 5. Subject-wise Performance Analysis: Pass% vs Fail% (Horizontal Stacked Bar Chart)
        plt.figure(figsize=(6, 4))
        plt.barh(sorted_subject_cols, sorted_subj_passes, label='Passed', color='#4CAF50')
        plt.barh(sorted_subject_cols, sorted_subj_fails, left=sorted_subj_passes, label='Failed', color='#F44336')
        plt.title('Subject-wise Performance Analysis (Pass/Fail)')
        plt.xlabel('Number of Students')
        plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=2)
        plt.tight_layout()
        subj_perf_chart = os.path.join(chart_dir, f"subj_perf_chart_{chart_id}.png")
        plt.savefig(subj_perf_chart)
        plt.close()
        chart_paths.append(subj_perf_chart)
    else:
        subj_avg_chart = subj_perf_chart = None

    # Generate PDF
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=14, alignment=1, textColor=colors.HexColor('#2c3e50'))
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=16, spaceAfter=10, spaceBefore=15, textColor=colors.HexColor('#2c3e50'))
    sub_heading_style = ParagraphStyle('SubHeadingStyle', parent=styles['Heading3'], fontSize=14, spaceAfter=8, spaceBefore=12, textColor=colors.HexColor('#2c3e50'))
    normal_style = styles['Normal']
    bullet_style = ParagraphStyle('Bullet', parent=normal_style, leftIndent=20, bulletIndent=10)

    # --- 1. INSTITUTE NAME & EXECUTIVE SUMMARY ---
    story.append(Paragraph(f"<b>{institute_name}</b>", title_style))
    
    report_title = "Academic Performance Report"
    if class_name and class_name.strip():
        report_title = f"{class_name.strip()} Class Performance Report"
        
    story.append(Paragraph(f"<b>{report_title}</b>", ParagraphStyle('SubTitle', parent=title_style, fontSize=16, textColor=colors.gray)))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>EXECUTIVE SUMMARY</b>", heading_style))
    story.append(Paragraph(f"This report provides a comprehensive overview of the academic performance for the recent examination cycle. Out of <b>{total_students}</b> students, the overall pass percentage stands at <b>{pass_rate:.1f}%</b>, while the fail percentage is <b>{fail_rate:.1f}%</b>. The general performance trend indicates areas of both high achievement and required support.", normal_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>KEY PERFORMANCE METRICS</b>", heading_style))
    metrics_data = [
        ["Metric", "Value"],
        ["Total Students", str(total_students)],
        ["Students Passed", str(total_passed)],
        ["Students Failed", str(total_failed)],
        ["Average Total Marks (Passed)", f"{avg_score_passed:.1f}"],
        ["Highest Total Marks", str(highest_score)],
        ["Lowest Total Marks (Passed)", str(lowest_score_passed)]
    ]
    metrics_table = Table(metrics_data, colWidths=[200, 150])
    
    metrics_base_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), 
        ('ALIGN', (0,0), (0,-1), 'LEFT'), 
        ('ALIGN', (1,0), (1,-1), 'CENTER'), 
        ('ALIGN', (0,0), (-1,0), 'CENTER'), 
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10), 
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]
    
    for i in range(1, len(metrics_data)):
        if i % 2 == 0:
            metrics_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1')))
        else:
            metrics_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

    metrics_table.setStyle(TableStyle(metrics_base_style))
    story.append(metrics_table)
    story.append(Spacer(1, 15))

    # --- 2. PERFORMANCE VISUALIZATIONS & INSIGHTS ---
    story.append(PageBreak())
    story.append(Paragraph("<b>PERFORMANCE VISUALIZATIONS & INSIGHTS</b>", heading_style))

    # Pie Chart
    story.append(Paragraph("<b>1. Pass/Fail Distribution:</b> Understand the overarching success metric.", bullet_style))
    story.append(RLImage(pie_chart_path, width=300, height=240))

    if subject_chart_cols:
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>PERFORMANCE VISUALIZATIONS & INSIGHTS (Cont.)</b>", heading_style))
        story.append(Paragraph("<b>3. Subject-wise Pass Ratio:</b> Identifies overall course success rates.", bullet_style))
        story.append(RLImage(subj_avg_chart, width=350, height=230))
        
        story.append(Paragraph("<b>4. Subject-wise Performance Analysis:</b> Identifies pass/fail success per subject.", bullet_style))
        story.append(RLImage(subj_perf_chart, width=350, height=230))

    # --- 3. SUBJECT-WISE PERFORMANCE ANALYSIS ---
    if subject_numeric_cols:
        story.append(PageBreak())
        story.append(Paragraph("<b>SUBJECT-WISE PERFORMANCE ANALYSIS</b>", heading_style))
        
        subj_perf_data = [["Subject", "Total Students", "Mean", "Median", "Min", "Max", "Std Dev"]]
        for subj in subject_numeric_cols:
            s_count = df[subj].count()
            s_mean = df[subj].mean()
            s_median = df[subj].median()
            s_min = df[subj].min()
            s_max = df[subj].max()
            s_std = df[subj].std()
            
            subj_perf_data.append([subj, f"{s_count}", f"{s_mean:.1f}", f"{s_median:.1f}", f"{s_min:.1f}", f"{s_max:.1f}", f"{s_std:.1f}"])
            
        subj_table = Table(subj_perf_data, colWidths=[90, 70, 60, 60, 60, 60, 60])
        
        subj_base_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,1), (0,-1), 8),  # Makes the Subject column text smaller
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('GRID', (0,0), (-1,-1), 1, colors.grey)
        ]
        
        for i in range(1, len(subj_perf_data)):
            if i % 2 == 0:
                subj_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1')))
            else:
                subj_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
                
        subj_table.setStyle(TableStyle(subj_base_style))
        story.append(subj_table)
        story.append(Spacer(1, 15))
    elif subject_chart_cols:
        story.append(PageBreak())
        story.append(Paragraph("<b>SUBJECT-WISE PERFORMANCE ANALYSIS</b>", heading_style))

        subj_perf_data = [["Subject", "Total Students", "Passed", "Failed", "Pass Rate", "Min", "Max"]]
        subject_rows = []
        for subject, stats in subject_stats.items():
            total = stats["pass"] + stats["fail"]
            pass_rate_pct = (stats["pass"] / total * 100) if total else 0
            subject_rows.append((
                subject,
                total,
                stats["pass"],
                stats["fail"],
                pass_rate_pct,
                stats.get("min_mark"),
                stats.get("max_mark")
            ))

        subject_rows.sort(key=lambda row: row[4])
        for subject, total, passed, failed, pass_rate_pct, min_mark, max_mark in subject_rows:
            min_display = f"{min_mark:.0f}" if min_mark is not None else "-"
            max_display = f"{max_mark:.0f}" if max_mark is not None else "-"
            subj_perf_data.append([
                subject.title(),
                str(total),
                str(passed),
                str(failed),
                f"{pass_rate_pct:.1f}%",
                min_display,
                max_display,
            ])

        subj_table = Table(subj_perf_data, colWidths=[120, 80, 50, 50, 70, 60, 60])

        subj_base_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,1), (0,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('GRID', (0,0), (-1,-1), 1, colors.grey)
        ]

        for i in range(1, len(subj_perf_data)):
            if i % 2 == 0:
                subj_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1')))
            else:
                subj_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

        subj_table.setStyle(TableStyle(subj_base_style))
        story.append(subj_table)
        story.append(Spacer(1, 15))

    # --- 4. TOP 10 PERFORMERS ---
    story.append(PageBreak())
    story.append(Paragraph("<b>TOP 10 PERFORMERS</b>", heading_style))
    top10_df = df.sort_values(by='Total_Marks', ascending=False).head(10)
    max_total_marks = df['Total_Marks'].max() if len(df) > 0 else 0
    
    top_data = [["Rank", "Student Name", "Roll Number", "Total Marks", "Comments"]]
    for idx, row in enumerate(top10_df.iterrows()):
        row_data = row[1]
        if subject_numeric_cols:
            pct = (row_data.get('Total_Marks', 0) / (len(subject_numeric_cols) * 100) * 100)
        else:
            pct = (row_data.get('Total_Marks', 0) / max_total_marks * 100) if max_total_marks else 0
        cmt = "Excellent" if pct >= 80 else "Good"
        top_data.append([str(idx+1), str(row_data.get('Name', '')), str(row_data.get('Roll_Number', '')), f"{row_data.get('Total_Marks', 0):.1f}", cmt])
    
    top_table = Table(top_data, colWidths=[50, 140, 100, 100, 100])
    
    # Base Style
    base_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#27ae60')), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), 
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
        ('BOTTOMPADDING', (0,0), (-1,0), 10), 
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]
    
    # Alternating Colors logically like tr:nth-child(even)
    for i in range(1, len(top_data)):
        if i % 2 == 0:
            base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#eafaf1')))
        else:
            base_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

    top_table.setStyle(TableStyle(base_style))
    story.append(top_table)
    story.append(Spacer(1, 15))

    # --- 5. STUDENTS REQUIRING SUPPORT ---
    story.append(Paragraph("<b>STUDENTS REQUIRING SUPPORT</b>", heading_style))
    failed_df = df[df['Derived_Status'] != 'PASS'].sort_values(by='Total_Marks', ascending=True)
    
    crit_subj_style = ParagraphStyle('CritSubj', parent=styles['Normal'], fontSize=7, leading=9, alignment=1) # alignment=1 is Center
    
    support_data = [["Rank", "Roll Number", "Name", "Critical Subjects"]]
    rank = 1
    for _, row in failed_df.iterrows():
        weak_subjs = parse_critical_subjects(row, subject_numeric_cols)
        weak_str = ", ".join(weak_subjs) if weak_subjs else "None"
        # Wrap the critical subjects cell in a Paragraph so it wraps and uses smaller font
        support_data.append([str(rank), str(row.get('Roll_Number', '')), str(row.get('Name', '')), Paragraph(weak_str, crit_subj_style)])
        rank += 1

    if len(support_data) > 1:
        support_table = Table(support_data, colWidths=[50, 100, 150, 180])
        
        support_base_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#c0392b')), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), 
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
            ('FONTSIZE', (0,1), (2,-1), 9), 
            ('BOTTOMPADDING', (0,0), (-1,0), 10), 
            ('GRID', (0,0), (-1,-1), 1, colors.grey)
        ]
        
        # Alternating background colors for rows
        for i in range(1, len(support_data)):
            if i % 2 == 0:
                support_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5b7b1')))
            else:
                support_base_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

        support_table.setStyle(TableStyle(support_base_style))
        story.append(support_table)
    else:
        story.append(Paragraph("No students currently require emergency academic support based on failing status.", normal_style))
        
    story.append(Spacer(1, 15))

    # --- 6. RECOMMENDATIONS FOR IMPROVEMENT ---
    story.append(Paragraph("<b>RECOMMENDATIONS FOR IMPROVEMENT</b>", heading_style))
    story.append(Paragraph("• <b>Extra classes:</b> Arrange supplementary classes for students falling behind in core subjects.", bullet_style))
    story.append(Paragraph("• <b>Subject-specific coaching:</b> Provide targeted coaching based on the most challenging subjects.", bullet_style))
    story.append(Paragraph("• <b>Teacher strategy improvement:</b> Review and align teaching methodologies to address common areas of weakness.", bullet_style))
    story.append(Paragraph("• <b>Student mentoring:</b> Implement a peer-to-peer or faculty mentoring program to guide struggling students.", bullet_style))

    # Build the PDF
    doc.build(story)
    print(f"Report successfully generated at: {output_pdf}")
    
    # Cleanup temp chart images
    for p in chart_paths:
        if p and os.path.exists(p):
            os.remove(p)

if __name__ == "__main__":
    generate_report()
