from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import subprocess
import base64
from typing import Optional
import json
from github import Github
import tempfile
from fastapi.responses import FileResponse, JSONResponse
from bs4 import BeautifulSoup
from pathlib import Path

app = FastAPI()

class JobRequest(BaseModel):
    job_url: str
    github_token: str
    github_repo: str
    latex_path: str
    ollama_host: str = "http://localhost:11434"  # Default Ollama host

class ResumeResponse(BaseModel):
    pdf_base64: str
    summary_text: str

def parse_job_posting(url: str) -> str:
    """Extract text content from job posting URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
            
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse job posting: {str(e)}")

def get_latex_resume(github_token: str, repo: str, path: str) -> str:
    """Pull LaTeX resume from Github."""
    try:
        g = Github(github_token)
        repo = g.get_repo(repo)
        file_content = repo.get_contents(path)
        return base64.b64decode(file_content.content).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch resume from Github: {str(e)}")

def generate_summary(resume_text: str, job_description: str, ollama_host: str) -> str:
    """Generate resume summary using local Ollama deployment with Llama model."""
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        You are a professional resume writer. Your task is to create a powerful summary section 
        for a resume based on the candidate's experience and the specific job they're applying for.
        
        Resume Content:
        {resume_text}

        Job Description:
        {job_description}

        Generate a professional summary for this resume that highlights the most relevant experience 
        and skills for this specific job posting. The summary should be 3-4 sentences long and 
        focus on matching qualifications with job requirements. Make it impactful and specific.
        
        Summary:
        """
        
        data = {
            "model": "llama3.1",  # Using Llama 3.1 model
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        response = requests.post(
            f"{ollama_host}/api/generate",
            headers=headers,
            json=data
        )
        
        response.raise_for_status()
        return response.json()['response'].strip()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=500, 
            detail="Failed to connect to Ollama service. Ensure Ollama is running locally."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

def update_latex_template(template: str, summary: str) -> str:
    """Insert generated summary into LaTeX template."""
    # Assuming template has a placeholder like SUMMARYPLACEHOLDER
    return template.replace("SUMMARYPLACEHOLDER", summary)

# Create a temporary directory to store PDFs
TEMP_DIR = Path("temp_pdfs")
TEMP_DIR.mkdir(exist_ok=True)

def cleanup_old_files():
    """Remove PDF files older than 1 hour"""
    import time
    current_time = time.time()
    for pdf_file in TEMP_DIR.glob("*.pdf"):
        if current_time - pdf_file.stat().st_mtime > 3600:  # 1 hour
            pdf_file.unlink()

# [Previous functions remain the same until generate_pdf]

def generate_pdf(latex_content: str) -> Path:
    """Generate PDF from LaTeX content and return the file path."""
    try:
        cleanup_old_files()  # Cleanup old files
        
        # Create a unique filename
        import uuid
        pdf_filename = f"resume_{uuid.uuid4()}.pdf"
        pdf_path = TEMP_DIR / pdf_filename
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write LaTeX content to temporary file
            tex_path = os.path.join(temp_dir, "resume.tex")
            with open(tex_path, 'w') as f:
                f.write(latex_content)
            
            # Run pdflatex twice to resolve references
            for _ in range(2):
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', tex_path],
                    cwd=temp_dir,
                    capture_output=True,
                    check=True
                )
            
            # Copy the generated PDF to our temp directory
            temp_pdf_path = os.path.join(temp_dir, "resume.pdf")
            import shutil
            shutil.copy2(temp_pdf_path, pdf_path)
            
        return pdf_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@app.post("/generate-resume")
async def generate_resume(request: JobRequest):
    """Generate resume and return PDF file."""
    try:
        # 1. Parse job posting
        job_description = parse_job_posting(request.job_url)
        
        # 2. Get LaTeX resume template
        latex_template = get_latex_resume(
            request.github_token,
            request.github_repo,
            request.latex_path
        )
        
        # 3. Generate summary
        summary = generate_summary(latex_template, job_description, request.ollama_host)
        
        # 4. Update template with new summary
        updated_latex = update_latex_template(latex_template, summary)
        
        # 5. Generate PDF and get file path
        pdf_path = generate_pdf(updated_latex)
        
        # 6. Return the PDF file
        return FileResponse(
            path=pdf_path,
            filename="resume.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=resume.pdf"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Add an endpoint to get just the summary text
@app.post("/generate-summary")
async def generate_summary_only(request: JobRequest):
    """Generate and return only the summary text."""
    try:
        job_description = parse_job_posting(request.job_url)
        latex_template = get_latex_resume(
            request.github_token,
            request.github_repo,
            request.latex_path
        )
        summary = generate_summary(latex_template, job_description, request.ollama_host)
        return {"summary": summary}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup temporary files when shutting down."""
    import shutil
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)