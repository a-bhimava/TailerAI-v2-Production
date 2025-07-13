# Master Resume Input & Storage Workflow - TailerAI v2.0

## 🎯 **USER INPUT METHODS: MULTIPLE PATHWAYS TO BUILD MASTER DATASET**

Users can build their master dataset through several flexible input methods, accommodating different preferences and existing documentation formats.

---

## 📤 **INPUT METHOD 1: COMPREHENSIVE RESUME UPLOAD**

### **Primary Workflow: Intelligent Document Parsing**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📄 MASTER RESUME UPLOAD & PARSING WORKFLOW                                │
│                                                                             │
│ Step 1: Upload Comprehensive Resume                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📁 DRAG & DROP OR BROWSE                                                │ │
│ │ Supported: PDF, DOCX, TXT                                               │ │
│ │ ✅ "Comprehensive_Resume_All_Experience.pdf" (uploaded)                 │ │
│ │ ✅ "Complete_Work_History.docx" (uploaded)                              │ │
│ │ ✅ "Master_CV_Full_Details.txt" (uploaded)                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Step 2: AI-Powered Intelligent Parsing                                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🤖 ENHANCED PARSING ENGINE                                              │ │
│ │                                                                         │ │
│ │ ✅ Contact Information Extracted                                        │ │
│ │   • Name: John Smith                                                    │ │
│ │   • Email: john.smith@email.com                                         │ │
│ │   • Phone: +1 (555) 123-4567                                           │ │
│ │   • LinkedIn: linkedin.com/in/johnsmith                                 │ │
│ │                                                                         │ │
│ │ ✅ Work Experiences Identified: 4 positions                            │ │
│ │   • ICICI Bank - Manager (2023-2024) → 8 achievements detected         │ │
│ │   • Galderma - Marketing Intern (2022) → 5 achievements detected       │ │
│ │   • TechCorp - Analyst (2021-2022) → 6 achievements detected           │ │
│ │   • StartupXYZ - Intern (2021) → 3 achievements detected               │ │
│ │                                                                         │ │
│ │ ✅ Education & Certifications: 3 entries                               │ │
│ │   • MBA - Carnegie Mellon University (2023)                            │ │
│ │   • B.Tech - Indian Institute of Technology (2021)                     │ │
│ │   • CFA Level 1 Certification (2022)                                   │ │
│ │                                                                         │ │
│ │ ✅ Skills Extracted: 45 technical & soft skills                        │ │ 
│ │ ✅ Projects Identified: 6 significant projects                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Step 3: AI-Enhanced Content Structuring                                    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🧠 GEMINI AI CONTENT ANALYSIS                                           │ │
│ │                                                                         │ │
│ │ Processing each work experience:                                        │ │
│ │ ✅ Achievement Categorization (leadership, technical, financial)        │ │
│ │ ✅ Impact Level Scoring (1-10 scale)                                    │ │
│ │ ✅ Keyword Extraction for ATS optimization                              │ │ 
│ │ ✅ Skills Mapping to specific achievements                              │ │
│ │ ✅ Quantified Metrics Identification ($, %, numbers)                   │ │
│ │ ✅ Business Function Classification                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Enhanced Parsing Implementation**

```python
# Enhanced DocumentParser for Master Dataset Creation
class MasterDatasetParser(DocumentParser):
    """
    Enhanced parser specifically for comprehensive master dataset creation
    Integrates AI analysis for intelligent content structuring
    """
    
    def parse_master_resume(self, file_path: Path, user_profile_id: str) -> MasterDatasetContent:
        """
        Parse comprehensive resume and create structured master dataset
        """
        # Step 1: Basic document parsing (existing functionality)
        parsed_content = self.parse_document(file_path)
        
        # Step 2: AI-enhanced content analysis
        enhanced_content = self._ai_enhanced_analysis(parsed_content)
        
        # Step 3: Structure for master dataset storage
        master_dataset = self._create_master_dataset_structure(
            enhanced_content, user_profile_id
        )
        
        return master_dataset
    
    def _ai_enhanced_analysis(self, parsed_content: ParsedContent) -> EnhancedContent:
        """
        Use Gemini AI to intelligently analyze and categorize content
        """
        from app.services.gemini_client import GeminiClient
        
        gemini_client = GeminiClient()
        
        # AI Analysis Prompt for Master Dataset Creation
        analysis_prompt = f"""
        Analyze this comprehensive resume and extract structured information for a master dataset:
        
        RESUME CONTENT:
        {parsed_content.raw_text}
        
        Please extract and structure the following:
        
        1. WORK EXPERIENCES:
           - For each position, identify:
             * Company name, role, dates
             * Individual achievements (separate each bullet point)
             * Quantified metrics (numbers, percentages, dollar amounts)
             * Skills demonstrated in each achievement
             * Impact level (1-10 scale) for each achievement
             * Business function (sales, marketing, operations, etc.)
             * Keywords for ATS optimization
        
        2. EDUCATION:
           - Institutions, degrees, dates, GPA, honors
           - Relevant coursework and academic projects
           - Academic achievements and awards
        
        3. SKILLS & COMPETENCIES:
           - Technical skills with proficiency levels
           - Soft skills with examples
           - Tools and technologies
           - Years of experience for each skill
        
        4. PROJECTS:
           - Project name, description, role, outcomes
           - Technologies used, team size
           - Measurable results and impact
        
        Return as structured JSON with detailed categorization.
        """
        
        # Get AI analysis
        ai_analysis = gemini_client.analyze_content(analysis_prompt)
        
        return self._parse_ai_response(ai_analysis)
```

---

## 📤 **INPUT METHOD 2: MANUAL COMPREHENSIVE INPUT**

### **Guided Step-by-Step Builder**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔨 MASTER DATASET BUILDER - Comprehensive Manual Input                    │
│                                                                             │
│ Progress: [████████████████████░░░░] 80% Complete                          │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Step 4 of 5: Work Experience Details                                   │ │
│ │                                                                         │ │
│ │ 🏢 ICICI BANK - Manager, Corporate Banking                             │ │
│ │ Duration: April 2023 - November 2024                                   │ │
│ │                                                                         │ │
│ │ ✅ Basic Info Complete                                                  │ │
│ │ ✅ Role Summary Complete                                                │ │
│ │ 📝 Now Adding Individual Achievements:                                  │ │
│ │                                                                         │ │
│ │ Achievement #3:                                                         │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Description: *                                                      │ │ │
│ │ │ Managed investment portfolio worth $650M comprising 45 corpo...     │ │ │
│ │ │                                                                     │ │ │
│ │ │ 🎯 Impact Level: ●●●●●●●●●○ (9/10)                                 │ │ │
│ │ │ 💼 Category: [Financial Management ▼]                              │ │ │
│ │ │ 📊 Quantified Results:                                              │ │ │
│ │ │   • Dollar Amount: $650,000,000                                     │ │ │
│ │ │   • Count: 45 corporations                                          │ │ │
│ │ │   • Time Period: 18 months                                          │ │ │
│ │ │                                                                     │ │ │
│ │ │ 🔧 Skills Demonstrated:                                             │ │ │
│ │ │   ✅ Portfolio Management  ✅ Risk Assessment                       │ │ │
│ │ │   ✅ Client Relations     ✅ Financial Analysis                     │ │ │
│ │ │                                                                     │ │ │
│ │ │ 🏷️ ATS Keywords:                                                    │ │ │
│ │ │   portfolio, management, financial, corporate banking, investment   │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                         │ │
│ │ [Save Achievement] [+ Add Another] [AI Suggestions]                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Previous: Role Summary] [Next: Projects & Skills] [Save & Continue Later] │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📤 **INPUT METHOD 3: BULK IMPORT FROM EXTERNAL SOURCES**

### **LinkedIn Integration & Bulk Import**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔗 BULK IMPORT OPTIONS                                                     │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 💼 LINKEDIN IMPORT                                                      │ │
│ │ Connect your LinkedIn profile to auto-populate work history:            │ │
│ │                                                                         │ │
│ │ [🔗 Connect LinkedIn Account]                                           │ │
│ │                                                                         │ │
│ │ What we'll import:                                                      │ │
│ │ ✅ Work experience titles, companies, dates                            │ │
│ │ ✅ Education details and institutions                                   │ │
│ │ ✅ Skills and endorsements                                              │ │
│ │ ✅ Recommendations and achievements                                     │ │
│ │ ⚠️  Note: You'll still need to add detailed achievements manually      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 CSV/EXCEL IMPORT                                                     │ │
│ │ Upload structured data files:                                           │ │
│ │                                                                         │ │
│ │ [📁 Upload CSV] [📁 Upload Excel] [📄 Download Template]               │ │
│ │                                                                         │ │
│ │ Template includes columns for:                                          │ │
│ │ • Company, Role, Start Date, End Date                                   │ │
│ │ • Achievement Description, Impact Level, Category                       │ │
│ │ • Quantified Metrics, Skills, Keywords                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📝 MULTIPLE RESUME PARSING                                              │ │
│ │ Upload multiple resumes/CVs for comprehensive dataset:                  │ │
│ │                                                                         │ │
│ │ ✅ "Technical_Resume_Software_Roles.pdf"                               │ │
│ │ ✅ "Finance_Resume_Banking_Experience.docx"                            │ │
│ │ ✅ "Academic_CV_Research_Projects.pdf"                                  │ │
│ │ ✅ "Comprehensive_Career_History.txt"                                   │ │
│ │                                                                         │ │
│ │ AI will merge and deduplicate content automatically                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💾 **DATA STORAGE ARCHITECTURE**

### **Database Storage Implementation**

```python
# Master Dataset Storage Models
from sqlalchemy import Column, String, DateTime, Integer, Text, ARRAY, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserProfile(Base):
    """
    Main user profile containing master dataset
    """
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False)  # External user ID
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    location = Column(String(255))
    target_industries = Column(ARRAY(Text))  # ["Technology", "Finance"]
    career_level = Column(String(50))  # "senior", "mid", "entry"
    
    # Relationships
    work_experiences = relationship("WorkExperience", back_populates="profile")
    achievements = relationship("Achievement", back_populates="profile")
    education_entries = relationship("EducationEntry", back_populates="profile")
    skills = relationship("Skill", back_populates="profile")

class WorkExperience(Base):
    """
    Individual work experience entries
    """
    __tablename__ = "work_experiences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    
    company_name = Column(String(255), nullable=False)
    position_title = Column(String(255), nullable=False)
    employment_type = Column(String(50))  # "full-time", "internship", etc.
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)  # NULL for current position
    location = Column(String(255))
    company_size = Column(String(50))  # "startup", "enterprise", etc.
    industry = Column(String(100))
    role_summary = Column(Text)  # Brief description of role
    
    # Relationships
    profile = relationship("UserProfile", back_populates="work_experiences")
    achievements = relationship("Achievement", back_populates="experience")

class Achievement(Base):
    """
    Individual achievements within work experiences
    Core of the master dataset
    """
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    experience_id = Column(UUID(as_uuid=True), ForeignKey("work_experiences.id"))
    
    # Core achievement data
    achievement_text = Column(Text, nullable=False)  # Original description
    achievement_category = Column(String(100))  # "leadership", "technical", etc.
    impact_level = Column(Integer)  # 1-10 scale
    business_function = Column(String(100))  # "sales", "marketing", etc.
    
    # Quantified metrics (stored as JSON)
    quantified_metrics = Column(JSON)  # {"revenue": 650000000, "percentage": 25}
    
    # ATS and keyword optimization
    keywords = Column(ARRAY(Text))  # General keywords
    ats_keywords = Column(ARRAY(Text))  # Specific ATS-optimized keywords
    skills_demonstrated = Column(ARRAY(Text))  # Skills shown in this achievement
    
    # Context and verification
    time_period = Column(String(100))  # "Q1 2024", "6 months", etc.
    context_tags = Column(ARRAY(Text))  # ["remote", "international", "startup"]
    verification_status = Column(String(50), default="user_provided")
    
    # Performance tracking
    selection_count = Column(Integer, default=0)  # How often selected
    success_correlation = Column(Integer, default=0)  # Performance in applications
    
    # Relationships
    profile = relationship("UserProfile", back_populates="achievements")
    experience = relationship("WorkExperience", back_populates="achievements")
```

### **Storage Workflow Implementation**

```python
class MasterDatasetService:
    """
    Service for managing master dataset creation and storage
    """
    
    async def create_master_dataset_from_upload(
        self, 
        user_id: str, 
        uploaded_file: UploadFile
    ) -> MasterDatasetCreationResult:
        """
        Complete workflow: Upload → Parse → AI Analysis → Database Storage
        """
        
        try:
            # Step 1: Save uploaded file temporarily
            temp_file_path = await self._save_temp_file(uploaded_file)
            
            # Step 2: Parse document using enhanced parser
            parser = MasterDatasetParser()
            parsed_content = parser.parse_master_resume(temp_file_path, user_id)
            
            # Step 3: AI analysis for intelligent structuring
            ai_analysis = await self._ai_analyze_content(parsed_content)
            
            # Step 4: Create/update user profile
            user_profile = await self._create_or_update_profile(user_id, ai_analysis.contact_info)
            
            # Step 5: Store work experiences
            work_experiences = []
            for exp_data in ai_analysis.work_experiences:
                work_exp = await self._store_work_experience(user_profile.id, exp_data)
                work_experiences.append(work_exp)
                
                # Store individual achievements for this experience
                for achievement_data in exp_data.achievements:
                    await self._store_achievement(
                        user_profile.id, 
                        work_exp.id, 
                        achievement_data
                    )
            
            # Step 6: Store education, skills, projects
            await self._store_education_entries(user_profile.id, ai_analysis.education)
            await self._store_skills(user_profile.id, ai_analysis.skills)
            await self._store_projects(user_profile.id, ai_analysis.projects)
            
            # Step 7: Generate summary and recommendations
            summary = await self._generate_dataset_summary(user_profile.id)
            
            return MasterDatasetCreationResult(
                success=True,
                user_profile_id=user_profile.id,
                total_achievements=len(ai_analysis.all_achievements),
                work_experiences_count=len(work_experiences),
                summary=summary,
                recommendations=await self._generate_improvement_recommendations(user_profile.id)
            )
            
        except Exception as e:
            logger.error(f"Master dataset creation failed: {str(e)}")
            raise MasterDatasetCreationError(f"Failed to create master dataset: {str(e)}")
        
        finally:
            # Cleanup temporary files
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
    
    async def _ai_analyze_content(self, parsed_content: ParsedContent) -> AIAnalysisResult:
        """
        Use Gemini AI to intelligently analyze and structure content
        """
        from app.services.gemini_client import GeminiClient
        
        gemini_client = GeminiClient()
        
        # Enhanced AI prompt for comprehensive analysis
        analysis_prompt = self._build_comprehensive_analysis_prompt(parsed_content)
        
        # Get AI analysis with structured response
        ai_response = await gemini_client.analyze_with_structured_output(
            prompt=analysis_prompt,
            expected_format="detailed_resume_analysis"
        )
        
        return self._parse_ai_structured_response(ai_response)
    
    async def _store_achievement(
        self, 
        profile_id: UUID, 
        experience_id: UUID, 
        achievement_data: AchievementData
    ) -> Achievement:
        """
        Store individual achievement with full metadata
        """
        achievement = Achievement(
            profile_id=profile_id,
            experience_id=experience_id,
            achievement_text=achievement_data.text,
            achievement_category=achievement_data.category,
            impact_level=achievement_data.impact_level,
            business_function=achievement_data.business_function,
            quantified_metrics=achievement_data.metrics,
            keywords=achievement_data.keywords,
            ats_keywords=achievement_data.ats_keywords,
            skills_demonstrated=achievement_data.skills,
            time_period=achievement_data.time_period,
            context_tags=achievement_data.context_tags
        )
        
        db.session.add(achievement)
        await db.session.commit()
        
        return achievement
```

---

## 🔄 **CONTINUOUS ENHANCEMENT WORKFLOW**

### **Ongoing Dataset Improvement**

```python
class DatasetEnhancementService:
    """
    Continuous improvement of master dataset quality
    """
    
    async def suggest_missing_achievements(self, user_profile_id: UUID) -> List[AchievementSuggestion]:
        """
        AI analysis to suggest potentially missing achievements
        """
        user_profile = await self._get_user_profile(user_profile_id)
        existing_achievements = await self._get_all_achievements(user_profile_id)
        
        # AI prompt to identify gaps
        gap_analysis_prompt = f"""
        Based on this user's work history and existing achievements, suggest additional achievements 
        they might have accomplished but haven't documented:
        
        WORK HISTORY: {user_profile.work_experiences}
        EXISTING ACHIEVEMENTS: {existing_achievements}
        
        Look for common achievements in similar roles that might be missing:
        - Leadership activities
        - Process improvements  
        - Training or mentoring
        - Cost savings or efficiency gains
        - Client relationships or customer satisfaction
        - Technical implementations
        - Team collaborations
        
        Suggest specific, realistic achievements they likely accomplished.
        """
        
        suggestions = await self.ai_client.generate_suggestions(gap_analysis_prompt)
        return self._format_achievement_suggestions(suggestions)
    
    async def enhance_achievement_quality(self, achievement_id: UUID) -> AchievementEnhancement:
        """
        AI-powered suggestions to improve achievement descriptions
        """
        achievement = await self._get_achievement(achievement_id)
        
        enhancement_prompt = f"""
        Improve this achievement for better ATS optimization and impact:
        
        ORIGINAL: {achievement.achievement_text}
        CONTEXT: {achievement.experience.position_title} at {achievement.experience.company_name}
        IMPACT LEVEL: {achievement.impact_level}/10
        
        Suggest improvements for:
        1. Stronger action verbs
        2. More specific quantified results
        3. Better ATS keywords
        4. Clearer impact statement
        5. Industry-relevant terminology
        
        Maintain authenticity - only suggest realistic enhancements.
        """
        
        enhancement = await self.ai_client.enhance_content(enhancement_prompt)
        return self._format_enhancement_suggestion(enhancement, achievement)
```

---

## 📊 **STORAGE PERFORMANCE & SCALABILITY**

### **Database Optimization Strategy**

```sql
-- Optimized indexing for master dataset queries
CREATE INDEX idx_achievements_profile_id ON achievements(profile_id);
CREATE INDEX idx_achievements_category ON achievements(achievement_category);
CREATE INDEX idx_achievements_impact_level ON achievements(impact_level);
CREATE INDEX idx_achievements_keywords ON achievements USING GIN(keywords);
CREATE INDEX idx_achievements_selection_performance ON achievements(selection_count, success_correlation);

-- Compound indexes for common query patterns
CREATE INDEX idx_work_exp_profile_dates ON work_experiences(profile_id, start_date, end_date);
CREATE INDEX idx_achievements_profile_experience ON achievements(profile_id, experience_id);

-- Full-text search indexes for content matching
CREATE INDEX idx_achievements_text_search ON achievements USING GIN(to_tsvector('english', achievement_text));
```

### **Caching Strategy**

```python
# Redis caching for frequently accessed master datasets
@cache(expire=3600)  # 1 hour cache
async def get_user_master_dataset(user_profile_id: UUID) -> CachedMasterDataset:
    """
    Cached retrieval of complete master dataset for user
    """
    return await MasterDatasetService.get_complete_dataset(user_profile_id)

@cache(expire=1800)  # 30 minute cache  
async def get_achievement_selection_scores(user_profile_id: UUID, job_keywords: List[str]) -> Dict[UUID, float]:
    """
    Cached relevance scores for achievements against specific job requirements
    """
    return await ContentSelectionEngine.calculate_all_scores(user_profile_id, job_keywords)
```

This comprehensive input and storage system provides users with flexible options to build their master dataset while ensuring intelligent AI-powered structuring and optimized database storage for fast retrieval and selection algorithms.