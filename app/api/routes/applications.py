#!/usr/bin/env python3
"""
Application Management API routes for TailerAI v2.0 - PRD-011: Personal Application Management

Personal job application tracking endpoints for individual users.
Provides comprehensive application lifecycle management, analytics, and follow-up tracking.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field, validator

from app.api.dependencies.auth_deps import get_current_user
from app.models.database import User
from app.services.application_management_service import get_application_management_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/applications", tags=["applications"])


# Request/Response Models

class CreateApplicationRequest(BaseModel):
    """Create job application request model."""
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    position_title: str = Field(..., min_length=1, max_length=255, description="Job position title")
    job_board_url: Optional[str] = Field(None, max_length=1000, description="Job posting URL")
    job_board_source: Optional[str] = Field("direct", description="Job board source")
    application_method: Optional[str] = Field("online", description="Application method")
    cover_letter_used: bool = Field(False, description="Whether cover letter was used")
    resume_version_used: Optional[str] = Field(None, description="Resume version identifier")
    recruiter_name: Optional[str] = Field(None, max_length=255, description="Recruiter name")
    recruiter_email: Optional[str] = Field(None, max_length=255, description="Recruiter email")
    recruiter_phone: Optional[str] = Field(None, max_length=50, description="Recruiter phone")
    hr_contact: Optional[str] = Field(None, max_length=255, description="HR contact")
    salary_range_min: Optional[int] = Field(None, ge=0, description="Minimum salary range")
    salary_range_max: Optional[int] = Field(None, ge=0, description="Maximum salary range")
    personal_interest_level: int = Field(5, ge=1, le=10, description="Interest level (1-10)")
    benefits_notes: Optional[str] = Field(None, description="Benefits notes")
    company_culture_notes: Optional[str] = Field(None, description="Company culture notes")
    application_date: Optional[datetime] = Field(None, description="Application date")
    
    @validator('job_board_source')
    def validate_job_board_source(cls, v):
        valid_sources = ["linkedin", "indeed", "glassdoor", "company_website", "referral", "direct", "other"]
        if v and v not in valid_sources:
            raise ValueError(f"Job board source must be one of: {valid_sources}")
        return v
    
    @validator('application_method')
    def validate_application_method(cls, v):
        valid_methods = ["online", "email", "referral", "in_person", "other"]
        if v and v not in valid_methods:
            raise ValueError(f"Application method must be one of: {valid_methods}")
        return v


class UpdateStatusRequest(BaseModel):
    """Update application status request model."""
    new_status: str = Field(..., description="New application status")
    event_description: Optional[str] = Field(None, description="Description of status change")
    interview_notes: Optional[str] = Field(None, description="Interview notes")
    next_interview_date: Optional[datetime] = Field(None, description="Next interview date")
    outcome_reason: Optional[str] = Field(None, description="Outcome reason or feedback")
    follow_up_date: Optional[datetime] = Field(None, description="Next follow-up date")
    
    @validator('new_status')
    def validate_status(cls, v):
        valid_statuses = [
            "applied", "screening", "phone_screen", "technical_interview",
            "on_site_interview", "final_interview", "offer", "rejected",
            "withdrawn", "no_response"
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class AddEventRequest(BaseModel):
    """Add application event request model."""
    event_type: str = Field(..., description="Event type")
    event_description: str = Field(..., description="Event description")
    event_date: Optional[datetime] = Field(None, description="Event date")
    contact_person: Optional[str] = Field(None, description="Contact person")
    contact_method: Optional[str] = Field(None, description="Contact method")
    outcome: Optional[str] = Field("neutral", description="Event outcome")
    next_steps: Optional[str] = Field(None, description="Next steps")
    follow_up_required: bool = Field(False, description="Follow-up required")
    follow_up_date: Optional[datetime] = Field(None, description="Follow-up date")
    
    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = [
            "application_sent", "response_received", "phone_call", "email_sent",
            "interview_scheduled", "interview_completed", "follow_up_sent",
            "reference_check", "offer_received", "offer_negotiation", "decision_made"
        ]
        if v not in valid_types:
            raise ValueError(f"Event type must be one of: {valid_types}")
        return v
    
    @validator('outcome')
    def validate_outcome(cls, v):
        valid_outcomes = ["positive", "negative", "neutral", "pending"]
        if v and v not in valid_outcomes:
            raise ValueError(f"Outcome must be one of: {valid_outcomes}")
        return v


class ApplicationResponse(BaseModel):
    """Application response model."""
    success: bool
    application_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Application list response model."""
    success: bool
    applications: List[Dict[str, Any]]
    total_count: int
    offset: int
    limit: int
    has_more: bool


class ApplicationDetailsResponse(BaseModel):
    """Application details response model."""
    success: bool
    application: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Analytics response model."""
    success: bool
    analytics: Optional[Dict[str, Any]] = None
    date_range_days: Optional[int] = None
    error: Optional[str] = None


class RemindersResponse(BaseModel):
    """Follow-up reminders response model."""
    success: bool
    reminders: List[Dict[str, Any]]
    total_count: int
    days_ahead: int


# Application Management Routes

@router.post("/", response_model=ApplicationResponse)
async def create_application(
    request: CreateApplicationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new job application record.
    Tracks application details, contact information, and initial status.
    """
    try:
        app_service = get_application_management_service()
        
        # Get user profile ID
        if not current_user.profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile_id = str(current_user.profile.id)
        
        # Convert request to dict
        application_data = request.dict()
        
        # Create application
        result = await app_service.create_application(
            profile_id=profile_id,
            company_name=request.company_name,
            position_title=request.position_title,
            application_data=application_data
        )
        
        if result["success"]:
            logger.info(f"Application created: {result['application_id']} for user {current_user.id}")
            return ApplicationResponse(
                success=True,
                application_id=result["application_id"],
                message=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create application for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )


@router.get("/", response_model=ApplicationListResponse)
async def get_applications(
    status_filter: Optional[str] = Query(None, description="Filter by application status"),
    company_filter: Optional[str] = Query(None, description="Filter by company name"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of applications"),
    offset: int = Query(0, ge=0, description="Number of applications to skip"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's job applications with filtering and pagination.
    Supports filtering by status, company, and date ranges.
    """
    try:
        app_service = get_application_management_service()
        
        # Get user profile ID
        if not current_user.profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile_id = str(current_user.profile.id)
        
        # Get applications
        result = await app_service.get_applications(
            profile_id=profile_id,
            status_filter=status_filter,
            company_filter=company_filter,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return ApplicationListResponse(
                success=True,
                applications=result["applications"],
                total_count=result["total_count"],
                offset=result["offset"],
                limit=result["limit"],
                has_more=result["has_more"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get applications for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get applications: {str(e)}"
        )


@router.get("/{application_id}", response_model=ApplicationDetailsResponse)
async def get_application_details(
    application_id: str,
    include_events: bool = Query(True, description="Include application events"),
    include_documents: bool = Query(True, description="Include application documents"),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information for a specific application.
    Includes timeline events, associated documents, and complete history.
    """
    try:
        app_service = get_application_management_service()
        
        # Get application details
        result = await app_service.get_application_details(
            application_id=application_id,
            include_events=include_events,
            include_documents=include_documents
        )
        
        if result["success"]:
            return ApplicationDetailsResponse(
                success=True,
                application=result["application"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get application details for {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application details: {str(e)}"
        )


@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    request: UpdateStatusRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update application status and record timeline event.
    Automatically calculates response times and process duration.
    """
    try:
        app_service = get_application_management_service()
        
        # Prepare additional data
        additional_data = {}
        if request.interview_notes:
            additional_data["interview_notes"] = request.interview_notes
        if request.next_interview_date:
            additional_data["next_interview_date"] = request.next_interview_date
        if request.outcome_reason:
            additional_data["outcome_reason"] = request.outcome_reason
        if request.follow_up_date:
            additional_data["next_follow_up_date"] = request.follow_up_date
        
        # Update status
        result = await app_service.update_application_status(
            application_id=application_id,
            new_status=request.new_status,
            event_description=request.event_description,
            additional_data=additional_data
        )
        
        if result["success"]:
            logger.info(f"Application {application_id} status updated to {request.new_status}")
            return ApplicationResponse(
                success=True,
                application_id=result["application_id"],
                message=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update application status for {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application status: {str(e)}"
        )


@router.post("/{application_id}/events", response_model=ApplicationResponse)
async def add_application_event(
    application_id: str,
    request: AddEventRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Add an event to application timeline.
    Tracks interactions, interviews, follow-ups, and other significant events.
    """
    try:
        app_service = get_application_management_service()
        
        # Convert request to event data
        event_data = request.dict()
        
        # Add event
        result = await app_service.add_application_event(
            application_id=application_id,
            event_type=request.event_type,
            event_description=request.event_description,
            event_data=event_data
        )
        
        if result["success"]:
            logger.info(f"Event {request.event_type} added to application {application_id}")
            return ApplicationResponse(
                success=True,
                application_id=application_id,
                message=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add event to application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add application event: {str(e)}"
        )


@router.get("/analytics/summary", response_model=AnalyticsResponse)
async def get_applications_analytics(
    date_range_days: int = Query(365, ge=1, le=3650, description="Number of days to include in analytics"),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics for user's job applications.
    Provides success rates, response times, and application trends.
    """
    try:
        app_service = get_application_management_service()
        
        # Get user profile ID
        if not current_user.profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile_id = str(current_user.profile.id)
        
        # Get analytics
        result = await app_service.get_applications_analytics(
            profile_id=profile_id,
            date_range_days=date_range_days
        )
        
        if result["success"]:
            return AnalyticsResponse(
                success=True,
                analytics=result["analytics"],
                date_range_days=date_range_days
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/reminders/follow-ups", response_model=RemindersResponse)
async def get_follow_up_reminders(
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days ahead to check"),
    current_user: User = Depends(get_current_user)
):
    """
    Get applications that need follow-up in the specified time range.
    Helps users stay on top of their application process.
    """
    try:
        app_service = get_application_management_service()
        
        # Get user profile ID
        if not current_user.profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile_id = str(current_user.profile.id)
        
        # Get follow-up reminders
        result = await app_service.get_follow_up_reminders(
            profile_id=profile_id,
            days_ahead=days_ahead
        )
        
        if result["success"]:
            return RemindersResponse(
                success=True,
                reminders=result["reminders"],
                total_count=result["total_count"],
                days_ahead=days_ahead
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get follow-up reminders for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get follow-up reminders: {str(e)}"
        )


@router.delete("/{application_id}", response_model=ApplicationResponse)
async def delete_application(
    application_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an application and all associated data.
    Provides cleanup functionality with proper user verification.
    """
    try:
        app_service = get_application_management_service()
        
        # Get user profile ID for verification
        profile_id = str(current_user.profile.id) if current_user.profile else None
        
        # Delete application
        result = await app_service.delete_application(
            application_id=application_id,
            profile_id=profile_id
        )
        
        if result["success"]:
            logger.info(f"Application {application_id} deleted by user {current_user.id}")
            return ApplicationResponse(
                success=True,
                message=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete application: {str(e)}"
        )


@router.get("/status/options")
async def get_status_options(
    current_user: User = Depends(get_current_user)
):
    """
    Get available application status options and their descriptions.
    Provides status workflow information for the frontend.
    """
    try:
        status_options = {
            "applied": {
                "label": "Applied",
                "description": "Application submitted",
                "next_statuses": ["screening", "phone_screen", "rejected", "no_response"],
                "color": "blue"
            },
            "screening": {
                "label": "Screening",
                "description": "Initial screening in progress",
                "next_statuses": ["phone_screen", "technical_interview", "rejected"],
                "color": "yellow"
            },
            "phone_screen": {
                "label": "Phone Screen",
                "description": "Phone/video screening scheduled or completed",
                "next_statuses": ["technical_interview", "on_site_interview", "rejected"],
                "color": "orange"
            },
            "technical_interview": {
                "label": "Technical Interview",
                "description": "Technical interview scheduled or completed",
                "next_statuses": ["on_site_interview", "final_interview", "rejected"],
                "color": "purple"
            },
            "on_site_interview": {
                "label": "On-site Interview",
                "description": "On-site or final round interview",
                "next_statuses": ["final_interview", "offer", "rejected"],
                "color": "indigo"
            },
            "final_interview": {
                "label": "Final Interview",
                "description": "Final interview completed",
                "next_statuses": ["offer", "rejected"],
                "color": "pink"
            },
            "offer": {
                "label": "Offer Received",
                "description": "Job offer received",
                "next_statuses": ["hired", "rejected", "withdrawn"],
                "color": "green"
            },
            "hired": {
                "label": "Hired",
                "description": "Offer accepted, hired",
                "next_statuses": [],
                "color": "green"
            },
            "rejected": {
                "label": "Rejected",
                "description": "Application rejected",
                "next_statuses": [],
                "color": "red"
            },
            "withdrawn": {
                "label": "Withdrawn",
                "description": "Application withdrawn by candidate",
                "next_statuses": [],
                "color": "gray"
            },
            "no_response": {
                "label": "No Response",
                "description": "No response from company",
                "next_statuses": [],
                "color": "gray"
            }
        }
        
        return {
            "success": True,
            "status_options": status_options,
            "default_status": "applied"
        }
        
    except Exception as e:
        logger.error(f"Failed to get status options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get status options"
        )