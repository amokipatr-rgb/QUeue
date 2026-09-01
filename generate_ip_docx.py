from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import re

doc = Document()

# Configure default font
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)

# Title page
doc.add_paragraph()
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('SMART QUEUE MANAGEMENT SYSTEM')
run.bold = True
run.font.size = Pt(24)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('(SMQSS)')
run.bold = True
run.font.size = Pt(18)

doc.add_paragraph()

inventor = doc.add_paragraph()
inventor.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = inventor.add_run('INVENTION DISCLOSURE DOCUMENT')
run.font.size = Pt(14)

doc.add_paragraph()

author = doc.add_paragraph()
author.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = author.add_run('Inventor: Ogwal Richard')
run.font.size = Pt(12)

author2 = doc.add_paragraph()
author2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = author2.add_run('Student Number: 2300716574')
run.font.size = Pt(12)

advisor = doc.add_paragraph()
advisor.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = advisor.add_run('Advisor: Odongo Steven Eyobu (PhD)')
run.font.size = Pt(12)

university = doc.add_paragraph()
university.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = university.add_run('Makerere University')
run.font.size = Pt(12)

date_p = doc.add_paragraph()
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date_p.add_run('August 2026')
run.font.size = Pt(12)

doc.add_page_break()

# Table of Contents
doc.add_heading('Table of Contents', level=1)
toc_items = [
    '1. Title of the Invention',
    '2. Field of the Invention',
    '3. Background of the Invention',
    '4. Summary of the Invention',
    '5. Brief Description of Drawings',
    '6. Detailed Description of Preferred Embodiments',
    '7. Claims (10 Claims)',
    '8. Abstract of the Disclosure',
    '9. Inventor Declaration',
]
for item in toc_items:
    doc.add_paragraph(item, style='List Number')

doc.add_page_break()

# Section 1: Title
doc.add_heading('1. Title of the Invention', level=1)
doc.add_paragraph('SMART QUEUE MANAGEMENT SYSTEM WITH AI-POWERED ANALYTICS, MULTI-PLATFORM KIOSK ARCHITECTURE, AND REAL-TIME VOICE-ENABLED PUBLIC DISPLAYS')

# Section 2: Field
doc.add_heading('2. Field of the Invention', level=1)
doc.add_paragraph('The present invention relates to queue management systems, and more particularly to a smart queue management system integrating artificial intelligence, multi-platform kiosk terminals, real-time public displays with voice announcements, and an administrative dashboard for educational institutions.')

# Section 3: Background
doc.add_heading('3. Background of the Invention', level=1)
doc.add_paragraph('Traditional queue management in educational institutions relies on manual token distribution, paper-based tracking, and verbal announcements. These approaches suffer from:')
problems = [
    'No real-time visibility into queue status for students or administrators',
    'Manual attendance tracking prone to errors and time manipulation',
    'No data-driven insights for service improvement',
    'Fragmented feedback collection with no structured follow-up',
    'Limited accessibility for students with disabilities',
]
for p in problems:
    doc.add_paragraph(p, style='List Bullet')

doc.add_paragraph('Existing commercial queue systems are expensive, proprietary, not designed for educational contexts, and lack AI-powered analytics, voice announcements, and multi-platform kiosk support.')

# Section 4: Summary
doc.add_heading('4. Summary of the Invention', level=1)
doc.add_paragraph('The SMQSS addresses these limitations through:')
features = [
    'Per-day first-free token numbering with gap-aware restart',
    'AI-powered attendance analysis, feedback correlation, and complaint response using LLMs',
    'Real-time public displays with adaptive voice announcements and character spelling',
    'Multi-platform architecture (Electron desktop, web, React Native mobile)',
    'Rate-before-next-token enforcement with QR-coded feedback receipts',
    'Office-hours clamping (8AM-5PM) with dynamic monthly target computation',
    'Three-metric heatmap analytics and tokens-per-hour efficiency metrics',
    'Crash recovery, silent receipt printing, and self-healing database migration',
]
for f in features:
    doc.add_paragraph(f, style='List Bullet')

# Section 5: Drawings
doc.add_heading('5. Brief Description of Drawings', level=1)
drawings = [
    'Figure 1: System Architecture Overview',
    'Figure 2: Token Lifecycle State Diagram',
    'Figure 3: Public Display with Voice Announcement Flow',
    'Figure 4: Officer Dashboard and Attendance Tracking',
    'Figure 5: AI Integration and Analytics Pipeline',
    'Figure 6: Multi-Platform Kiosk Deployment',
    'Figure 7: Database Schema and Migration Flow',
    'Figure 8: Receipt Generation with QR Code',
]
for d in drawings:
    doc.add_paragraph(d, style='List Bullet')

# Section 6: Detailed Description
doc.add_heading('6. Detailed Description of Preferred Embodiments', level=1)

doc.add_heading('6.1 System Architecture', level=2)
doc.add_paragraph('The SMQSS comprises a centralized Flask backend serving REST APIs to multiple frontend platforms. The backend handles token generation, queue management, attendance tracking, feedback collection, AI analytics, voice announcement generation, and administrative functions.')

doc.add_heading('6.2 Token Lifecycle Management', level=2)
doc.add_paragraph('Tokens are generated with per-day first-free numbering. The system queries existing tokens for the current date, extracts numeric suffixes, identifies the first unused number in the sequence, and assigns the token with an office code prefix and zero-padded numeric suffix. A unique constraint on (token_number, token_date) prevents duplicates. Queue reset operations atomically expire waiting tokens, delete expired/skipped tokens, and return the predicted next token number by identifying the first gap in the used number sequence.')

doc.add_heading('6.3 AI Integration', level=2)
doc.add_paragraph('The system integrates a large language model (LLM) for three primary functions: (1) attendance analysis generating natural-language reports with per-officer observations; (2) feedback-officer correlation analysis identifying patterns and improvement recommendations; and (3) complaint response polishing with selectable tone parameters. Monthly grades are computed based on actual working days, with the target dynamically calculated as 540 minutes multiplied by weekdays in the month.')

doc.add_heading('6.4 Public Display and Voice Announcements', level=2)
doc.add_paragraph('The public display receives queue data at regular polling intervals. An adaptive token preview algorithm adjusts the number of preview tokens based on active office count: 3+ offices show 1 next per office; 2 offices show 2 next per office; 1 office shows 3 next tokens. Voice announcements spell token characters individually, concatenate batches into grammatically correct sentences, and deduplicate using composite keys with configurable cooldown.')

doc.add_heading('6.5 Multi-Platform Kiosk Architecture', level=2)
doc.add_paragraph('The system supports three kiosk platforms: Electron desktop (fullscreen, frameless, crash recovery, silent printing), web-based (virtual keyboard adaptation), and React Native/Expo mobile. All platforms communicate with the centralized server through REST API endpoints. The Electron implementation includes a 30-attempt load retry, 30-second watchdog timer, and automatic window recreation on close events.')

doc.add_heading('6.6 Attendance and Analytics', level=2)
doc.add_paragraph('Attendance is calculated using first-login/last-logout with office-hours clamping (8AM-5PM). Multiple daily sessions are merged by taking min(login) and max(logout). Four distinct time metrics are computed: turnaround, service, queue wait, and call response. Three-metric heatmap analytics provide hourly breakdowns of token creation, average wait, and officer presence. Tokens-per-hour efficiency equals daily served tokens multiplied by 60 divided by daily logged-in minutes.')

doc.add_heading('6.7 Security and Infrastructure', level=2)
doc.add_paragraph('Route protection uses token-based URL paths with decoy redirects for unauthorized access attempts. Officer tokens persist to disk; admin and feedback tokens are ephemeral per server start. The database auto-migration system creates tables, adds columns, creates indexes, drops/recreates constraints, backfills data, and seeds defaults on every startup. Geographic IP resolution distinguishes private addresses (Local Network) from public addresses resolved to city, region, country, and GPS coordinates.')

# Section 7: Claims
doc.add_heading('7. Claims', level=1)

claims = [
    {
        'title': 'Claim 1 (Independent) — AI-Integrated Queue Management System',
        'text': 'A computer-implemented method for AI-integrated queue management in an educational institution, comprising: receiving token generation requests from a student kiosk terminal; generating queue tokens with per-day first-free numbering; storing token records in a database; transmitting queue data to a real-time public display; receiving officer service actions from an officer dashboard; processing feedback submissions from a feedback interface; and analyzing queue performance data using a large language model (LLM) to generate attendance reports, feedback-officer correlations, and complaint response recommendations, wherein the AI analysis includes per-officer anomaly detection with monthly grade computation based on actual working days in the month, where the monthly target is dynamically calculated as 540 minutes multiplied by the number of weekdays in the current month; wherein complaint replies are polished by the AI with a selectable tone parameter selected from the group consisting of professional, empathetic, formal, and friendly, constrained to 200 words maximum, preserving factual accuracy, and excluding markdown formatting; wherein the AI feedback-officer correlation analysis receives token-based feedback data, per-officer statistics, and general complaint records, and generates pattern analysis identifying improvement recommendations with specific officer identifiers; and wherein the AI attendance analysis receives structured attendance data including login/logout times, tokens served, availability percentages, and monthly grades, and generates a natural-language report with per-officer observations and actionable recommendations.'
    },
    {
        'title': 'Claim 2 (Independent) — Real-Time Public Display with Adaptive Voice Announcements',
        'text': 'A system for real-time public queue display comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; a voice announcement subsystem generating contextual audio messages for called, recalled, and serving tokens; an adaptive token preview algorithm dynamically adjusting the number of preview tokens displayed based on the count of active offices; and a screen health monitor detecting data staleness, API silence, and JavaScript errors to trigger safe reload operations, wherein the voice announcement subsystem spells token characters individually (e.g., "A R 0 1" for "AR01") and concatenates multiple token announcements into grammatically correct sentences using conjunction words for the final item in a batch; wherein the adaptive token preview algorithm assigns preview token counts as: three or more active offices display one next token per office; two active offices display two next tokens per office; and one active office displays three next tokens; wherein the screen health monitor executes at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations; and wherein voice announcements are deduplicated using a composite key comprising token number, office name, and action type, with a configurable cooldown period preventing repeated announcements of the same token-office-action combination.'
    },
    {
        'title': 'Claim 3 (Independent) — Per-Day First-Free Token Lifecycle Management',
        'text': 'A computer-implemented method for token lifecycle management in a queue system, comprising: generating tokens with per-day first-free numbering by querying existing tokens for the current date, extracting numeric suffixes, identifying the first unused number in the sequence, and assigning the token with office code prefix and zero-padded numeric suffix; enforcing a unique constraint on the combination of token number and token date; and supporting queue reset operations that atomically expire waiting tokens, delete expired tokens, and return the predicted next token number, wherein the queue reset operation performs three atomic operations: setting status to \'expired\' for all waiting and called tokens, deleting expired and skipped tokens from the current day, and calculating the next available token number by identifying the first gap in the used number sequence; wherein priority tokens generated for parent service requests (service code \'PS\') are sorted before standard tokens in the queue display and serving order, with priority status indicated visually on the receipt and public display; further comprising rate-before-next-token enforcement, wherein a student with an unrated completed token is blocked from generating a new token until the previous token\'s feedback is submitted, the blocked state displaying the unrated token number and a direct link to the feedback submission page; wherein an office availability gate prevents an administrator from marking an office as unavailable when students are currently waiting, returning a refusal message with the count of waiting students; and wherein batch operations allow calling, serving, or completing up to ten tokens simultaneously, with the batch size configurable between one and ten, and each operation incrementing a tokens-served counter on the officer\'s active session record.'
    },
    {
        'title': 'Claim 4 (Independent) — Attendance Tracking with Office-Hours Clamping and Analytics',
        'text': 'A system for attendance tracking in a queue management environment, comprising: recording officer login and logout events with timestamps; calculating daily attendance using a first-login/last-logout method where the effective start time is clamped to no earlier than 8:00 AM and the effective end time is clamped to no later than 5:00 PM; merging multiple sessions within a single day by taking the minimum login time and maximum logout time; and computing monthly attendance targets dynamically based on the actual number of working days in the month, wherein the monthly attendance target is computed by counting the number of days in the current month where the day of the week is Monday through Friday, and multiplying by 540 minutes (9 hours); further comprising computation of four distinct time metrics: turnaround time (request to completion), service time (service start to completion), queue wait time (request to service start), and call response time (call to service start); further comprising three-metric heatmap analytics providing hourly breakdowns of token creation count, average wait duration, and distinct officer presence per office per day, with peak hour and busiest office identification; and further comprising a tokens-per-hour efficiency metric computed as the total daily served tokens multiplied by 60 and divided by the total daily logged-in minutes, providing a measure of officer productivity.'
    },
    {
        'title': 'Claim 5 (Independent) — Multi-Platform Kiosk Architecture with Crash Recovery',
        'text': 'A multi-platform kiosk system for queue management, comprising: an Electron desktop application configured in fullscreen kiosk mode with frameless window, always-on-top positioning, and display sleep prevention; a web-based interface with virtual keyboard detection and automatic layout adaptation; and a mobile application built with React Native/Expo providing real-time queue display; all platforms communicating with a centralized server through REST API endpoints, wherein the Electron desktop application implements crash recovery comprising: monitoring renderer process crashed and unresponsive events with 2-second delayed restart; implementing a 30-attempt load retry with 3-second intervals; running a watchdog timer every 30 seconds testing renderer responsiveness; and recreating the window automatically upon window close events when the application is not in a quitting state; wherein the Electron desktop application implements silent receipt printing by scanning available printers for name patterns matching "POSPrinter" or "80C", falling back to an environment variable for printer name, and printing with silent mode, background graphics enabled, no margins, and no header/footer; wherein the feedback interface tracks the originating kiosk type using a URL query parameter (e.g., ?from=kiosk-B), and after feedback submission, redirects the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present; and wherein the kiosk auto-configuration comprises a PowerShell script that: checks Chrome installation across multiple file paths; sets the AutoplayAllowed registry key; creates a Chrome kiosk shortcut with --kiosk --autoplay-policy=no-user-gesture-required flags; adds the shortcut to the Windows Startup folder; and implements cursor auto-hiding after 3 seconds of inactivity.'
    },
    {
        'title': 'Claim 6 (Independent) — Token-Based Route Protection with Self-Healing Database',
        'text': 'A token-based route protection system for a web application, comprising: generating an officer token persisted to a file on disk for persistent authentication; generating admin and feedback tokens as ephemeral secrets per server start; embedding tokens in URL paths for protected routes (e.g., /admin/{token}, /officer/{token}, /feedback.html/{token}); implementing decoy routes that redirect unauthorized access attempts; and providing a token lookup endpoint for authenticated token retrieval, wherein decoy routes for /admin, /officer, /login, /workflow, and /feedback.html (without token) redirect to the application landing page, preventing direct access to protected pages without valid tokens; further comprising a self-healing database auto-migration system that on server startup: creates missing tables, adds missing columns via ALTER TABLE, creates missing indexes, drops and recreates unique constraints, backfills new columns from existing data, and seeds default data for empty tables, all operations being idempotent; and further comprising geographic IP resolution for officer login tracking, wherein private IP addresses (127.x, 192.168.x, 10.x, 172.x) are identified as "Local Network" and public IP addresses are resolved to city, region, country, and GPS coordinates using an external geolocation service, with results stored in the officer session record.'
    },
    {
        'title': 'Claim 7 (Independent) — Kiosk-Type-Aware Feedback Redirect System',
        'text': 'A feedback redirect system for a multi-kiosk queue management environment, comprising: generating a receipt with a feedback URL encoded with a kiosk-type query parameter (e.g., /r/{token}?from=kiosk-B); encoding the same URL as a QR code on the receipt; upon QR code scan or URL access, redirecting to a feedback page that reads the kiosk-type parameter; processing feedback submission on the feedback page; and after submission, redirecting the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present, wherein the kiosk-type parameter propagates through all redirect hops to ensure the user returns to the correct kiosk interface after feedback completion.'
    },
    {
        'title': 'Claim 8 (Independent) — Voice Announcement Batch Concatenation and Deduplication',
        'text': 'A voice announcement subsystem for a queue management display, comprising: receiving a batch of token numbers to announce; spelling each token character individually (e.g., "A R 0 1" for "AR01"); concatenating multiple token announcements into a single grammatically correct sentence using conjunction words for the final item in a batch (e.g., "Tokens A R 0 1, A R 0 2, and A R 0 3, please go to Admissions Office"); generating contextual announcement types for called, recalled, and serving tokens with distinct templates; deduplicating announcements using a composite key comprising token number, office name, and action type; applying a configurable cooldown period preventing repeated announcements of the same token-office-action combination; and queuing announcements sequentially in an audio playback queue to prevent announcement overlap, ensuring each announcement completes before the next begins.'
    },
    {
        'title': 'Claim 9 (Independent) — Rate-Before-Next-Token Enforcement with QR-Coded Receipt',
        'text': 'A rate-before-next-token enforcement system for a queue management environment, comprising: upon service completion, generating a receipt containing a QR code encoding a feedback URL; displaying a mandatory notice on the receipt indicating that rating is required before requesting a new token; upon subsequent token generation request, checking whether the student has any unrated completed tokens; if an unrated token exists, blocking the new token generation and displaying the unrated token number with a direct link to the feedback submission page; and upon feedback submission for the unrated token, unblocking token generation and allowing the student to proceed, wherein the feedback URL encodes the originating kiosk type to ensure redirect to the correct kiosk after submission.'
    },
    {
        'title': 'Claim 10 (Independent) — Adaptive Display with Dynamic Preview and Screen Health Monitoring',
        'text': 'A public display system for queue management, comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; an adaptive token preview algorithm that dynamically adjusts the number of preview tokens displayed based on the count of active offices, wherein three or more active offices display one next token per office, two active offices display two next tokens per office, and one active office displays three next tokens; a screen health monitor executing at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations; and a voice announcement subsystem that generates contextual audio messages, spells token characters individually, concatenates multiple token announcements into grammatically correct sentences, deduplicates announcements using a composite key, and queues announcements sequentially to prevent overlap.'
    },
]

for claim in claims:
    doc.add_heading(claim['title'], level=2)
    doc.add_paragraph(claim['text'])

# Section 8: Abstract
doc.add_heading('8. Abstract of the Disclosure', level=1)
doc.add_paragraph('A smart queue management system comprising an AI-powered Flask backend, multi-platform kiosk terminals (Electron desktop, web, Android mobile), real-time public displays with voice announcements, and an administrative dashboard. The system implements per-day first-free token numbering with gap-aware restart, adaptive display with dynamic preview counts, voice announcements with token character spelling and batch concatenation, AI-powered attendance analysis and feedback correlation, rate-before-next-token enforcement, and kiosk-type-aware feedback redirect tracking. The system supports crash recovery, silent receipt printing, geographic IP tracking, and self-healing database migration.')

# Section 9: Declaration
doc.add_heading('9. Inventor Declaration', level=1)
doc.add_paragraph('I, Ogwal Richard, hereby declare that I am the original inventor of the Smart Queue Management System (SMQSS) described in this document, developed under the supervision of Odongo Steven Eyobu (PhD) at Makerere University. All claims herein are based on original research and development conducted between January 2025 and August 2026.')

doc.add_paragraph()
doc.add_paragraph('Inventor: Ogwal Richard')
doc.add_paragraph('Student Number: 2300716574')
doc.add_paragraph('Signature: ________________________')
doc.add_paragraph('Date: ________________________')
doc.add_paragraph()
doc.add_paragraph('Advisor: Odongo Steven Eyobu (PhD)')
doc.add_paragraph('Signature: ________________________')
doc.add_paragraph('Date: ________________________')
doc.add_paragraph()
doc.add_paragraph('Document prepared for intellectual property protection under the Uganda Industrial Property Act, 2003 and the ARIPO Harare Protocol on Patents.')

# Save
doc.save('SMQSS_IP_PATENT.docx')
print('DOCX generated successfully: SMQSS_IP_PATENT.docx')
