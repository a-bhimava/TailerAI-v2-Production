"""
Achievement Semantic Categorization Service for TailerAI v2.0.
Uses Gemini AI to automatically categorize achievements with semantic tags.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from enum import Enum

from app.services.gemini_client import GeminiClient, GeminiResponse
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AchievementCategory(str, Enum):
    """Standard achievement categories for semantic tagging."""
    TECHNICAL = "technical"           # Technical implementations, systems, coding
    LEADERSHIP = "leadership"         # Team management, mentoring, decision-making
    FINANCIAL = "financial"          # Revenue, cost savings, budget management
    OPERATIONAL = "operational"      # Process improvements, efficiency gains
    STRATEGIC = "strategic"          # Planning, vision, business development
    COMMUNICATION = "communication"  # Presentations, documentation, stakeholder management
    ANALYTICAL = "analytical"        # Data analysis, research, insights
    CREATIVE = "creative"           # Design, innovation, problem-solving
    CUSTOMER = "customer"           # Customer service, satisfaction, relations
    COMPLIANCE = "compliance"       # Regulatory, quality assurance, standards


class BusinessFunction(str, Enum):
    """Standard business functions for achievement classification."""
    ENGINEERING = "engineering"
    PRODUCT = "product"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    HR = "human_resources"
    LEGAL = "legal"
    CUSTOMER_SUCCESS = "customer_success"
    DATA_SCIENCE = "data_science"
    DESIGN = "design"
    GENERAL = "general"


class AchievementCategorizationService:
    """
    Service for automatically categorizing achievements using AI semantic analysis.
    """
    
    def __init__(self):
        self.logger = logger
        self.gemini_client = None
        self.use_ai_categorization = getattr(settings, 'enable_ai_content_selection', False)
        
        # Initialize Gemini client if available
        if self.use_ai_categorization:
            try:
                self.gemini_client = GeminiClient()
                if not self.gemini_client.is_available():
                    self.use_ai_categorization = False
                    logger.warning("Gemini client not available for achievement categorization")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client for categorization: {e}")
                self.use_ai_categorization = False
    
    async def categorize_achievement(
        self, 
        achievement_text: str, 
        work_context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        Categorize an achievement using AI analysis.
        
        Args:
            achievement_text: The achievement description
            work_context: Optional context about the role/company
            
        Returns:
            Tuple of (category, business_function, confidence_score)
        """
        try:
            if self.use_ai_categorization and self.gemini_client:
                return await self._ai_categorization(achievement_text, work_context)
            else:
                return self._rule_based_categorization(achievement_text)
                
        except Exception as e:
            logger.error(f"Achievement categorization failed: {e}")
            return self._rule_based_categorization(achievement_text)
    
    async def _ai_categorization(
        self, 
        achievement_text: str, 
        work_context: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """Use Gemini AI for sophisticated achievement categorization."""
        
        context_part = f"\\nWork Context: {work_context}" if work_context else ""
        
        prompt = f"""Analyze this professional achievement and categorize it semantically.

Achievement: "{achievement_text}"{context_part}

Please categorize this achievement using these dimensions:

**Achievement Categories:**
- technical: Technical implementations, coding, system architecture
- leadership: Team management, mentoring, decision-making, influence
- financial: Revenue generation, cost savings, budget management
- operational: Process improvements, efficiency gains, workflow optimization
- strategic: Planning, vision, business development, market analysis
- communication: Presentations, documentation, stakeholder management
- analytical: Data analysis, research, insights, problem-solving
- creative: Design, innovation, creative problem-solving
- customer: Customer service, satisfaction, relationship management
- compliance: Regulatory, quality assurance, standards, governance

**Business Functions:**
- engineering: Software development, technical systems
- product: Product management, development, strategy
- sales: Revenue generation, client acquisition
- marketing: Brand, campaigns, lead generation
- operations: Business operations, logistics, efficiency
- finance: Financial management, analysis, planning
- human_resources: HR, recruiting, employee development
- data_science: Analytics, ML, data insights
- design: UX/UI, creative design, user experience
- customer_success: Customer support, success, retention
- general: Cross-functional or general business

Respond with JSON only:
{{
  "category": "selected_category",
  "business_function": "selected_function", 
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this categorization fits"
}}"""

        try:
            response = await self.gemini_client.generate_content(prompt)
            
            if response.success:
                import json
                result = json.loads(response.content.strip())
                
                category = result.get('category', 'operational')
                business_function = result.get('business_function', 'general')
                confidence = result.get('confidence', 0.8)
                reasoning = result.get('reasoning', '')
                
                # Validate categories
                if category not in [cat.value for cat in AchievementCategory]:
                    category = 'operational'
                if business_function not in [func.value for func in BusinessFunction]:
                    business_function = 'general'
                
                logger.info(f"AI categorization: {category}/{business_function} (confidence: {confidence})")
                logger.info(f"Reasoning: {reasoning}")
                
                return category, business_function, confidence
            else:
                logger.warning("AI categorization failed, falling back to rule-based")
                return self._rule_based_categorization(achievement_text)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI categorization response: {e}")
            return self._rule_based_categorization(achievement_text)
        except Exception as e:
            logger.error(f"AI categorization error: {e}")
            return self._rule_based_categorization(achievement_text)
    
    def _rule_based_categorization(self, achievement_text: str) -> Tuple[str, str, float]:
        """Fallback rule-based categorization using keyword matching."""
        
        text_lower = achievement_text.lower()
        
        # Define keyword patterns for categories
        category_patterns = {
            AchievementCategory.TECHNICAL: [
                'developed', 'built', 'implemented', 'coded', 'programmed', 'architected',
                'system', 'software', 'api', 'database', 'algorithm', 'framework',
                'microservices', 'docker', 'kubernetes', 'cloud', 'aws', 'gcp'
            ],
            AchievementCategory.LEADERSHIP: [
                'led', 'managed', 'mentored', 'coached', 'supervised', 'directed',
                'team', 'leadership', 'guided', 'influenced', 'collaborated'
            ],
            AchievementCategory.FINANCIAL: [
                'revenue', 'sales', 'profit', 'cost', 'budget', 'savings', 'roi',
                'million', 'thousand', '$', 'financial', 'money', 'investment'
            ],
            AchievementCategory.OPERATIONAL: [
                'improved', 'optimized', 'streamlined', 'enhanced', 'reduced',
                'process', 'efficiency', 'workflow', 'operations', 'productivity'
            ],
            AchievementCategory.ANALYTICAL: [
                'analyzed', 'data', 'metrics', 'insights', 'research', 'study',
                'investigation', 'findings', 'correlation', 'trends'
            ],
            AchievementCategory.CUSTOMER: [
                'customer', 'client', 'user', 'satisfaction', 'service', 'support',
                'experience', 'feedback', 'retention', 'engagement'
            ]
        }
        
        # Function patterns
        function_patterns = {
            BusinessFunction.ENGINEERING: [
                'software', 'development', 'coding', 'programming', 'technical',
                'system', 'architecture', 'api', 'database', 'infrastructure'
            ],
            BusinessFunction.PRODUCT: [
                'product', 'feature', 'roadmap', 'requirements', 'user stories',
                'stakeholder', 'launch', 'strategy'
            ],
            BusinessFunction.SALES: [
                'sales', 'revenue', 'client', 'deal', 'quota', 'pipeline',
                'prospect', 'conversion', 'account'
            ],
            BusinessFunction.MARKETING: [
                'marketing', 'campaign', 'brand', 'content', 'social media',
                'lead generation', 'awareness', 'engagement'
            ],
            BusinessFunction.DATA_SCIENCE: [
                'machine learning', 'ml', 'ai', 'data science', 'analytics',
                'model', 'prediction', 'algorithm', 'statistical'
            ]
        }
        
        # Score categories
        category_scores = {}
        for category, keywords in category_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        # Score functions
        function_scores = {}
        for function, keywords in function_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                function_scores[function] = score
        
        # Select best matches
        best_category = max(category_scores, key=category_scores.get) if category_scores else AchievementCategory.OPERATIONAL
        best_function = max(function_scores, key=function_scores.get) if function_scores else BusinessFunction.GENERAL
        
        # Calculate confidence based on keyword matches
        max_category_score = category_scores.get(best_category, 0)
        max_function_score = function_scores.get(best_function, 0)
        confidence = min(0.9, 0.5 + (max_category_score + max_function_score) * 0.1)
        
        logger.info(f"Rule-based categorization: {best_category.value}/{best_function.value} (confidence: {confidence})")
        
        return best_category.value, best_function.value, confidence
    
    async def categorize_multiple_achievements(
        self, 
        achievements: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Categorize multiple achievements efficiently.
        
        Args:
            achievements: List of dicts with 'text' and optional 'context' keys
            
        Returns:
            List of dicts with categorization results added
        """
        results = []
        
        for achievement in achievements:
            text = achievement.get('text', '')
            context = achievement.get('context', '')
            
            category, business_function, confidence = await self.categorize_achievement(text, context)
            
            result = achievement.copy()
            result.update({
                'category': category,
                'business_function': business_function,
                'confidence': confidence
            })
            results.append(result)
            
            # Small delay to avoid rate limiting
            if self.use_ai_categorization:
                await asyncio.sleep(0.1)
        
        return results
    
    def get_category_description(self, category: str) -> str:
        """Get human-readable description of a category."""
        descriptions = {
            'technical': 'Technical implementations and system development',
            'leadership': 'Team management and organizational influence',
            'financial': 'Revenue generation and cost management',
            'operational': 'Process improvements and efficiency gains',
            'strategic': 'Business planning and strategic initiatives',
            'communication': 'Information sharing and stakeholder engagement',
            'analytical': 'Data analysis and research insights',
            'creative': 'Innovation and creative problem-solving',
            'customer': 'Customer relationship and satisfaction management',
            'compliance': 'Regulatory and quality assurance activities'
        }
        return descriptions.get(category, 'General professional achievement')
    
    def get_all_categories(self) -> List[Dict[str, str]]:
        """Get all available categories with descriptions."""
        return [
            {'value': cat.value, 'label': cat.value.title(), 'description': self.get_category_description(cat.value)}
            for cat in AchievementCategory
        ]
    
    def get_all_business_functions(self) -> List[Dict[str, str]]:
        """Get all available business functions."""
        return [
            {'value': func.value, 'label': func.value.replace('_', ' ').title()}
            for func in BusinessFunction
        ]


# Global service instance
_categorization_service = None

def get_categorization_service() -> AchievementCategorizationService:
    """Get the global categorization service instance."""
    global _categorization_service
    if _categorization_service is None:
        _categorization_service = AchievementCategorizationService()
    return _categorization_service