import google.generativeai as genai
from pathlib import Path
import gradio as gr
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile

# Load environment variables from a .env file
load_dotenv()

# Configure the GenerativeAI API key using the loaded environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up the model configuration for text generation
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

# Define safety settings for content generation
safety_settings = [
    {"category": f"HARM_CATEGORY_{category}", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    for category in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]
]

# Initialize the GenerativeModel
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

def read_image_data(file_path):
    image_path = Path(file_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Could not find image: {image_path}")
    return {"mime_type": "image/jpeg", "data": image_path.read_bytes()}

def generate_gemini_response(prompt, image_path):
    image_data = read_image_data(image_path)
    response = model.generate_content([prompt, image_data])
    return response.text

def format_report(disease_name, analysis_text):
    # Split the analysis text into sections
    sections = analysis_text.split('\n\n')
    
    # Create a structured report
    report = {
        "disease_name": disease_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analysis": {
            "symptoms": "",
            "causes": "",
            "treatment": "",
            "prevention": "",
            "additional_notes": ""
        }
    }
    
    # Parse the sections
    for section in sections:
        if "Symptoms" in section:
            report["analysis"]["symptoms"] = section.replace("Symptoms:", "").strip()
        elif "Causes" in section:
            report["analysis"]["causes"] = section.replace("Causes:", "").strip()
        elif "Treatment" in section:
            report["analysis"]["treatment"] = section.replace("Treatment:", "").strip()
        elif "Prevention" in section:
            report["analysis"]["prevention"] = section.replace("Prevention:", "").strip()
        else:
            report["analysis"]["additional_notes"] += section + "\n"
    
    return report

def generate_pdf_report(report_data):
    # Create a temporary file for the PDF
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, f"plant_disease_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#1b5e20')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#2e7d32')
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    # Create content
    story = []
    
    # Title
    story.append(Paragraph("PLANT DISEASE ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 20))
    
    # Report Info Table
    report_info = [
        ["Disease Name:", report_data['disease_name']],
        ["Analysis Date:", report_data['timestamp']]
    ]
    table = Table(report_info, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1b5e20')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#a5d6a7'))
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Symptoms Section
    story.append(Paragraph("Symptoms", heading_style))
    story.append(Paragraph(report_data['analysis']['symptoms'], normal_style))
    story.append(Spacer(1, 10))
    
    # Causes Section
    story.append(Paragraph("Causes", heading_style))
    story.append(Paragraph(report_data['analysis']['causes'], normal_style))
    story.append(Spacer(1, 10))
    
    # Treatment Section
    story.append(Paragraph("Treatment", heading_style))
    story.append(Paragraph(report_data['analysis']['treatment'], normal_style))
    story.append(Spacer(1, 10))
    
    # Prevention Section
    story.append(Paragraph("Prevention", heading_style))
    story.append(Paragraph(report_data['analysis']['prevention'], normal_style))
    story.append(Spacer(1, 10))
    
    # Additional Notes Section
    if report_data['analysis']['additional_notes']:
        story.append(Paragraph("Additional Notes", heading_style))
        story.append(Paragraph(report_data['analysis']['additional_notes'], normal_style))
        story.append(Spacer(1, 10))
    
    # Disclaimer
    disclaimer_style = ParagraphStyle(
        'CustomDisclaimer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=1
    )
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Disclaimer: This report is generated by AI and should be used as a reference only. "
        "Please consult with a professional plant pathologist for accurate diagnosis and treatment.",
        disclaimer_style
    ))
    
    # Build PDF
    doc.build(story)
    return filename

def format_report_text(response):
    # Split the response into sections
    sections = response.split('\n\n')
    formatted_text = ""
    
    for section in sections:
        if "Disease Name:" in section:
            disease_name = section.replace("Disease Name:", "").strip()
            formatted_text += f"""
            <div class="disease-name">
                {disease_name}
            </div>
            """
        elif "Symptoms:" in section:
            formatted_text += f"""
            <div class="report-section">
                <div class="report-title">Symptoms</div>
                <div class="report-content">
                    {section.replace('Symptoms:', '').strip()}
                </div>
            </div>
            """
        elif "Causes:" in section:
            formatted_text += f"""
            <div class="report-section">
                <div class="report-title">Causes</div>
                <div class="report-content">
                    {section.replace('Causes:', '').strip()}
                </div>
            </div>
            """
        elif "Treatment:" in section:
            formatted_text += f"""
            <div class="report-section">
                <div class="report-title">Treatment</div>
                <div class="report-content">
                    {section.replace('Treatment:', '').strip()}
                </div>
            </div>
            """
        elif "Prevention:" in section:
            formatted_text += f"""
            <div class="report-section">
                <div class="report-title">Prevention</div>
                <div class="report-content">
                    {section.replace('Prevention:', '').strip()}
                </div>
            </div>
            """
        elif "Additional Notes:" in section:
            formatted_text += f"""
            <div class="report-section">
                <div class="report-title">Additional Notes</div>
                <div class="report-content">
                    {section.replace('Additional Notes:', '').strip()}
                </div>
            </div>
            """
        else:
            formatted_text += f"""
            <div class="report-section">
                <div class="report-content">
                    {section.strip()}
                </div>
            </div>
            """
    
    return formatted_text

def process_uploaded_files(files):
    file_path = files[0].name if files else None
    if file_path:
        response = generate_gemini_response(input_prompt, file_path)
        # Extract disease name (first line of response)
        disease_name = response.split('\n')[0].strip()
        # Format the report
        report_data = format_report(disease_name, response)
        # Generate PDF report
        report_file = generate_pdf_report(report_data)
        # Format the text for display
        formatted_text = format_report_text(response)
        return file_path, formatted_text, report_file
    return None, None, None

input_prompt = """
As a highly skilled plant pathologist, your expertise is indispensable in our pursuit of maintaining optimal plant health. You will be provided with information or samples related to plant diseases, and your role involves conducting a detailed analysis to identify the specific issues, propose solutions, and offer recommendations.

Please provide your analysis in the following structured format:

Disease Name: [Name of the disease]

Symptoms:
[Detailed description of visible symptoms]

Causes:
[Explanation of what causes this disease]

Treatment:
[Recommended treatment methods and steps]

Prevention:
[Preventive measures to avoid future occurrences]

Additional Notes:
[Any other relevant information]

Your analysis should be thorough, accurate, and focused on plant health. Please ensure the information is clear and actionable for the user.
"""

# Enhanced CSS with modern design elements and animations
custom_css = """
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    .gradio-container {
        background: linear-gradient(-45deg, #e8f5e9, #c8e6c9, #a5d6a7, #81c784, #66bb6a, #4caf50);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding: 20px;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
    }
    
    .gradio-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path fill="%23ffffff" fill-opacity="0.1" d="M0,0 L100,0 L100,100 L0,100 Z"/></svg>');
        opacity: 0.1;
        animation: shimmer 20s linear infinite;
    }
    
    .header {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #1b5e20;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        padding: 25px;
        background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(232,245,233,0.9));
        border-radius: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        animation: float 6s ease-in-out infinite;
        position: relative;
        overflow: hidden;
        border: 2px solid rgba(46,125,50,0.3);
    }
    
    .header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: slideIn 2s infinite;
    }
    
    .instructions {
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,245,233,0.95));
        padding: 25px;
        border-radius: 20px;
        border-left: 5px solid #2e7d32;
        margin-bottom: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: slideIn 1s ease-out;
        border: 1px solid rgba(46,125,50,0.2);
    }
    
    .step-icon {
        font-size: 32px;
        animation: pulse 2s infinite;
        margin-bottom: 10px;
        display: inline-block;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #2e7d32, #1b5e20);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .upload-box {
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,245,233,0.95));
        padding: 30px;
        border-radius: 20px;
        border: 3px dashed #2e7d32;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        animation: fadeIn 1s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .upload-box::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: rotate 4s linear infinite;
    }
    
    button.primary {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 30px !important;
        border-radius: 30px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        animation: pulse 2s infinite !important;
        position: relative;
        overflow: hidden;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .analysis-box {
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,245,233,0.95));
        border: 2px solid #a5d6a7;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: fadeIn 1s ease-out;
    }
    
    .tips-box {
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,245,233,0.95));
        padding: 20px;
        border-radius: 20px;
        margin-top: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border: 2px solid #a5d6a7;
        transition: all 0.3s ease;
        animation: slideIn 1s ease-out;
    }
    
    .footer {
        text-align: center;
        margin-top: 30px;
        color: #1b5e20;
        font-size: 16px;
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,245,233,0.95));
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        animation: fadeIn 1s ease-out;
        border: 1px solid rgba(46,125,50,0.2);
    }
    
    .plant-icon {
        font-size: 28px;
        vertical-align: middle;
        margin: 0 8px;
        animation: float 4s ease-in-out infinite;
        display: inline-block;
        filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.1));
    }
    
    .decoration {
        position: absolute;
        font-size: 24px;
        opacity: 0.3;
        animation: float 6s ease-in-out infinite;
        filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.1));
    }
    
    .decoration:nth-child(1) { top: 10%; left: 5%; animation-delay: 0s; }
    .decoration:nth-child(2) { top: 20%; right: 5%; animation-delay: 1s; }
    .decoration:nth-child(3) { bottom: 10%; left: 15%; animation-delay: 2s; }
    .decoration:nth-child(4) { bottom: 20%; right: 15%; animation-delay: 3s; }
    
    .report-section {
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,245,233,0.95));
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: slideIn 1s ease-out;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(46,125,50,0.2);
    }
    
    .report-title {
        color: #1b5e20;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
        border-bottom: 2px solid #a5d6a7;
        padding-bottom: 5px;
        position: relative;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .report-content {
        color: #333;
        line-height: 1.6;
        padding: 15px;
        background: rgba(232, 245, 233, 0.3);
        border-radius: 10px;
        transition: all 0.3s ease;
        border: 1px solid rgba(46,125,50,0.1);
    }
    
    .disease-name {
        font-size: 24px;
        color: #1b5e20;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        animation: float 4s ease-in-out infinite;
        background: linear-gradient(135deg, #2e7d32, #1b5e20);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
"""

with gr.Blocks(css=custom_css) as demo:
    # Header with enhanced styling
    gr.Markdown("""
    <div class='header'>
        <span class="decoration">🌱</span>
        <span class="decoration">🌿</span>
        <span class="decoration">🌾</span>
        <span class="decoration">🌵</span>
        <span class="decoration">🌸</span>
        <span class="decoration">🌺</span>
        <span class="plant-icon">🌱</span> 
        Plant Disease Detection AI 
        <span class="plant-icon">🌱</span>
    </div>
    """)
    
    # Instructions with enhanced styling
    gr.Markdown("""
    <div class='instructions'>
        <h3 style="color: #1b5e20; margin-top: 0; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">How to Use This Tool</h3>
        <div style="display: flex; justify-content: space-around; margin-top: 20px;">
            <div style="text-align: center;">
                <div class="step-icon">📸</div>
                <p style="font-weight: bold; color: #1b5e20;">Upload Image</p>
                <p style="color: #666;">Take a clear photo of your plant</p>
            </div>
            <div style="text-align: center;">
                <div class="step-icon">🔍</div>
                <p style="font-weight: bold; color: #1b5e20;">AI Analysis</p>
                <p style="color: #666;">Our AI examines the image</p>
            </div>
            <div style="text-align: center;">
                <div class="step-icon">📋</div>
                <p style="font-weight: bold; color: #1b5e20;">Get Results</p>
                <p style="color: #666;">Receive detailed diagnosis</p>
            </div>
        </div>
        <p style="margin-top: 20px; font-style: italic; color: #666; text-align: center;">
            For best results, ensure the image is well-lit and focused on the affected area
        </p>
    </div>
    """)

    # Main content area with enhanced styling
    with gr.Row():
        with gr.Column(scale=1):
            # Upload section with enhanced styling
            with gr.Group():
                gr.Markdown("""
                <div class="upload-box">
                    <h3 style="color: #1b5e20; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">Upload Your Plant Image</h3>
                    <p style="margin-bottom: 20px; color: #666;">Click below to select an image of your plant</p>
                    <span class="plant-icon">🌿</span>
                    <span class="plant-icon">🌸</span>
                    <span class="plant-icon">🌺</span>
                </div>
                """)
                upload_button = gr.UploadButton(
                    "📷 Upload Image",
                    file_types=["image"],
                    file_count="multiple",
                    variant="primary"
                )
            
            # Tips section with enhanced styling
            gr.Markdown("""
            <div class="tips-box">
                <h4 style="color: #1b5e20; margin-top: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">📝 Tips for Best Results:</h4>
                <ul style="margin-bottom: 0; color: #666;">
                    <li>Take photos in good lighting</li>
                    <li>Focus on affected leaves or stems</li>
                    <li>Include multiple angles if possible</li>
                    <li>Ensure clear, high-resolution images</li>
                </ul>
            </div>
            """)
            
        with gr.Column(scale=2):
            # Results section with enhanced styling
            with gr.Group():
                image_output = gr.Image(
                    label="Uploaded Image",
                    elem_classes=["analysis-box"],
                    height=400
                )
                file_output = gr.HTML(
                    label="Disease Analysis Report",
                    elem_classes=["analysis-box"]
                )
                report_file = gr.File(
                    label="Download Report",
                    visible=True
                )

    # Set up the upload button to trigger the processing function
    upload_button.upload(
        process_uploaded_files,
        upload_button,
        [image_output, file_output, report_file]
    )

    # Footer with enhanced styling
    gr.Markdown("""
    <div class='footer'>
        <div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 15px;">
            <span class="plant-icon">🌾</span>
            <span style="font-weight: bold; color: #1b5e20;">Helping farmers protect their crops</span>
            <span class="plant-icon">🌱</span>
            <span style="font-weight: bold; color: #1b5e20;">Powered by AI Technology</span>
            <span class="plant-icon">🌿</span>
            <span style="font-weight: bold; color: #1b5e20;">Making agriculture smarter</span>
        </div>
        <p style="margin-top: 10px; color: #666;">© 2024 Plant Disease Detection AI</p>
    </div>
    """)

# Launch the Gradio interface with debug mode enabled
demo.launch(debug=True, share=False, inbrowser=True)
