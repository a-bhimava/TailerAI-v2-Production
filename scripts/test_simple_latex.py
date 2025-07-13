#!/usr/bin/env python3

import subprocess
import tempfile
import os

# Create a simple test LaTeX document
test_latex_content = r"""
\documentclass[11pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{margin=0.75in}

\begin{document}
\section*{Test Resume}

\textbf{John Doe} \\
Software Engineer \\
Email: john@example.com

\section*{Experience}
\textbf{TechCorp} - Software Engineer (2020-2023) \\
New York, NY
\begin{itemize}
\item Developed scalable web applications
\item Improved system performance by 25\%
\end{itemize}

\section*{Education}
\textbf{University of Technology} \\
Bachelor of Science in Computer Science \\
Boston, MA (2019)

\end{document}
"""

print("Testing basic LaTeX compilation...")

try:
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, "test.tex")
        
        # Write LaTeX content
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(test_latex_content)
        
        print(f"LaTeX file written to: {tex_file}")
        
        # Try to compile
        result = subprocess.run(
            ['/Library/TeX/texbin/pdflatex', '-interaction=nonstopmode', 'test.tex'],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        # Check if PDF was created
        pdf_file = os.path.join(temp_dir, "test.pdf")
        if os.path.exists(pdf_file):
            print(f"✅ PDF created successfully: {pdf_file}")
            print(f"PDF size: {os.path.getsize(pdf_file)} bytes")
        else:
            print("❌ PDF was not created")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()