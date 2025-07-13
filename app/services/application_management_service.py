#!/usr/bin/env python3
"""
Application Management Service for TailerAI v2.0 - PRD-011: Personal Application Management

Personal job application tracking and management system for individual users.
Provides comprehensive application lifecycle management, analytics, and insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.database_service import DatabaseService
from app.models.database import (
    UserProfile, JobApplication, ApplicationDocument, ApplicationEvent,
    ExportHistory, ContentSelection, ATSOptimization
)

logger = logging.getLogger(__name__)


@dataclass
class ApplicationAnalytics:
    """Analytics data for job applications."""
    total_applications: int = 0
    active_applications: int = 0
    interviews_scheduled: int = 0
    offers_received: int = 0
    rejections_received: int = 0
    avg_response_time_days: float = 0.0
    success_rate: float = 0.0
    applications_by_status: Dict[str, int] = None
    applications_by_month: Dict[str, int] = None
    top_companies: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.applications_by_status is None:
            self.applications_by_status = {}
        if self.applications_by_month is None:
            self.applications_by_month = {}
        if self.top_companies is None:
            self.top_companies = []


class ApplicationManagementService:
    """
    Personal application management service for individual job seekers.
    Handles application tracking, follow-ups, analytics, and insights.
    """
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def create_application(
        self,
        profile_id: str,
        company_name: str,
        position_title: str,
        application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new job application record.
        
        Args:
            profile_id: User profile ID
            company_name: Company name
            position_title: Job position title
            application_data: Additional application details
            
        Returns:
            Dict with creation result and application ID
        """
        try:
            # Validate required fields
            if not all([profile_id, company_name, position_title]):
                return {
                    "success": False,
                    "error": "Missing required fields: profile_id, company_name, position_title"
                }
            
            # Prepare application data
            app_data = {
                "profile_id": profile_id,
                "company_name": company_name,
                "position_title": position_title,
                "application_date": application_data.get("application_date", datetime.now()),
                "job_board_url": application_data.get("job_board_url"),
                "job_board_source": application_data.get("job_board_source", "direct"),
                "application_method": application_data.get("application_method", "online"),
                "cover_letter_used": application_data.get("cover_letter_used", False),
                "resume_version_used": application_data.get("resume_version_used"),
                "application_status": "applied",
                "recruiter_name": application_data.get("recruiter_name"),
                "recruiter_email": application_data.get("recruiter_email"),
                "recruiter_phone": application_data.get("recruiter_phone"),
                "hr_contact": application_data.get("hr_contact"),
                "salary_range_min": application_data.get("salary_range_min"),
                "salary_range_max": application_data.get("salary_range_max"),
                "personal_interest_level": application_data.get("personal_interest_level", 5),
                "benefits_notes": application_data.get("benefits_notes"),
                "company_culture_notes": application_data.get("company_culture_notes")
            }
            
            # Create application in database
            with self.db_service.get_session() as session:
                application = JobApplication(**app_data)
                session.add(application)
                session.flush()
                
                application_id = str(application.id)
                
                # Create initial application event
                initial_event = ApplicationEvent(
                    application_id=application.id,
                    event_type="application_sent",
                    event_date=application.application_date,
                    event_description=f"Applied for {position_title} at {company_name}",
                    outcome="pending"
                )
                session.add(initial_event)
                
                session.commit()
                
                logger.info(f"Created application {application_id} for profile {profile_id}")
                
                return {
                    "success": True,
                    "application_id": application_id,
                    "message": f"Application created for {position_title} at {company_name}"
                }
                
        except Exception as e:
            logger.error(f"Failed to create application: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create application: {str(e)}"
            }
    
    async def update_application_status(
        self,
        application_id: str,
        new_status: str,
        event_description: str = None,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update application status and record event.
        
        Args:
            application_id: Application ID
            new_status: New application status
            event_description: Description of status change
            additional_data: Additional data to update
            
        Returns:
            Dict with update result
        """
        try:
            with self.db_service.get_session() as session:
                # Get application
                application = session.query(JobApplication).filter(
                    JobApplication.id == application_id
                ).first()
                
                if not application:
                    return {
                        "success": False,
                        "error": f"Application not found: {application_id}"
                    }
                
                old_status = application.application_status
                
                # Update application status
                application.application_status = new_status
                application.updated_at = datetime.now()
                
                # Update additional data if provided
                if additional_data:
                    for key, value in additional_data.items():
                        if hasattr(application, key):
                            setattr(application, key, value)
                
                # Calculate response time for first response
                if old_status == "applied" and new_status != "applied":
                    response_time = (datetime.now() - application.application_date).days
                    application.response_time_days = response_time
                
                # Set outcome date for final statuses
                if new_status in ["hired", "rejected", "withdrawn", "no_response"]:
                    application.outcome = new_status
                    application.outcome_date = datetime.now()
                    
                    # Calculate total process time
                    total_days = (datetime.now() - application.application_date).days
                    application.total_process_days = total_days
                
                # Create status change event
                event_desc = event_description or f"Status changed from {old_status} to {new_status}"
                status_event = ApplicationEvent(
                    application_id=application.id,
                    event_type="status_change",
                    event_date=datetime.now(),
                    event_description=event_desc,
                    outcome="positive" if new_status in ["interview", "offer", "hired"] else "neutral"
                )
                session.add(status_event)
                
                session.commit()
                
                logger.info(f"Updated application {application_id} status to {new_status}")
                
                return {
                    "success": True,
                    "application_id": application_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "message": f"Status updated to {new_status}"
                }
                
        except Exception as e:
            logger.error(f"Failed to update application status: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update application status: {str(e)}"
            }
    
    async def add_application_event(
        self,
        application_id: str,
        event_type: str,
        event_description: str,
        event_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Add an event to application timeline.
        
        Args:
            application_id: Application ID
            event_type: Type of event
            event_description: Event description
            event_data: Additional event data
            
        Returns:
            Dict with creation result
        """
        try:
            event_data = event_data or {}
            
            # Prepare event data
            event_info = {
                "application_id": application_id,
                "event_type": event_type,
                "event_date": event_data.get("event_date", datetime.now()),
                "event_description": event_description,
                "contact_person": event_data.get("contact_person"),
                "contact_method": event_data.get("contact_method"),
                "outcome": event_data.get("outcome", "neutral"),
                "next_steps": event_data.get("next_steps"),
                "follow_up_required": event_data.get("follow_up_required", False),
                "follow_up_date": event_data.get("follow_up_date"),
                "attachments": event_data.get("attachments", []),
                "external_references": event_data.get("external_references", [])
            }
            
            with self.db_service.get_session() as session:
                # Verify application exists
                application = session.query(JobApplication).filter(
                    JobApplication.id == application_id
                ).first()
                
                if not application:
                    return {
                        "success": False,
                        "error": f"Application not found: {application_id}"
                    }
                
                # Create event
                event = ApplicationEvent(**event_info)
                session.add(event)
                
                # Update application follow-up info if needed
                if event_info["follow_up_required"]:
                    application.next_follow_up_date = event_info["follow_up_date"]
                    application.follow_up_count += 1
                
                # Update interview tracking for interview events
                if event_type in ["phone_interview", "technical_interview", "on_site_interview", "final_interview"]:
                    application.interview_rounds += 1
                    if event_data.get("next_interview_date"):
                        application.next_interview_date = event_data["next_interview_date"]
                
                session.commit()
                
                logger.info(f"Added event {event_type} to application {application_id}")
                
                return {
                    "success": True,
                    "event_id": str(event.id),
                    "message": f"Event {event_type} added successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to add application event: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to add application event: {str(e)}"
            }
    
    async def get_applications(
        self,
        profile_id: str,
        status_filter: str = None,
        company_filter: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get applications for a user profile with filtering.
        
        Args:
            profile_id: User profile ID
            status_filter: Filter by application status
            company_filter: Filter by company name
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            Dict with applications list and metadata
        """
        try:
            with self.db_service.get_session() as session:
                # Build query
                query = session.query(JobApplication).filter(
                    JobApplication.profile_id == profile_id
                )
                
                # Apply filters
                if status_filter:
                    query = query.filter(JobApplication.application_status == status_filter)
                
                if company_filter:
                    query = query.filter(JobApplication.company_name.ilike(f"%{company_filter}%"))
                
                # Get total count
                total_count = query.count()
                
                # Get applications with pagination
                applications = query.order_by(
                    JobApplication.application_date.desc()
                ).offset(offset).limit(limit).all()
                
                # Convert to dict format
                app_list = []
                for app in applications:
                    app_dict = {
                        "id": str(app.id),
                        "company_name": app.company_name,
                        "position_title": app.position_title,
                        "application_status": app.application_status,
                        "application_date": app.application_date.isoformat(),
                        "job_board_source": app.job_board_source,
                        "personal_interest_level": app.personal_interest_level,
                        "outcome": app.outcome,
                        "response_time_days": app.response_time_days,
                        "interview_rounds": app.interview_rounds,
                        "salary_range_min": app.salary_range_min,
                        "salary_range_max": app.salary_range_max,
                        "next_follow_up_date": app.next_follow_up_date.isoformat() if app.next_follow_up_date else None,
                        "created_at": app.created_at.isoformat(),
                        "updated_at": app.updated_at.isoformat()
                    }
                    app_list.append(app_dict)
                
                return {
                    "success": True,
                    "applications": app_list,
                    "total_count": total_count,
                    "offset": offset,
                    "limit": limit,
                    "has_more": (offset + limit) < total_count
                }
                
        except Exception as e:
            logger.error(f"Failed to get applications: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get applications: {str(e)}"
            }
    
    async def get_application_details(
        self,
        application_id: str,
        include_events: bool = True,
        include_documents: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific application.
        
        Args:
            application_id: Application ID
            include_events: Include application events timeline
            include_documents: Include associated documents
            
        Returns:
            Dict with detailed application information
        """
        try:
            with self.db_service.get_session() as session:
                # Get application
                application = session.query(JobApplication).filter(
                    JobApplication.id == application_id
                ).first()
                
                if not application:
                    return {
                        "success": False,
                        "error": f"Application not found: {application_id}"
                    }
                
                # Build detailed application data
                app_data = {
                    "id": str(application.id),
                    "company_name": application.company_name,
                    "position_title": application.position_title,
                    "job_board_url": application.job_board_url,
                    "job_board_source": application.job_board_source,
                    "application_method": application.application_method,
                    "cover_letter_used": application.cover_letter_used,
                    "resume_version_used": application.resume_version_used,
                    "application_status": application.application_status,
                    "application_date": application.application_date.isoformat(),
                    "recruiter_name": application.recruiter_name,
                    "recruiter_email": application.recruiter_email,
                    "recruiter_phone": application.recruiter_phone,
                    "hr_contact": application.hr_contact,
                    "interview_rounds": application.interview_rounds,
                    "next_interview_date": application.next_interview_date.isoformat() if application.next_interview_date else None,
                    "interview_notes": application.interview_notes,
                    "outcome": application.outcome,
                    "outcome_date": application.outcome_date.isoformat() if application.outcome_date else None,
                    "outcome_reason": application.outcome_reason,
                    "salary_range_min": application.salary_range_min,
                    "salary_range_max": application.salary_range_max,
                    "benefits_notes": application.benefits_notes,
                    "company_culture_notes": application.company_culture_notes,
                    "personal_interest_level": application.personal_interest_level,
                    "response_time_days": application.response_time_days,
                    "total_process_days": application.total_process_days,
                    "last_follow_up_date": application.last_follow_up_date.isoformat() if application.last_follow_up_date else None,
                    "next_follow_up_date": application.next_follow_up_date.isoformat() if application.next_follow_up_date else None,
                    "follow_up_count": application.follow_up_count,
                    "created_at": application.created_at.isoformat(),
                    "updated_at": application.updated_at.isoformat()
                }
                
                # Include events if requested
                if include_events:
                    events = session.query(ApplicationEvent).filter(
                        ApplicationEvent.application_id == application.id
                    ).order_by(ApplicationEvent.event_date.desc()).all()
                    
                    app_data["events"] = [
                        {
                            "id": str(event.id),
                            "event_type": event.event_type,
                            "event_date": event.event_date.isoformat(),
                            "event_description": event.event_description,
                            "contact_person": event.contact_person,
                            "contact_method": event.contact_method,
                            "outcome": event.outcome,
                            "next_steps": event.next_steps,
                            "follow_up_required": event.follow_up_required,
                            "follow_up_date": event.follow_up_date.isoformat() if event.follow_up_date else None
                        }
                        for event in events
                    ]
                
                # Include documents if requested
                if include_documents:
                    documents = session.query(ApplicationDocument).filter(
                        ApplicationDocument.application_id == application.id
                    ).all()
                    
                    app_data["documents"] = [
                        {
                            "id": str(doc.id),
                            "document_type": doc.document_type,
                            "document_format": doc.document_format,
                            "file_path": doc.file_path,
                            "file_size_bytes": doc.file_size_bytes,
                            "quality_score": doc.quality_score,
                            "created_at": doc.created_at.isoformat()
                        }
                        for doc in documents
                    ]
                
                return {
                    "success": True,
                    "application": app_data
                }
                
        except Exception as e:
            logger.error(f"Failed to get application details: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get application details: {str(e)}"
            }
    
    async def get_applications_analytics(
        self,
        profile_id: str,
        date_range_days: int = 365
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for user's job applications.
        
        Args:
            profile_id: User profile ID
            date_range_days: Number of days to include in analytics
            
        Returns:
            Dict with analytics data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=date_range_days)
            
            with self.db_service.get_session() as session:
                # Get applications in date range
                applications = session.query(JobApplication).filter(
                    JobApplication.profile_id == profile_id,
                    JobApplication.application_date >= cutoff_date
                ).all()
                
                analytics = ApplicationAnalytics()
                analytics.total_applications = len(applications)
                
                if analytics.total_applications == 0:
                    return {
                        "success": True,
                        "analytics": analytics.__dict__
                    }
                
                # Calculate basic metrics
                active_statuses = ["applied", "screening", "phone_screen", "technical_interview", "on_site_interview", "final_interview"]
                analytics.active_applications = len([app for app in applications if app.application_status in active_statuses])
                analytics.interviews_scheduled = len([app for app in applications if app.interview_rounds > 0])
                analytics.offers_received = len([app for app in applications if app.outcome == "hired" or app.application_status == "offer"])
                analytics.rejections_received = len([app for app in applications if app.outcome == "rejected"])
                
                # Calculate success rate
                completed_applications = len([app for app in applications if app.outcome in ["hired", "rejected", "withdrawn", "no_response"]])
                if completed_applications > 0:
                    analytics.success_rate = analytics.offers_received / completed_applications
                
                # Calculate average response time
                response_times = [app.response_time_days for app in applications if app.response_time_days is not None]
                if response_times:
                    analytics.avg_response_time_days = sum(response_times) / len(response_times)
                
                # Applications by status
                status_counts = {}
                for app in applications:
                    status = app.application_status
                    status_counts[status] = status_counts.get(status, 0) + 1
                analytics.applications_by_status = status_counts
                
                # Applications by month
                month_counts = {}
                for app in applications:
                    month_key = app.application_date.strftime("%Y-%m")
                    month_counts[month_key] = month_counts.get(month_key, 0) + 1
                analytics.applications_by_month = month_counts
                
                # Top companies by application count
                company_counts = {}
                for app in applications:
                    company = app.company_name
                    company_counts[company] = company_counts.get(company, 0) + 1
                
                analytics.top_companies = [
                    {"company_name": company, "application_count": count}
                    for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ]
                
                return {
                    "success": True,
                    "analytics": analytics.__dict__,
                    "date_range_days": date_range_days,
                    "cutoff_date": cutoff_date.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get applications analytics: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get applications analytics: {str(e)}"
            }
    
    async def get_follow_up_reminders(
        self,
        profile_id: str,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Get applications that need follow-up in the specified time range.
        
        Args:
            profile_id: User profile ID
            days_ahead: Number of days ahead to check for follow-ups
            
        Returns:
            Dict with follow-up reminders
        """
        try:
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            with self.db_service.get_session() as session:
                # Get applications needing follow-up
                applications = session.query(JobApplication).filter(
                    JobApplication.profile_id == profile_id,
                    JobApplication.next_follow_up_date.isnot(None),
                    JobApplication.next_follow_up_date <= end_date,
                    JobApplication.application_status.in_(["applied", "screening", "phone_screen", "technical_interview", "on_site_interview"])
                ).order_by(JobApplication.next_follow_up_date).all()
                
                reminders = []
                for app in applications:
                    days_until = (app.next_follow_up_date - datetime.now()).days
                    urgency = "overdue" if days_until < 0 else "urgent" if days_until <= 1 else "upcoming"
                    
                    reminder = {
                        "application_id": str(app.id),
                        "company_name": app.company_name,
                        "position_title": app.position_title,
                        "application_status": app.application_status,
                        "follow_up_date": app.next_follow_up_date.isoformat(),
                        "days_until_follow_up": days_until,
                        "urgency": urgency,
                        "follow_up_count": app.follow_up_count,
                        "recruiter_email": app.recruiter_email,
                        "recruiter_name": app.recruiter_name
                    }
                    reminders.append(reminder)
                
                return {
                    "success": True,
                    "reminders": reminders,
                    "total_count": len(reminders),
                    "days_ahead": days_ahead
                }
                
        except Exception as e:
            logger.error(f"Failed to get follow-up reminders: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get follow-up reminders: {str(e)}"
            }
    
    async def delete_application(
        self,
        application_id: str,
        profile_id: str = None
    ) -> Dict[str, Any]:
        """
        Delete an application and all associated data.
        
        Args:
            application_id: Application ID
            profile_id: Optional profile ID for additional verification
            
        Returns:
            Dict with deletion result
        """
        try:
            with self.db_service.get_session() as session:
                # Get application
                query = session.query(JobApplication).filter(
                    JobApplication.id == application_id
                )
                
                if profile_id:
                    query = query.filter(JobApplication.profile_id == profile_id)
                
                application = query.first()
                
                if not application:
                    return {
                        "success": False,
                        "error": f"Application not found: {application_id}"
                    }
                
                company_name = application.company_name
                position_title = application.position_title
                
                # Delete application (cascade will handle related records)
                session.delete(application)
                session.commit()
                
                logger.info(f"Deleted application {application_id} for {position_title} at {company_name}")
                
                return {
                    "success": True,
                    "message": f"Application for {position_title} at {company_name} has been deleted"
                }
                
        except Exception as e:
            logger.error(f"Failed to delete application: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete application: {str(e)}"
            }


# Create global application management service instance
application_management_service = None

def get_application_management_service() -> ApplicationManagementService:
    """Get the global application management service instance."""
    global application_management_service
    if application_management_service is None:
        from app.services.database_service import database_service
        application_management_service = ApplicationManagementService(database_service)
    return application_management_service