"""
Interview scheduling agent with calendar integration
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from loguru import logger

# Note: In production, install google-api-python-client
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build


class InterviewScheduler:
    """Automated interview scheduling with calendar integration"""
    
    def __init__(self, calendar_api=None):
        """
        Initialize scheduler
        
        Args:
            calendar_api: Google Calendar API client (or other calendar service)
        """
        self.calendar = calendar_api
        self.default_duration_minutes = 30
    
    def find_optimal_slots(
        self,
        candidate_availability: List[Dict],
        interviewer_ids: List[str],
        duration_minutes: int = 30,
        timezone: str = "UTC",
        look_ahead_days: int = 14
    ) -> List[Dict]:
        """
        Find overlapping availability between candidate and interviewers
        
        Args:
            candidate_availability: List of candidate's available time slots
                Format: [{"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T17:00:00Z"}]
            interviewer_ids: List of interviewer email addresses or IDs
            duration_minutes: Required meeting duration
            timezone: Timezone for scheduling
            look_ahead_days: How many days ahead to search
            
        Returns:
            List of available time slots ranked by optimality
        """
        logger.info(f"Finding optimal slots for {len(interviewer_ids)} interviewers")
        
        if not self.calendar:
            logger.warning("Calendar API not configured, returning mock slots")
            return self._generate_mock_slots(duration_minutes)
        
        # Get interviewer calendars
        interviewer_busy_times = []
        for interviewer_id in interviewer_ids:
            busy_times = self._get_busy_times(
                interviewer_id,
                look_ahead_days,
                timezone
            )
            interviewer_busy_times.append(busy_times)
        
        # Find free slots
        free_slots = self._find_free_slots(
            candidate_availability,
            interviewer_busy_times,
            duration_minutes,
            timezone
        )
        
        # Rank slots by preference
        ranked_slots = self._rank_slots(free_slots, timezone)
        
        # Return top 3 options
        return ranked_slots[:3]
    
    def _get_busy_times(
        self,
        calendar_id: str,
        days_ahead: int,
        timezone: str
    ) -> List[Dict]:
        """
        Get busy times from a calendar
        
        This is a mock implementation. In production, use:
        service = build('calendar', 'v3', credentials=creds)
        events = service.events().list(calendarId=calendar_id, ...).execute()
        """
        # Mock implementation
        return []
    
    def _find_free_slots(
        self,
        candidate_slots: List[Dict],
        interviewer_busy: List[List[Dict]],
        duration: int,
        timezone: str
    ) -> List[Dict]:
        """Find time slots that work for everyone"""
        free_slots = []
        
        for candidate_slot in candidate_slots:
            start = datetime.fromisoformat(candidate_slot["start"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(candidate_slot["end"].replace('Z', '+00:00'))
            
            # Generate potential slots within candidate's availability
            current = start
            while current + timedelta(minutes=duration) <= end:
                slot_end = current + timedelta(minutes=duration)
                
                # Check if this slot conflicts with any interviewer
                conflicts = False
                for interviewer_calendar in interviewer_busy:
                    if self._has_conflict(current, slot_end, interviewer_calendar):
                        conflicts = True
                        break
                
                if not conflicts:
                    free_slots.append({
                        "start": current.isoformat(),
                        "end": slot_end.isoformat(),
                        "duration_minutes": duration
                    })
                
                # Move to next potential slot (30 min increments)
                current += timedelta(minutes=30)
        
        return free_slots
    
    def _has_conflict(
        self,
        slot_start: datetime,
        slot_end: datetime,
        busy_times: List[Dict]
    ) -> bool:
        """Check if a time slot conflicts with busy times"""
        for busy in busy_times:
            busy_start = datetime.fromisoformat(busy["start"].replace('Z', '+00:00'))
            busy_end = datetime.fromisoformat(busy["end"].replace('Z', '+00:00'))
            
            # Check for overlap
            if slot_start < busy_end and slot_end > busy_start:
                return True
        
        return False
    
    def _rank_slots(self, slots: List[Dict], timezone: str) -> List[Dict]:
        """
        Rank available slots by preference
        
        Preferences:
        1. Weekday mornings (9-11 AM) - highest priority
        2. Weekday afternoons (2-4 PM) - medium priority
        3. Other weekday times - lower priority
        4. Avoid early mornings (<9 AM) and late afternoons (>5 PM)
        """
        scored_slots = []
        
        for slot in slots:
            start = datetime.fromisoformat(slot["start"].replace('Z', '+00:00'))
            
            score = 0
            hour = start.hour
            
            # Weekday bonus
            if start.weekday() < 5:  # Monday-Friday
                score += 10
            
            # Time of day preferences
            if 9 <= hour < 11:
                score += 20  # Morning preferred
            elif 14 <= hour < 16:
                score += 15  # Afternoon acceptable
            elif 11 <= hour < 14:
                score += 10  # Midday okay
            elif hour < 9 or hour >= 17:
                score -= 10  # Discourage early/late
            
            # Avoid Monday mornings and Friday afternoons
            if start.weekday() == 0 and hour < 11:
                score -= 5
            if start.weekday() == 4 and hour >= 15:
                score -= 5
            
            scored_slots.append({
                **slot,
                "preference_score": score
            })
        
        # Sort by score (descending)
        scored_slots.sort(key=lambda x: x["preference_score"], reverse=True)
        
        return scored_slots
    
    def _generate_mock_slots(self, duration: int) -> List[Dict]:
        """Generate mock time slots for testing"""
        now = datetime.utcnow()
        
        # Generate 3 slots over the next week
        slots = []
        for i in range(3):
            days_ahead = 2 + i * 2  # 2, 4, 6 days ahead
            slot_start = now + timedelta(days=days_ahead, hours=10)  # 10 AM
            slot_start = slot_start.replace(minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(minutes=duration)
            
            slots.append({
                "start": slot_start.isoformat() + "Z",
                "end": slot_end.isoformat() + "Z",
                "duration_minutes": duration,
                "preference_score": 20 - i * 5
            })
        
        return slots
    
    def send_interview_invite(
        self,
        candidate_email: str,
        interviewer_emails: List[str],
        time_slot: Dict,
        job_title: str,
        meeting_platform: str = "zoom"
    ) -> Dict:
        """
        Send calendar invitation to candidate and interviewers
        
        Args:
            candidate_email: Candidate's email
            interviewer_emails: List of interviewer emails
            time_slot: Selected time slot
            job_title: Job title for the interview
            meeting_platform: Video platform (zoom, teams, etc.)
            
        Returns:
            Meeting details including video link
        """
        logger.info(f"Sending interview invite to {candidate_email}")
        
        # Generate video meeting link
        video_link = self._create_video_meeting(
            time_slot,
            job_title,
            meeting_platform
        )
        
        # Create calendar event
        event = {
            "summary": f"Interview: {job_title}",
            "description": f"""
Interview for {job_title} position

Video meeting link: {video_link}

Please join a few minutes early and ensure your camera and microphone are working.

If you need to reschedule, please contact us at least 24 hours in advance.
            """.strip(),
            "start": {
                "dateTime": time_slot["start"],
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": time_slot["end"],
                "timeZone": "UTC"
            },
            "attendees": [
                {"email": candidate_email},
                *[{"email": email} for email in interviewer_emails]
            ],
            "conferenceData": {
                "entryPoints": [{
                    "entryPointType": "video",
                    "uri": video_link
                }]
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},  # 1 day before
                    {"method": "popup", "minutes": 30}  # 30 min before
                ]
            }
        }
        
        # In production, create event using calendar API:
        # event = service.events().insert(calendarId='primary', body=event).execute()
        
        logger.info(f"Interview scheduled for {time_slot['start']}")
        
        return {
            "event_id": "mock_event_id",
            "meeting_url": video_link,
            "scheduled_time": time_slot["start"],
            "attendees": [candidate_email] + interviewer_emails
        }
    
    def _create_video_meeting(
        self,
        time_slot: Dict,
        topic: str,
        platform: str
    ) -> str:
        """
        Create video meeting on specified platform
        
        For Zoom, you would use:
        from zoomus import ZoomClient
        client = ZoomClient(API_KEY, API_SECRET)
        meeting = client.meeting.create(...)
        """
        # Mock implementation
        if platform == "zoom":
            return f"https://zoom.us/j/mock123456?pwd=mockpassword"
        elif platform == "teams":
            return f"https://teams.microsoft.com/l/meetup-join/mock123"
        else:
            return f"https://meet.custom.com/interview-{datetime.utcnow().timestamp()}"
    
    def reschedule_interview(
        self,
        event_id: str,
        new_time_slot: Dict,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Reschedule an existing interview
        
        Args:
            event_id: Calendar event ID
            new_time_slot: New time slot
            reason: Optional reason for rescheduling
            
        Returns:
            Updated meeting details
        """
        logger.info(f"Rescheduling interview {event_id}")
        
        # In production:
        # event = service.events().get(calendarId='primary', eventId=event_id).execute()
        # event['start'] = new_time_slot['start']
        # event['end'] = new_time_slot['end']
        # updated_event = service.events().update(...).execute()
        
        return {
            "event_id": event_id,
            "new_time": new_time_slot["start"],
            "status": "rescheduled"
        }
    
    def cancel_interview(
        self,
        event_id: str,
        send_notification: bool = True
    ) -> bool:
        """
        Cancel an interview
        
        Args:
            event_id: Calendar event ID
            send_notification: Whether to notify attendees
            
        Returns:
            Success status
        """
        logger.info(f"Canceling interview {event_id}")
        
        # In production:
        # service.events().delete(calendarId='primary', eventId=event_id, sendNotifications=send_notification).execute()
        
        return True
