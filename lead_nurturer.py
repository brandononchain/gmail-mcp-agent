#!/usr/bin/env python3
"""
Lead Nurturing System for the Gmail MCP Agent.

Handles automated follow-ups, response tracking, and lead scoring. All
campaign-specific content (sender identity, subjects, email copy, contact list)
is loaded from configuration and the ``templates/`` directory so the agent stays
generic and plug-and-play.
"""

import csv
import json
import os
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from email.message import EmailMessage
import base64

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from jinja2 import Template

@dataclass
class Lead:
    email: str
    first_name: str
    company: str
    status: str = "new"  # new, contacted, responded, interested, not_interested, scheduled
    last_contact: Optional[datetime] = None
    response_count: int = 0
    follow_up_count: int = 0
    lead_score: int = 0
    notes: str = ""

class LeadNurturer:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json",
                 config_path: str = "nurturing_config.json", service: Any = None):
        self.config_path = config_path
        self.config = self._load_config()
        self.service = service or self._get_service(credentials_path, token_path)
        self.leads = self._load_leads()
        self.templates = self._load_templates()
        self.sync_state = self._load_sync_state()
        
    def _get_service(self, credentials_path: str, token_path: str):
        """Initialize Gmail service"""
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 
                 "https://www.googleapis.com/auth/gmail.send"]
        
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        
        return build("gmail", "v1", credentials=creds)
    
    def _load_leads(self) -> Dict[str, Lead]:
        """Load leads from the contacts CSV and tracking file"""
        leads = {}

        contacts_file = self.config.get('contacts_file', 'contacts.csv')

        # Load from the contacts CSV (only a `to` column is required;
        # `first_name` and `company` are optional and used for personalization).
        try:
            with open(contacts_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_email = (row.get('to') or row.get('email') or '').strip()
                    if not raw_email:
                        continue
                    email = raw_email.lower()
                    leads[email] = Lead(
                        email=email,
                        first_name=(row.get('first_name') or '').strip(),
                        company=(row.get('company') or '').strip(),
                    )
        except FileNotFoundError:
            print(f"Contacts file not found: {contacts_file}")
        
        # Load tracking data
        try:
            with open('lead_tracking.json', 'r') as f:
                tracking_data = json.load(f)
                for email, data in tracking_data.items():
                    if email in leads:
                        leads[email].status = data.get('status', 'new')
                        leads[email].last_contact = datetime.fromisoformat(data['last_contact']) if data.get('last_contact') else None
                        leads[email].response_count = data.get('response_count', 0)
                        leads[email].follow_up_count = data.get('follow_up_count', 0)
                        leads[email].lead_score = data.get('lead_score', 0)
                        leads[email].notes = data.get('notes', '')
        except FileNotFoundError:
            print("No existing tracking data found")
        
        return leads

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def reload_config(self, new_config: Dict[str, Any]):
        self.config = new_config or {}

    def _load_sync_state(self) -> Dict[str, Any]:
        try:
            with open('gmail_sync_state.json', 'r') as f:
                return json.load(f)
        except Exception:
            return {"last_checked_iso": None, "processed_message_ids": []}

    def _save_sync_state(self):
        try:
            with open('gmail_sync_state.json', 'w') as f:
                json.dump(self.sync_state, f, indent=2)
        except Exception:
            pass
    
    def _save_leads(self):
        """Save lead tracking data"""
        tracking_data = {}
        for email, lead in self.leads.items():
            tracking_data[email] = {
                'status': lead.status,
                'last_contact': lead.last_contact.isoformat() if lead.last_contact else None,
                'response_count': lead.response_count,
                'follow_up_count': lead.follow_up_count,
                'lead_score': lead.lead_score,
                'notes': lead.notes
            }
        
        with open('lead_tracking.json', 'w') as f:
            json.dump(tracking_data, f, indent=2)
    
    # Generic fallbacks used only when a template file is missing, so the agent
    # always has something to send. Real copy lives in the ``templates/`` dir.
    _DEFAULT_TEMPLATES = {
        'initial': (
            "Hi {{ first_name }},\n\n"
            "I'm reaching out because I think {{ company }} could benefit from "
            "what we're building.\n\n"
            "Would you be open to a quick call this week?\n\n"
            "Thanks,\n{{ sender_name }}\n{{ company_name }}"
        ),
        'followup_1': (
            "Hi {{ first_name }},\n\n"
            "Just following up on my previous note in case it slipped through.\n\n"
            "Best,\n{{ sender_name }}\n{{ company_name }}"
        ),
        'followup_2': (
            "Hi {{ first_name }},\n\n"
            "This will be my last note for now — no pressure either way.\n\n"
            "Best,\n{{ sender_name }}\n{{ company_name }}"
        ),
        'interested': (
            "Hi {{ first_name }},\n\n"
            "Great to hear from you! Let me know a time that works and I'll send "
            "over the details.\n\n"
            "Best,\n{{ sender_name }}\n{{ company_name }}"
        ),
    }

    def _load_templates(self) -> Dict[str, Template]:
        """Load email templates from the configured templates directory.

        Each template type maps to a ``.txt`` file. Missing files fall back to a
        built-in generic version so the system never breaks.
        """
        templates_dir = self.config.get('templates_dir', 'templates')
        template_files = {
            'initial': 'initial.txt',
            'followup_1': 'followup_1.txt',
            'followup_2': 'followup_2.txt',
            'interested': 'interested.txt',
        }

        templates = {}
        for key, filename in template_files.items():
            path = os.path.join(templates_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    templates[key] = Template(f.read().strip())
            except FileNotFoundError:
                templates[key] = Template(self._DEFAULT_TEMPLATES[key])
        return templates

    def _render(self, template: Template, lead: "Lead") -> str:
        """Render a template with lead and sender context."""
        return template.render(
            first_name=lead.first_name,
            company=lead.company,
            email=lead.email,
            sender_name=self.config.get('sender_name', ''),
            company_name=self.config.get('company_name', ''),
        )

    def _subject(self, key: str, lead: "Lead", default: str) -> str:
        """Resolve a configurable, templated subject line."""
        subject_template = self.config.get('subjects', {}).get(key, default)
        return Template(subject_template).render(
            first_name=lead.first_name,
            company=lead.company,
            sender_name=self.config.get('sender_name', ''),
            company_name=self.config.get('company_name', ''),
        )
    
    def check_for_responses(self):
        """Check Gmail for responses to our outreach with pagination and idempotency"""
        try:
            # Build search query
            newer_than_hours = (
                self.config.get('automation', {}).get('check_responses_interval_hours', 24)
            )
            query_parts = ["in:inbox"]
            if newer_than_hours:
                # Gmail supports newer_than with d,m,y; for hours we fallback to after timestamp
                after_ts = None
                if self.sync_state.get('last_checked_iso'):
                    try:
                        dt = datetime.fromisoformat(self.sync_state['last_checked_iso'])
                        after_ts = int(dt.timestamp())
                    except Exception:
                        after_ts = None
                if after_ts:
                    query_parts.append(f"after:{after_ts}")
                else:
                    # default to 1d window if no state
                    query_parts.append("newer_than:1d")
            query = " ".join(query_parts)

            processed_ids = set(self.sync_state.get('processed_message_ids', []))
            page_token = None
            while True:
                results = self.service.users().messages().list(
                    userId='me', q=query, pageToken=page_token, maxResults=100
                ).execute()
                messages = results.get('messages', [])

                for message in messages:
                    msg_id = message.get('id')
                    if not msg_id or msg_id in processed_ids:
                        continue

                    msg = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                    headers = msg.get('payload', {}).get('headers', [])

                    sender = None
                    subject = None
                    for header in headers:
                        name = header.get('name')
                        if name == 'From':
                            sender = header.get('value')
                        elif name == 'Subject':
                            subject = header.get('value')

                    if sender:
                        sender_email_match = re.search(r'<(.+?)>', sender)
                        if sender_email_match:
                            sender_email = sender_email_match.group(1).lower()
                        else:
                            sender_email = sender.lower()

                        if sender_email in self.leads:
                            self._process_response(sender_email, subject or "", msg)
                            processed_ids.add(msg_id)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            # Update last checked time and persist processed ids (bounded)
            self.sync_state['last_checked_iso'] = datetime.utcnow().isoformat()
            # Keep only last 500 ids to bound file size
            latest_ids = list(processed_ids)
            if len(latest_ids) > 500:
                latest_ids = latest_ids[-500:]
            self.sync_state['processed_message_ids'] = latest_ids
            self._save_sync_state()

        except HttpError as he:
            print(f"Gmail API error checking responses: {he}")
        except Exception as e:
            print(f"Error checking responses: {e}")
    
    def _process_response(self, email: str, subject: str, message: dict):
        """Process a response from a lead"""
        lead = self.leads[email]
        lead.response_count += 1
        lead.last_contact = datetime.now()
        
        # Analyze response sentiment and keywords
        body = self._get_message_body(message)
        response_lower = body.lower()
        
        # Update lead score based on response
        interested_words = self.config.get('response_keywords', {}).get('interested', ['interested','yes','demo','call','meeting','schedule','book'])
        not_interested_words = self.config.get('response_keywords', {}).get('not_interested', ['not interested','no thanks','stop','unsubscribe','remove'])

        if any(word in response_lower for word in interested_words):
            lead.status = 'interested'
            lead.lead_score += int(self.config.get('lead_scoring', {}).get('response_bonus', 10))
            lead.lead_score += int(self.config.get('lead_scoring', {}).get('interest_bonus', 5))
            if self.config.get('automation', {}).get('auto_respond_to_interest', True):
                self._send_automated_response(email, 'interested')
        elif any(word in response_lower for word in not_interested_words):
            lead.status = 'not_interested'
            lead.lead_score -= 5
        else:
            lead.lead_score += 2
        
        # Add notes
        lead.notes += f"\n{datetime.now().strftime('%Y-%m-%d')}: Response received - {subject}"
        
        print(f"Processed response from {lead.first_name} at {lead.company}")
    
    def _get_message_body(self, message: dict) -> str:
        """Extract message body from Gmail message"""
        try:
            payload = message.get('payload', {})
            # Prefer text/plain; fallback to text/html stripped
            def decode_part(part):
                data = part.get('body', {}).get('data')
                if not data:
                    return ""
                try:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                except Exception:
                    return ""

            if 'parts' in payload:
                # Walk parts recursively
                stack = list(payload.get('parts', []))
                html_candidate = ""
                while stack:
                    part = stack.pop()
                    mime = part.get('mimeType', '')
                    if 'parts' in part:
                        stack.extend(part.get('parts', []))
                    if mime == 'text/plain':
                        text = decode_part(part)
                        if text:
                            return text
                    elif mime == 'text/html' and not html_candidate:
                        html_candidate = decode_part(part)
                if html_candidate:
                    # Strip HTML tags rudimentarily
                    return re.sub('<[^<]+?>', '', html_candidate)
            else:
                mime = payload.get('mimeType')
                if mime == 'text/plain':
                    return decode_part(payload)
                elif mime == 'text/html':
                    html = decode_part(payload)
                    return re.sub('<[^<]+?>', '', html)
        except Exception as e:
            print(f"Error extracting message body: {e}")
        return ""
    
    def _send_automated_response(self, email: str, template_type: str):
        """Send automated response based on template type"""
        lead = self.leads[email]
        template = self.templates[template_type]

        subject = self._subject(template_type, lead, default="Re: Thanks for getting back to me")
        body = self._render(template, lead)

        # Send email (using existing send_message function)
        try:
            msg = EmailMessage()
            msg["To"] = email
            sender_email = self.config.get('sender_email') or self.service.users().getProfile(userId='me').execute().get('emailAddress')
            sender_name = self.config.get('sender_name') or ''
            msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
            msg["Subject"] = subject
            msg.set_content(body)
            
            encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self.service.users().messages().send(
                userId="me", 
                body={"raw": encoded}
            ).execute()
            
            print(f"Sent {template_type} response to {lead.first_name}")
        except Exception as e:
            print(f"Error sending response: {e}")
    
    def run_follow_up_sequence(self):
        """Run follow-up sequence for leads that need it"""
        now = datetime.now()
        
        for email, lead in self.leads.items():
            if not self.config.get('automation', {}).get('auto_send_follow_ups', True):
                continue
            if lead.status in ['new', 'contacted'] and lead.last_contact:
                days_since_contact = (now - lead.last_contact).days
                cfg_schedule = self.config.get('follow_up_schedule', {})
                fu1_days = int(cfg_schedule.get('followup_1_days', 3))
                fu2_days = int(cfg_schedule.get('followup_2_days', 7))
                max_follow = int(cfg_schedule.get('max_follow_ups', 2))

                # Follow-up 1
                if days_since_contact >= fu1_days and lead.follow_up_count == 0:
                    self._send_follow_up(email, 'followup_1')
                    lead.follow_up_count = 1
                    lead.last_contact = now
                # Follow-up 2
                elif days_since_contact >= fu2_days and lead.follow_up_count == 1:
                    self._send_follow_up(email, 'followup_2')
                    lead.follow_up_count = 2
                    lead.last_contact = now
                    if max_follow <= 2:
                        lead.status = 'not_interested'
    
    def _send_follow_up(self, email: str, template_type: str):
        """Send follow-up email"""
        lead = self.leads[email]
        template = self.templates[template_type]

        subject = self._subject(template_type, lead, default="Following up")
        body = self._render(template, lead)

        try:
            msg = EmailMessage()
            msg["To"] = email
            sender_email = self.config.get('sender_email') or self.service.users().getProfile(userId='me').execute().get('emailAddress')
            sender_name = self.config.get('sender_name') or ''
            msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
            msg["Subject"] = subject
            msg.set_content(body)
            
            encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self.service.users().messages().send(
                userId="me", 
                body={"raw": encoded}
            ).execute()
            
            print(f"Sent {template_type} to {lead.first_name} at {lead.company}")
        except Exception as e:
            print(f"Error sending follow-up: {e}")
    
    def generate_lead_report(self):
        """Generate a lead nurturing report"""
        total_leads = len(self.leads)
        contacted = sum(1 for lead in self.leads.values() if lead.status != 'new')
        responded = sum(1 for lead in self.leads.values() if lead.response_count > 0)
        interested = sum(1 for lead in self.leads.values() if lead.status == 'interested')
        
        print(f"\n📊 LEAD NURTURING REPORT")
        print(f"Total Leads: {total_leads}")
        print(f"Contacted: {contacted}")
        print(f"Responded: {responded}")
        print(f"Interested: {interested}")
        print(f"Response Rate: {(responded/contacted*100):.1f}%" if contacted > 0 else "Response Rate: N/A")
        print(f"Interest Rate: {(interested/responded*100):.1f}%" if responded > 0 else "Interest Rate: 0%")
        
        # Top leads by score
        top_leads = sorted(self.leads.values(), key=lambda x: x.lead_score, reverse=True)[:5]
        print(f"\n🏆 TOP LEADS BY SCORE:")
        for lead in top_leads:
            print(f"  {lead.first_name} at {lead.company} - Score: {lead.lead_score}")
    
    def run_nurturing_cycle(self):
        """Run the complete nurturing cycle"""
        print("🔄 Starting lead nurturing cycle...")
        
        # Check for responses
        print("📧 Checking for responses...")
        self.check_for_responses()
        
        # Run follow-up sequence
        print("📤 Running follow-up sequence...")
        self.run_follow_up_sequence()
        
        # Save updated data
        self._save_leads()
        # Persist sync state already handled in check_for_responses
        
        # Generate report
        self.generate_lead_report()
        
        print("✅ Nurturing cycle complete!")

if __name__ == "__main__":
    nurturer = LeadNurturer()
    nurturer.run_nurturing_cycle()
