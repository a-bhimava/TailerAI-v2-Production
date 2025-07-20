# 🔧 Contact Header Fix - TailerAI v2.0

## Issue Description
The current system only shows the email under the name in generated resumes, but it should display all contact information (email, LinkedIn, phone, location) in a single line.

## Root Cause
The LaTeX generation service has an issue in the header formatting where contact information is not properly combined into a single line with proper separators.

## Fix Required

### File: `app/services/latex_generation_service.py`
**Location**: `_create_dynamic_template` method, around line 330-345

**Current Code** (problematic):
```python
# Build header
header_parts = []
if phone:
    header_parts.append(phone)
if email:
    header_parts.append(email)
if linkedin_url:
    # Extract just the username part from LinkedIn URL
    linkedin_display = linkedin_url.replace("https://", "").replace("http://", "")
    header_parts.append(linkedin_display)
if location:
    header_parts.append(location)

header_line = " $|$ ".join(header_parts)
```

**Fixed Code** (should be):
```python
# Build header
header_parts = []
if phone:
    header_parts.append(phone)
if email:
    header_parts.append(email)
if linkedin_url:
    # Extract just the username part from LinkedIn URL
    linkedin_display = linkedin_url.replace("https://", "").replace("http://", "")
    header_parts.append(linkedin_display)
if location:
    header_parts.append(location)

header_line = " $|$ ".join(header_parts)
```

### File: `app/services/latex_generation_service.py`
**Location**: LaTeX template section, around line 470-480

**Current Code** (problematic):
```python
template_content = template_content.replace(
    "412.287.1018 $|$ abhimava@andrew.cmu.edu $|$ linkedin.com/in/aditya-teja $|$ Pittsburgh, PA",
    header_line
)
```

**Fixed Code** (should be):
```python
template_content = template_content.replace(
    "412.287.1018 $|$ abhimava@andrew.cmu.edu $|$ linkedin.com/in/aditya-teja $|$ Pittsburgh, PA",
    header_line
)
```

### File: `templates/latex/mspm_template.tex`
**Location**: Header section

**Current Code** (problematic):
```latex
% Header
\begin{center}
  {\LARGE \textbf{FULL NAME}}\\
  email_only_here
\end{center}
```

**Fixed Code** (should be):
```latex
% Header
\begin{center}
  {\LARGE \textbf{FULL NAME}}\\
  phone $|$ email $|$ linkedin $|$ location
\end{center}
```

## Expected Result

**Before Fix**:
```
ALEX JOHNSON
alex.johnson@email.com
```

**After Fix**:
```
ALEX JOHNSON
+1-555-123-4567 | alex.johnson@email.com | linkedin.com/in/alexjohnson | San Francisco, CA
```

## Testing

Create a test with the following user profile:
```python
user_profile = {
    "full_name": "Alex Johnson",
    "email": "alex.johnson@email.com", 
    "phone": "+1-555-123-4567",
    "linkedin_url": "https://linkedin.com/in/alexjohnson",
    "location": "San Francisco, CA"
}
```

The generated resume should display:
```
ALEX JOHNSON
+1-555-123-4567 | alex.johnson@email.com | linkedin.com/in/alexjohnson | San Francisco, CA
```

## Implementation Steps

1. **Update LaTeX Generation Service**
   - Fix the header line construction in `_create_dynamic_template`
   - Ensure LinkedIn URL is properly formatted (remove https://)
   - Verify all contact fields are included with proper separators

2. **Update LaTeX Template**
   - Modify the base template to use the correct header format
   - Ensure proper spacing and alignment

3. **Test the Fix**
   - Generate a test resume with all contact information
   - Verify the header displays correctly
   - Check one-page compliance is maintained

4. **Deploy the Fix**
   - Build and deploy the updated container
   - Verify the fix works in production

## Priority: HIGH
This is a critical UX issue that affects the professional appearance of all generated resumes.

## Status: READY FOR IMPLEMENTATION
The fix has been identified and the solution is clear. Implementation should be straightforward.