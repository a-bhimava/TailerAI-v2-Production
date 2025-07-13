# Enhanced Master Dataset Schema for TailerAI v2.0

## 🎯 **Updated Strategy: Intelligent Content Selection from Comprehensive Work History**

Based on customer behavior analysis and the existing system architecture, this enhanced schema focuses on creating a comprehensive workplace dataset that enables AI-powered selection of optimal content for ATS-optimized, one-page resumes.

---

## 📊 **ENHANCED DATABASE SCHEMA**

### **Core Master Dataset Tables**

```sql
-- User Profiles with Master Dataset
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL, -- External user identifier
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    location VARCHAR(255),
    target_industries TEXT[], -- Array of preferred industries
    career_level VARCHAR(50), -- 'entry', 'mid', 'senior', 'executive'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comprehensive Work Experience Database
CREATE TABLE work_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    position_title VARCHAR(255) NOT NULL,
    employment_type VARCHAR(50), -- 'full-time', 'part-time', 'contract', 'internship'
    start_date DATE NOT NULL,
    end_date DATE, -- NULL for current position
    location VARCHAR(255),
    company_size VARCHAR(50), -- 'startup', 'small', 'medium', 'large', 'enterprise'
    industry VARCHAR(100),
    company_description TEXT,
    role_summary TEXT, -- Brief description of the role
    reporting_structure VARCHAR(255), -- Who they reported to
    team_size INTEGER, -- Size of team managed/worked with
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Granular Achievement Database (Core of Master Dataset)
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id UUID REFERENCES work_experiences(id) ON DELETE CASCADE,
    achievement_text TEXT NOT NULL, -- Original achievement description
    achievement_category VARCHAR(100), -- 'leadership', 'technical', 'financial', 'process', 'growth'
    quantified_metrics JSONB, -- {"revenue": 650000000, "percentage": 25, "team_size": 45}
    impact_level INTEGER CHECK (impact_level >= 1 AND impact_level <= 10), -- 1-10 scale
    business_function VARCHAR(100), -- 'sales', 'marketing', 'operations', 'finance', 'hr'
    keywords TEXT[], -- Extracted keywords for matching
    skills_demonstrated TEXT[], -- Skills showcased in this achievement
    tools_technologies TEXT[], -- Tools/tech used
    time_period VARCHAR(100), -- 'Q1 2024', 'FY 2023', '6 months'
    verification_status VARCHAR(50) DEFAULT 'user_provided', -- 'verified', 'user_provided'
    ats_keywords TEXT[], -- Specific ATS-friendly keywords
    context_tags TEXT[], -- Additional context: 'remote', 'international', 'startup'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievement Performance Tracking
CREATE TABLE achievement_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    achievement_id UUID REFERENCES achievements(id) ON DELETE CASCADE,
    job_application_id UUID, -- Links to job applications where this was used
    selection_frequency INTEGER DEFAULT 0, -- How often this achievement is selected
    success_correlation DECIMAL(3,2), -- Correlation with successful applications (0-1)
    last_selected_at TIMESTAMP,
    performance_score DECIMAL(5,2), -- Calculated performance score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Education & Certifications
CREATE TABLE education_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    institution_name VARCHAR(255) NOT NULL,
    degree_type VARCHAR(100), -- 'Bachelor', 'Master', 'PhD', 'Certificate'
    field_of_study VARCHAR(255),
    specialization VARCHAR(255),
    start_date DATE,
    end_date DATE,
    gpa DECIMAL(3,2),
    gpa_scale DECIMAL(3,2) DEFAULT 4.0,
    honors TEXT[], -- Dean's list, magna cum laude, etc.
    relevant_coursework TEXT[],
    thesis_topic TEXT,
    education_achievements TEXT[], -- Academic achievements, awards
    is_relevant_to_target BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills & Competencies with Proficiency Tracking
CREATE TABLE skills_competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    skill_category VARCHAR(50), -- 'technical', 'soft', 'industry', 'language'
    skill_subcategory VARCHAR(100), -- 'programming', 'data_analysis', 'leadership'
    proficiency_level INTEGER CHECK (proficiency_level >= 1 AND proficiency_level <= 10),
    years_experience DECIMAL(3,1),
    last_used_date DATE,
    learning_source VARCHAR(100), -- 'work', 'education', 'certification', 'self-taught'
    certifications TEXT[], -- Related certifications
    endorsements INTEGER DEFAULT 0, -- LinkedIn-style endorsements
    skill_keywords TEXT[], -- Alternative names/keywords for this skill
    industry_relevance TEXT[], -- Industries where this skill is valuable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects & Initiatives (Side projects, volunteer work)
CREATE TABLE projects_initiatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(100), -- 'professional', 'side_project', 'volunteer', 'academic'
    description TEXT,
    role_in_project VARCHAR(255),
    start_date DATE,
    end_date DATE,
    project_url VARCHAR(500),
    github_repo VARCHAR(500),
    technologies_used TEXT[],
    team_size INTEGER,
    project_outcomes TEXT[], -- Specific outcomes/achievements
    skills_developed TEXT[],
    impact_metrics JSONB, -- {"users": 1000, "downloads": 5000}
    is_featured BOOLEAN DEFAULT false, -- Whether to highlight this project
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Job Application & Content Selection Tables**

```sql
-- Job Applications with AI Selection History
CREATE TABLE job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    job_description TEXT,
    job_requirements TEXT[],
    preferred_qualifications TEXT[],
    industry VARCHAR(100),
    job_level VARCHAR(50),
    salary_range VARCHAR(100),
    location VARCHAR(255),
    application_date TIMESTAMP,
    application_status VARCHAR(50), -- 'applied', 'interviewed', 'rejected', 'offer'
    ats_score INTEGER, -- Calculated ATS compatibility score
    keyword_match_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Selected Content for Each Application
CREATE TABLE application_content_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_application_id UUID REFERENCES job_applications(id) ON DELETE CASCADE,
    selected_achievements UUID[], -- Array of achievement IDs
    selected_experiences UUID[], -- Array of experience IDs to include
    selected_projects UUID[], -- Array of project IDs
    selected_skills UUID[], -- Array of skill IDs
    content_selection_algorithm VARCHAR(50), -- Version of selection algorithm used
    relevance_scores JSONB, -- Detailed scoring for each selected item
    one_page_constraint_met BOOLEAN,
    total_content_score DECIMAL(6,2),
    manual_overrides JSONB, -- User manual selections/deselections
    ai_rationale TEXT, -- AI explanation for content selection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Selection Rules & Preferences
CREATE TABLE selection_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    preference_type VARCHAR(100), -- 'industry', 'role_type', 'content_priority'
    preference_value VARCHAR(255),
    weight DECIMAL(3,2), -- Weight in selection algorithm (0-1)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **AI Analysis & Optimization Tables**

```sql
-- Job Description Analysis Cache
CREATE TABLE job_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_description_hash VARCHAR(64) UNIQUE, -- Hash of job description for caching
    extracted_keywords TEXT[],
    required_skills TEXT[],
    preferred_skills TEXT[],
    industry_classification VARCHAR(100),
    role_level VARCHAR(50),
    key_responsibilities TEXT[],
    company_culture_indicators TEXT[],
    ats_keywords TEXT[], -- Keywords specifically for ATS optimization
    analysis_version VARCHAR(50), -- Version of analysis algorithm
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Optimization Suggestions
CREATE TABLE optimization_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(100), -- 'achievement_enhancement', 'keyword_integration', 'content_addition'
    target_content_id UUID, -- ID of achievement/experience to optimize
    original_content TEXT,
    suggested_content TEXT,
    improvement_rationale TEXT,
    estimated_impact_score DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🤖 **ENHANCED SELECTION ALGORITHMS**

### **1. Multi-Dimensional Relevance Scoring**

```python
def calculate_comprehensive_relevance_score(achievement, job_analysis, user_preferences):
    """
    Enhanced scoring algorithm considering multiple factors
    """
    score_components = {
        'keyword_match': 0.0,
        'industry_relevance': 0.0,
        'role_similarity': 0.0,
        'impact_magnitude': 0.0,
        'recency_factor': 0.0,
        'user_preference': 0.0,
        'performance_history': 0.0
    }
    
    # Keyword Matching (35% weight) - Enhanced with semantic similarity
    keyword_score = calculate_semantic_keyword_match(
        achievement.keywords + achievement.ats_keywords,
        job_analysis.extracted_keywords + job_analysis.ats_keywords
    )
    score_components['keyword_match'] = keyword_score * 0.35
    
    # Industry Relevance (20% weight)
    industry_score = calculate_industry_alignment(
        achievement.context_tags,
        job_analysis.industry_classification
    )
    score_components['industry_relevance'] = industry_score * 0.20
    
    # Role Similarity (15% weight)
    role_score = calculate_role_function_similarity(
        achievement.business_function,
        job_analysis.role_level,
        job_analysis.key_responsibilities
    )
    score_components['role_similarity'] = role_score * 0.15
    
    # Impact Magnitude (15% weight)
    impact_score = normalize_impact_score(achievement.impact_level, achievement.quantified_metrics)
    score_components['impact_magnitude'] = impact_score * 0.15
    
    # Recency Factor (5% weight) - More recent achievements scored higher
    recency_score = calculate_recency_factor(achievement.time_period)
    score_components['recency_factor'] = recency_score * 0.05
    
    # User Preferences (5% weight)
    preference_score = apply_user_preferences(achievement, user_preferences)
    score_components['user_preference'] = preference_score * 0.05
    
    # Historical Performance (5% weight) - How well this achievement performed before
    performance_score = get_achievement_performance_score(achievement.id)
    score_components['performance_history'] = performance_score * 0.05
    
    total_score = sum(score_components.values())
    
    return {
        'total_score': total_score,
        'components': score_components,
        'confidence': calculate_scoring_confidence(score_components)
    }
```

### **2. One-Page Optimization with Content Density**

```python
def optimize_for_one_page_constraint(scored_content, target_length=3500):
    """
    Knapsack optimization considering both relevance and content density
    """
    # Calculate content density score (relevance per character)
    for item in scored_content:
        char_count = len(item.achievement_text)
        item.density_score = item.relevance_score / max(char_count, 1)
        item.character_count = char_count
    
    # Dynamic programming approach for optimal selection
    selected_content = knapsack_with_density_optimization(
        items=scored_content,
        capacity_constraint=target_length,
        value_function=lambda x: x.relevance_score,
        weight_function=lambda x: x.character_count,
        density_bonus=True
    )
    
    return selected_content
```

### **3. ATS Optimization Engine**

```python
def optimize_for_ats_compatibility(selected_content, job_analysis):
    """
    Ensure optimal ATS keyword density and placement
    """
    ats_optimization = {
        'keyword_coverage': calculate_keyword_coverage(selected_content, job_analysis.ats_keywords),
        'keyword_density': calculate_optimal_density(selected_content),
        'section_distribution': optimize_keyword_placement(selected_content),
        'readability_score': assess_content_readability(selected_content)
    }
    
    # Suggest adjustments if needed
    if ats_optimization['keyword_coverage'] < 0.7:
        ats_optimization['suggestions'] = generate_keyword_enhancement_suggestions(
            selected_content, job_analysis.ats_keywords
        )
    
    return ats_optimization
```

---

## 🎛️ **ENHANCED USER EXPERIENCE DESIGN**

### **Master Dataset Dashboard Interface**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎯 MASTER RESUME DATASET - Comprehensive Work History                     │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 PORTFOLIO OVERVIEW                                                   │ │
│ │ Total Experiences: 4 | Achievements: 28 | Success Rate: 73%           │ │
│ │ Most Successful Content: Financial Impact Achievements                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏢 ICICI BANK - Manager, Corporate Banking (04/23-11/24)              │ │
│ │                                                                         │ │
│ │ 🎯 High-Impact Achievements (Selected: 3/6)                           │ │
│ │ ✅ Managed portfolio worth $650M [IMPACT: 10/10] [USED: 8 times]      │ │
│ │ ✅ Increased portfolio by $185M in FY 2024 [IMPACT: 9/10]             │ │
│ │ ✅ Delivered 26 C-Suite presentations [IMPACT: 7/10]                   │ │
│ │ ⭕ Reduced turnaround time by 25% [IMPACT: 8/10] [NEVER USED]          │ │
│ │ ⭕ Led cross-functional team of 12 members [IMPACT: 6/10]              │ │
│ │ ⭕ Implemented new CRM system [IMPACT: 5/10]                           │ │
│ │                                                                         │ │
│ │ 🔧 Skills Developed: Financial Analysis, Team Leadership, CRM          │ │
│ │ 🏷️ Tags: Finance, B2B, Enterprise, Leadership, Sales                   │ │
│ │ [+ Add Achievement] [Edit Experience] [Performance Analytics]           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏢 GALDERMA - Marketing Intern (04/22-07/22)                          │ │
│ │                                                                         │ │
│ │ 🎯 High-Impact Achievements (Selected: 2/4)                           │ │
│ │ ✅ Conducted 900 interviews, 10 focus groups [IMPACT: 9/10]           │ │
│ │ ✅ Reduced reconciliation time by 3600% [IMPACT: 8/10]                │ │
│ │ ⭕ Launched campaign achieving 2-3.5% market share [IMPACT: 7/10]      │ │
│ │ ⭕ Created market analysis dashboard [IMPACT: 6/10]                     │ │
│ │                                                                         │ │
│ │ 🔧 Skills: Market Research, Data Analysis, Process Improvement         │ │
│ │ 🏷️ Tags: Marketing, Healthcare, Internship, Analytics                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [+ Add New Experience] [Import from LinkedIn] [Bulk Achievement Import]    │
│ [Content Performance Analytics] [AI Content Suggestions]                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Intelligent Content Selection Interface**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎯 AI CONTENT SELECTION - Senior Product Manager at Google                │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 JOB ANALYSIS SUMMARY                                                 │ │
│ │ Industry: Technology | Level: Senior | Keywords: 47 identified         │ │
│ │ Key Requirements: Product Strategy, Data Analysis, Team Leadership      │ │
│ │ ATS Keywords: product management, analytics, stakeholder, roadmap       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🤖 AI SELECTION RESULTS (Content Length: 3,247 chars - ✅ One Page)   │ │
│ │                                                                         │ │
│ │ ✅ SELECTED (Score: 94/100) 🏆 TOP PERFORMER                          │ │
│ │ "Managed portfolio worth $650M comprising 45 corporations"             │ │
│ │ 💡 Why: Financial scale + management keywords (portfolio, managed)     │ │
│ │ 🎯 Matches: "portfolio management", "large scale operations"           │ │
│ │                                                                         │ │
│ │ ✅ SELECTED (Score: 89/100)                                            │ │
│ │ "Conducted 900 interviews, 10 focus groups for market research"        │ │
│ │ 💡 Why: Data-driven approach + user research relevance                 │ │
│ │ 🎯 Matches: "user research", "data analysis", "market insights"       │ │
│ │                                                                         │ │
│ │ ✅ SELECTED (Score: 86/100)                                            │ │
│ │ "Reduced reconciliation time by 3600% through process automation"      │ │
│ │ 💡 Why: Process improvement + quantified impact                        │ │
│ │ 🎯 Matches: "process optimization", "efficiency", "automation"         │ │
│ │                                                                         │ │
│ │ ❌ NOT SELECTED (Score: 34/100)                                        │ │
│ │ "World Top 15 teams in Underwater Vehicle Competition"                 │ │
│ │ 💡 Why: Low relevance to product management; academic achievement       │ │
│ │ ⚡ Override: [Force Include] [Never Show for PM roles]                │ │
│ │                                                                         │ │
│ │ ❌ NOT SELECTED (Score: 28/100)                                        │ │
│ │ "Organized cultural events for 500+ participants"                      │ │
│ │ 💡 Why: Event management not relevant; space constraint                │ │
│ │                                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 📈 OPTIMIZATION INSIGHTS                                                │ │
│ │ ATS Score: 87/100 | Keyword Coverage: 73% | Readability: A+           │ │
│ │ 🔥 Strengths: Strong quantified results, industry-relevant experience  │ │
│ │ ⚠️  Suggestions: Consider adding "stakeholder management" keywords     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Generate Resume] [Manual Content Review] [Save Selection Profile]         │
│ [Performance Prediction] [Alternative Selections] [Export Analysis]        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 **IMPLEMENTATION ROADMAP**

### **Phase 1: Enhanced Database Foundation (Week 3)**
- [ ] Implement enhanced SQLAlchemy models
- [ ] Create comprehensive migration scripts  
- [ ] Build master dataset seeding utilities
- [ ] Add performance tracking tables

### **Phase 2: Intelligent Selection Engine (Week 4)**
- [ ] Develop multi-dimensional scoring algorithms
- [ ] Implement semantic keyword matching
- [ ] Create one-page optimization solver
- [ ] Build ATS compatibility engine

### **Phase 3: User Experience Enhancement (Week 5)**
- [ ] Create master dataset management interface
- [ ] Build content selection transparency dashboard
- [ ] Implement performance analytics
- [ ] Add AI content suggestions

### **Phase 4: Integration & Intelligence (Week 6)**
- [ ] Connect selection engine to LaTeX generation
- [ ] Implement learning from application outcomes
- [ ] Add predictive success modeling
- [ ] Create comprehensive testing suite

---

This enhanced schema transforms TailerAI v2.0 into a comprehensive career intelligence platform that learns from user success patterns and optimizes content selection for maximum impact while maintaining authenticity and ATS compatibility.