#!/usr/bin/env python3
"""Generate clean DOCX for IP_DOCUMENT.md and IP_CLAIMS_ONLY.md"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
import re

def setup_styles(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.5

    for level in range(1, 4):
        heading = doc.styles[f'Heading {level}']
        heading.font.name = 'Times New Roman'
        heading.font.color.rgb = RGBColor(0, 0, 0)
        heading.font.bold = True
        if level == 1:
            heading.font.size = Pt(16)
            heading.paragraph_format.space_before = Pt(24)
            heading.paragraph_format.space_after = Pt(12)
        elif level == 2:
            heading.font.size = Pt(14)
            heading.paragraph_format.space_before = Pt(18)
            heading.paragraph_format.space_after = Pt(8)
        else:
            heading.font.size = Pt(12)
            heading.paragraph_format.space_before = Pt(12)
            heading.paragraph_format.space_after = Pt(6)

def add_title_page(doc):
    for _ in range(4):
        doc.add_paragraph('')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('INTELLECTUAL PROPERTY DOCUMENT')
    run.bold = True
    run.font.size = Pt(20)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('SMART QUEUE MANAGEMENT SYSTEM (SMQSS)')
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('A System and Method for AI-Integrated Queue Management\nwith Real-Time Voice Announcements, Adaptive Display,\nand Multi-Platform Kiosk Architecture')
    run.font.size = Pt(14)
    run.font.name = 'Times New Roman'

    doc.add_paragraph('')
    doc.add_paragraph('')

    info = [
        ('Application Type:', 'Software Patent / Utility Model'),
        ('Filing Jurisdiction:', 'Uganda Registration Services Bureau (URSB) / ARIPO'),
        ('Inventor:', 'Ogwal Richard (Student Number: 2300716574)'),
        ('Advisor:', 'Odongo Steven Eyobu (PhD)'),
        ('Institution:', 'Makerere University, College of Computing and Information Sciences'),
        ('Version:', '2.1.0'),
        ('Date:', 'August 2026'),
    ]

    for label, value in info:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(label + ' ')
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'
        run = p.add_run(value)
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

    doc.add_page_break()

def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(10)
                run.font.name = 'Times New Roman'

    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_text in enumerate(row_data):
            cell = table.rows[row_idx + 1].cells[col_idx]
            cell.text = cell_text
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
                    run.font.name = 'Times New Roman'

def add_code_block(doc, code):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    run = p.add_run(code)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)

def add_claim(doc, number, text, independent=False):
    label = f'Claim {number}'
    if independent:
        label += ' (Independent)'

    p = doc.add_paragraph()
    run = p.add_run(label)
    run.bold = True
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph(text)
    p.paragraph_format.left_indent = Cm(1)
    for run in p.runs:
        run.font.size = Pt(12)
        run.font.name = 'Times New Roman'

def generate_full_doc():
    doc = Document()
    setup_styles(doc)
    add_title_page(doc)

    doc.add_heading('1. ABSTRACT', level=1)
    doc.add_paragraph(
        'A smart queue management system (SMQSS) comprising an AI-powered backend server, '
        'multi-platform kiosk terminals, real-time public display screens, and an officer dashboard, '
        'all communicating through a centralized hub-and-spoke architecture. The system introduces '
        'novel methods for per-day first-free token numbering with gap-aware restart, adaptive public '
        'display with dynamic token preview counts based on active office density, voice announcements '
        'using token character spelling with batch concatenation, AI-integrated attendance analysis with '
        'anomaly detection, and a rate-before-next-token enforcement mechanism. The system supports '
        'Electron desktop kiosks with crash recovery and silent receipt printing, web-based interfaces '
        'with virtual keyboard adaptation, and Android mobile applications, all synchronized to server '
        'time in the Africa/Nairobi timezone.'
    )
    p = doc.add_paragraph()
    run = p.add_run('Keywords: ')
    run.bold = True
    run.font.name = 'Times New Roman'
    run = p.add_run('Queue management, artificial intelligence, token system, voice announcements, '
                     'real-time display, kiosk, attendance tracking, Electron, Python, Flask')
    run.font.name = 'Times New Roman'

    doc.add_heading('2. FIELD OF INVENTION', level=1)
    doc.add_paragraph(
        'The present invention relates to the field of queue management systems, specifically to '
        'computer-implemented methods and systems for managing service queues in educational '
        'institutions, government offices, and public service centers. More particularly, the invention '
        'relates to AI-integrated queue management with real-time voice announcements, adaptive display '
        'algorithms, multi-platform kiosk architecture, and comprehensive attendance analytics.'
    )

    doc.add_heading('3. BACKGROUND OF THE INVENTION', level=1)
    doc.add_heading('3.1 Prior Art', level=2)
    doc.add_paragraph(
        'Traditional queue management systems suffer from several limitations:'
    )
    limitations = [
        ('Static Token Numbering:', 'Existing systems use sequential numbering that does not account for queue resets, leading to confusion when tokens are expired or skipped.'),
        ('Passive Display Systems:', 'Current public displays show fixed information without adapting to real-time conditions such as the number of active offices or current queue density.'),
        ('No AI Integration:', 'Prior art systems lack artificial intelligence capabilities for analyzing attendance patterns, correlating feedback with officer performance, and generating intelligent complaint responses.'),
        ('Limited Voice Support:', 'Existing voice announcement systems use simple text-to-speech without optimization for token number pronunciation, batch announcement concatenation, or deduplication.'),
        ('Single-Platform Limitation:', 'Most queue systems are designed for a single platform (web or desktop) without supporting multi-platform deployment across Electron desktop apps, web browsers, and mobile devices.'),
        ('No Rate Enforcement:', 'Existing systems do not enforce feedback submission before allowing new token generation, leading to low feedback response rates.'),
    ]
    for title, desc in limitations:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(title + ' ')
        run.bold = True
        run.font.name = 'Times New Roman'
        run = p.add_run(desc)
        run.font.name = 'Times New Roman'

    doc.add_heading('3.2 Deficiencies in Prior Art', level=2)
    add_table(doc,
        ['Deficiency', 'Prior Art Approach', 'Present Invention'],
        [
            ['Token numbering', 'Sequential, no reset handling', 'Per-day first-free with gap-aware restart'],
            ['Display adaptation', 'Fixed layout', 'Dynamic preview count based on active office density'],
            ['AI integration', 'None', 'LLM-powered attendance analysis, feedback correlation, complaint polishing'],
            ['Voice announcements', 'Basic TTS', 'Character spelling, batch concatenation, deduplication, audio queue'],
            ['Platform support', 'Single platform', 'Electron + Web + Android mobile'],
            ['Feedback enforcement', 'Optional', 'Rate-before-next-token blocking with direct feedback linking'],
            ['Attendance tracking', 'Simple login/logout', 'First-login/last-logout clamped to office hours with multi-session merging'],
            ['Crash recovery', 'Basic restart', '30-attempt retry, watchdog timer, window recreation, cache clearing'],
        ]
    )

    doc.add_heading('4. SUMMARY OF THE INVENTION', level=1)
    doc.add_paragraph(
        'The present invention provides a smart queue management system comprising:'
    )
    summaries = [
        'A centralized Flask-based backend server with MySQL database, implementing per-day first-free token numbering, attendance calculation with office-hours clamping, and AI-powered analytics through GROQ LLM integration.',
        'Multi-platform kiosk terminals including Electron desktop applications with crash recovery, silent receipt printing, and kiosk mode; web-based interfaces with virtual keyboard adaptation; and Android mobile applications built with React Native/Expo.',
        'Real-time public display screens with adaptive token preview algorithms, contextual voice announcements using edge-tts with token character spelling, batch concatenation, and deduplication.',
        'An officer dashboard with PIN authentication, batch token operations (call/serve/complete up to 10 tokens), status logging, and peer rating capabilities.',
        'A feedback system with QR-coded receipts, opaque URL redirects, rate-before-next-token enforcement, and kiosk-type-aware redirect tracking.',
        'An administrative dashboard with AI-powered attendance analysis, feedback-officer correlation, complaint management with AI-polished responses, heatmap analytics, and multi-week trend analysis.',
    ]
    for i, s in enumerate(summaries, 1):
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(chr(64 + i) + '. ')
        run.bold = True
        run.font.name = 'Times New Roman'
        run = p.add_run(s)
        run.font.name = 'Times New Roman'

    doc.add_heading('5. BRIEF DESCRIPTION OF DRAWINGS', level=1)
    add_table(doc,
        ['Figure', 'Description'],
        [
            ['FIG. 1', 'System Architecture Diagram - Hub-and-spoke architecture with Flask server as central hub'],
            ['FIG. 2', 'Token Lifecycle Flowchart - From generation through service completion and feedback'],
            ['FIG. 3', 'Adaptive Display Algorithm - Dynamic preview count calculation based on active office count'],
            ['FIG. 4', 'Attendance Calculation Flowchart - First-login/last-logout with office-hours clamping'],
            ['FIG. 5', 'AI Integration Diagram - GROQ LLM interfaces for attendance, feedback, and complaints'],
            ['FIG. 6', 'Multi-Platform Architecture - Electron, Web, and Mobile component relationships'],
            ['FIG. 7', 'Voice Announcement Pipeline - TTS generation, deduplication, and audio queue management'],
            ['FIG. 8', 'Kiosk Crash Recovery State Machine - Retry, watchdog, and window recreation logic'],
            ['FIG. 9', 'Feedback Flow with Kiosk Tracking - QR code, redirect, rating, kiosk-type-aware return'],
            ['FIG. 10', 'Database Schema - Entity relationship diagram for token, officer, session, and feedback tables'],
        ]
    )

    doc.add_page_break()
    doc.add_heading('6. DETAILED DESCRIPTION', level=1)

    doc.add_heading('6.1 System Architecture', level=2)
    doc.add_paragraph(
        'The SMQSS system employs a hub-and-spoke architecture where a centralized Flask server '
        '(app.py, approximately 5,000 lines) manages all state and communication. Six interconnected '
        'components communicate exclusively through REST API endpoints:'
    )
    components = [
        ('Student Kiosk', '3-step guided wizard with AI assistant typewriter interface for token generation.'),
        ('Public Display', 'TV-optimized real-time display with voice announcements, news ticker, and recall banners.'),
        ('Officer Dashboard', 'PIN-authenticated interface for queue operations including batch call/serve/complete.'),
        ('Admin Dashboard', 'CRUD operations, analytics, attendance monitoring, and AI-powered analysis.'),
        ('Feedback System', 'Token-lookup rating interface with typewriter AI guidance and kiosk-type-aware redirects.'),
        ('Mobile Application', 'React Native/Expo application mirroring the public display for Android devices.'),
    ]
    for i, (name, desc) in enumerate(components, 1):
        p = doc.add_paragraph(style='List Number')
        run = p.add_run(name + ': ')
        run.bold = True
        run.font.name = 'Times New Roman'
        run = p.add_run(desc)
        run.font.name = 'Times New Roman'

    doc.add_heading('6.2 Per-Day First-Free Token Numbering (Claim 11)', level=2)
    doc.add_paragraph(
        'The system implements a novel token numbering algorithm that ensures gap-free numbering '
        'within each day while supporting queue resets:'
    )
    p = doc.add_paragraph()
    run = p.add_run('Algorithm:')
    run.bold = True
    run.font.name = 'Times New Roman'
    add_code_block(doc, (
        '1. Query all token numbers for the given office on the current date\n'
        '2. Extract numeric suffix from each token number (e.g., "AR" + "01" -> 1)\n'
        '3. Build set of used numbers\n'
        '4. Starting from 1, find first unused number\n'
        '5. Assign token: office_code + padded_number (e.g., "AR01")\n'
        '6. Unique constraint: (token_number, token_date) -- per-day uniqueness only'
    ))
    doc.add_paragraph(
        'This approach allows queue resets to recycle numbers from the beginning rather than '
        'continuing from the last assigned number, preventing confusion when tokens are expired or skipped.'
    )

    doc.add_heading('6.3 Adaptive Public Display Algorithm (Claim 8)', level=2)
    doc.add_paragraph(
        'The public display implements a dynamic "Up Next" preview algorithm that adjusts the number '
        'of preview tokens based on the density of active offices:'
    )
    add_code_block(doc, (
        'Active offices >= 3: Show 1 next token per office\n'
        'Active offices = 2: Show 2 next tokens per office\n'
        'Active offices = 1: Show 3 next tokens per office'
    ))
    doc.add_paragraph(
        'This algorithm ensures that the display remains balanced and informative regardless of how '
        'many offices are currently serving students, preventing information overload when many offices '
        'are active and maximizing useful information when few offices are active.'
    )

    doc.add_heading('6.4 Voice Announcement Pipeline (Claims 6-10)', level=2)
    doc.add_paragraph(
        'The voice announcement system implements a multi-stage pipeline:'
    )

    stages = [
        ('Stage 1: Token Spelling', 'Token numbers are character-spoken for clarity: "AR01" -> "A R 0 1".'),
        ('Stage 2: Contextual Message Generation', 'Three announcement types with distinct templates:\n'
         '- Called: "Token [N], please go to [Office]"\n'
         '- Recall: "Token [N], please return to [Office]"\n'
         '- Serving: "Token [N], you are now being served at [Office]"'),
        ('Stage 3: Batch Concatenation', 'Multiple tokens are concatenated into a single grammatically correct sentence: '
         '"Tokens A R 0 1, A R 0 2, and A R 0 3, please go to Admissions Office."'),
        ('Stage 4: Deduplication', 'Recent announcements tracked with composite key token|officeName|actionType '
         'and 1-second cooldown prevent duplicate announcements.'),
        ('Stage 5: Audio Queue', 'Sequential audio playback queue using invisible video elements prevents '
         'announcement overlap, ensuring each announcement completes before the next begins.'),
    ]
    for title, desc in stages:
        p = doc.add_paragraph()
        run = p.add_run(title + ': ')
        run.bold = True
        run.font.name = 'Times New Roman'
        run = p.add_run(desc)
        run.font.name = 'Times New Roman'

    doc.add_heading('6.5 Attendance Calculation (Claims 17-21)', level=2)
    doc.add_paragraph(
        'The attendance system implements a sophisticated calculation that handles multiple sessions per day:'
    )
    p = doc.add_paragraph()
    run = p.add_run('Algorithm:')
    run.bold = True
    run.font.name = 'Times New Roman'
    add_code_block(doc, (
        'For each day:\n'
        '  1. Collect all login/logout times across all sessions\n'
        '  2. first_login = min(all logins)\n'
        '  3. last_logout = max(all logouts)\n'
        '  4. effective_start = max(first_login, 8:00 AM)\n'
        '  5. effective_end = min(last_logout, 5:00 PM)\n'
        '  6. duration = max(0, (effective_end - effective_start).total_seconds() / 60)'
    ))
    p = doc.add_paragraph()
    run = p.add_run('Monthly Target Calculation:')
    run.bold = True
    run.font.name = 'Times New Roman'
    add_code_block(doc, (
        'days_in_month = calendar.monthrange(year, month)[1]\n'
        'working_days = count of days where weekday < 5 (Mon-Fri)\n'
        'monthly_target = 540 minutes x working_days'
    ))
    p = doc.add_paragraph()
    run = p.add_run('Four Distinct Time Metrics:')
    run.bold = True
    run.font.name = 'Times New Roman'
    metrics = [
        'avg_turnaround_minutes: requested_at -> completed_at',
        'avg_service_minutes: serving_started_at -> completed_at',
        'avg_queue_wait_before_service_minutes: requested_at -> serving_started_at',
        'avg_response_after_call_minutes: called_at -> serving_started_at',
    ]
    for m in metrics:
        p = doc.add_paragraph(m, style='List Bullet')
        for run in p.runs:
            run.font.name = 'Times New Roman'

    doc.add_heading('6.6 AI Integration (Claims 1-5)', level=2)
    doc.add_paragraph(
        'The system integrates GROQ LLM (model: openai/gpt-oss-120b) for three distinct AI-powered functions:'
    )
    ai_funcs = [
        ('AI Complaint Reply Generation:', 'Admin drafts are polished by AI with selectable tone '
         '(professional, empathetic, formal, friendly), constrained to 200 words, no markdown, fact-preserving.'),
        ('AI Weekly Attendance Analysis:', 'Structured officer attendance data (login/logout times, tokens served, '
         'availability percentages, monthly grades) is formatted and sent to AI for natural-language report '
         'with per-officer observations, anomaly detection, and actionable recommendations.'),
        ('AI Feedback-Officer Correlation Analysis:', 'Token-based feedback, per-officer statistics, and '
         'general complaints are correlated by AI for pattern analysis and improvement recommendations.'),
    ]
    for title, desc in ai_funcs:
        p = doc.add_paragraph()
        run = p.add_run(title + ' ')
        run.bold = True
        run.font.name = 'Times New Roman'
        run = p.add_run(desc)
        run.font.name = 'Times New Roman'

    doc.add_heading('6.7 Multi-Platform Kiosk Architecture (Claims 22-26)', level=2)

    p = doc.add_paragraph()
    run = p.add_run('Electron Desktop Kiosk:')
    run.bold = True
    run.font.name = 'Times New Roman'
    electron_items = [
        'Fullscreen frameless always-on-top window',
        'powerSaveBlocker.start("prevent-display-sleep") for continuous display',
        'Crash recovery with 30-attempt retry at 3-second intervals',
        'Watchdog timer testing renderer responsiveness every 30 seconds',
        'HTTP cache clearing on startup for fresh content',
        'Silent POS receipt printing with automatic printer detection',
    ]
    for item in electron_items:
        p = doc.add_paragraph(item, style='List Bullet')
        for run in p.runs:
            run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    run = p.add_run('Web Interface:')
    run.bold = True
    run.font.name = 'Times New Roman'
    web_items = [
        'Virtual keyboard detection via window.visualViewport.resize',
        'Automatic layout restructuring when keyboard opens',
        'scrollInputIntoView() for focused input visibility',
    ]
    for item in web_items:
        p = doc.add_paragraph(item, style='List Bullet')
        for run in p.runs:
            run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    run = p.add_run('Android Mobile:')
    run.bold = True
    run.font.name = 'Times New Roman'
    mobile_items = [
        'React Native/Expo application with same layout as TV display',
        'Real-time polling at 2-second/3-second/10-second intervals',
        'Voice announcements via edge-tts',
        'Offline/online detection with animated banners',
    ]
    for item in mobile_items:
        p = doc.add_paragraph(item, style='List Bullet')
        for run in p.runs:
            run.font.name = 'Times New Roman'

    doc.add_heading('6.8 Feedback System with Kiosk Tracking (Claim 25)', level=2)
    doc.add_paragraph(
        'The feedback system implements kiosk-type-aware redirect tracking:'
    )
    p = doc.add_paragraph()
    run = p.add_run('Flow:')
    run.bold = True
    run.font.name = 'Times New Roman'
    add_code_block(doc, (
        '1. Kiosk generates receipt with feedback URL: /r/{token}?from={kiosk-type}\n'
        '2. QR code encodes the same URL\n'
        '3. User scans QR -> /r/{token}?from={kiosk-type}\n'
        '4. Server redirects to /feedback.html/{secret_token}/{token}?from={kiosk-type}\n'
        '5. Feedback page reads ?from= parameter\n'
        '6. After submission: redirects to originating kiosk type\n'
        '   - from=kiosk-B -> /student-kiosk-B.html\n'
        '   - No parameter -> /student-token.html (default)'
    ))

    doc.add_heading('6.9 Security Architecture (Claims 27-30)', level=2)
    p = doc.add_paragraph()
    run = p.add_run('Token-Based Route Protection:')
    run.bold = True
    run.font.name = 'Times New Roman'
    security_items = [
        'Officer tokens: Persistent (written to .officer_token file)',
        'Admin tokens: Ephemeral (generated per server start)',
        'Feedback tokens: Ephemeral (generated per server start)',
        'Decoy routes redirect unauthorized access attempts',
    ]
    for item in security_items:
        p = doc.add_paragraph(item, style='List Bullet')
        for run in p.runs:
            run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    run = p.add_run('Database Auto-Migration:')
    run.bold = True
    run.font.name = 'Times New Roman'
    doc.add_paragraph(
        'Server startup performs idempotent schema management: creates missing tables, adds missing '
        'columns via ALTER TABLE, creates missing indexes, drops and recreates unique constraints, '
        'backfills new columns from existing data, and seeds default data for empty tables.'
    )

    doc.add_page_break()
    doc.add_heading('7. CLAIMS', level=1)

    categories = [
        ('Category A: AI-Powered Queue Intelligence', [
            (1, True, 'A computer-implemented method for AI-integrated queue management in an educational institution, comprising: receiving token generation requests from a student kiosk terminal; generating queue tokens with per-day first-free numbering; storing token records in a database; transmitting queue data to a real-time public display; receiving officer service actions from an officer dashboard; processing feedback submissions from a feedback interface; and analyzing queue performance data using a large language model (LLM) to generate attendance reports, feedback-officer correlations, and complaint response recommendations.'),
            (2, False, 'The method of Claim 1, wherein the AI analysis includes per-officer anomaly detection with monthly grade computation based on actual working days in the month, where the monthly target is dynamically calculated as 540 minutes multiplied by the number of weekdays in the current month.'),
            (3, False, 'The method of Claim 1, wherein complaint replies are polished by the AI with a selectable tone parameter selected from the group consisting of professional, empathetic, formal, and friendly, constrained to 200 words maximum, preserving factual accuracy, and excluding markdown formatting.'),
            (4, False, 'The method of Claim 1, wherein the AI feedback-officer correlation analysis receives token-based feedback data, per-officer statistics, and general complaint records, and generates pattern analysis identifying improvement recommendations with specific officer identifiers.'),
            (5, False, 'The method of Claim 1, wherein the AI attendance analysis receives structured attendance data including login/logout times, tokens served, availability percentages, and monthly grades, and generates a natural-language report with per-officer observations and actionable recommendations.'),
        ]),
        ('Category B: Voice and Real-Time Display', [
            (6, True, 'A system for real-time public queue display comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; a voice announcement subsystem generating contextual audio messages for called, recalled, and serving tokens; an adaptive token preview algorithm dynamically adjusting the number of preview tokens displayed based on the count of active offices; and a screen health monitor detecting data staleness, API silence, and JavaScript errors to trigger safe reload operations.'),
            (7, False, 'The system of Claim 6, wherein the voice announcement subsystem spells token characters individually (e.g., "A R 0 1" for "AR01") and concatenates multiple token announcements into grammatically correct sentences using conjunction words for the final item in a batch.'),
            (8, False, 'The system of Claim 6, wherein the adaptive token preview algorithm assigns preview token counts as: three or more active offices display one next token per office; two active offices display two next tokens per office; and one active office displays three next tokens.'),
            (9, False, 'The system of Claim 6, wherein the screen health monitor executes at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations.'),
            (10, False, 'The system of Claim 6, wherein voice announcements are deduplicated using a composite key comprising token number, office name, and action type, with a configurable cooldown period preventing repeated announcements of the same token-office-action combination.'),
        ]),
        ('Category C: Token Lifecycle Management', [
            (11, True, 'A computer-implemented method for token lifecycle management in a queue system, comprising: generating tokens with per-day first-free numbering by querying existing tokens for the current date, extracting numeric suffixes, identifying the first unused number in the sequence, and assigning the token with office code prefix and zero-padded numeric suffix; enforcing a unique constraint on the combination of token number and token date; and supporting queue reset operations that atomically expire waiting tokens, delete expired tokens, and return the predicted next token number.'),
            (12, False, 'The method of Claim 11, wherein the queue reset operation performs three atomic operations: setting status to "expired" for all waiting and called tokens, deleting expired and skipped tokens from the current day, and calculating the next available token number by identifying the first gap in the used number sequence.'),
            (13, False, 'The method of Claim 11, wherein priority tokens generated for parent service requests (service code "PS") are sorted before standard tokens in the queue display and serving order, with priority status indicated visually on the receipt and public display.'),
            (14, False, 'The method of Claim 11, further comprising rate-before-next-token enforcement, wherein a student with an unrated completed token is blocked from generating a new token until the previous token\'s feedback is submitted, the blocked state displaying the unrated token number and a direct link to the feedback submission page.'),
            (15, False, 'The method of Claim 11, wherein an office availability gate prevents an administrator from marking an office as unavailable when students are currently waiting, returning a refusal message with the count of waiting students.'),
            (16, False, 'The method of Claim 11, wherein batch operations allow calling, serving, or completing up to ten tokens simultaneously, with the batch size configurable between one and ten, and each operation incrementing a tokens-served counter on the officer\'s active session record.'),
        ]),
        ('Category D: Attendance and Analytics', [
            (17, True, 'A system for attendance tracking in a queue management environment, comprising: recording officer login and logout events with timestamps; calculating daily attendance using a first-login/last-logout method where the effective start time is clamped to no earlier than 8:00 AM and the effective end time is clamped to no later than 5:00 PM; merging multiple sessions within a single day by taking the minimum login time and maximum logout time; and computing monthly attendance targets dynamically based on the actual number of working days in the month.'),
            (18, False, 'The system of Claim 17, wherein the monthly attendance target is computed by counting the number of days in the current month where the day of the week is Monday through Friday, and multiplying by 540 minutes (9 hours).'),
            (19, False, 'The system of Claim 17, further comprising computation of four distinct time metrics: turnaround time (request to completion), service time (service start to completion), queue wait time (request to service start), and call response time (call to service start).'),
            (20, False, 'The system of Claim 17, further comprising three-metric heatmap analytics providing hourly breakdowns of token creation count, average wait duration, and distinct officer presence per office per day, with peak hour and busiest office identification.'),
            (21, False, 'The system of Claim 17, further comprising a tokens-per-hour efficiency metric computed as the total daily served tokens multiplied by 60 and divided by the total daily logged-in minutes, providing a measure of officer productivity.'),
        ]),
        ('Category E: Multi-Platform Kiosk Architecture', [
            (22, True, 'A multi-platform kiosk system for queue management, comprising: an Electron desktop application configured in fullscreen kiosk mode with frameless window, always-on-top positioning, and display sleep prevention; a web-based interface with virtual keyboard detection and automatic layout adaptation; and a mobile application built with React Native/Expo providing real-time queue display; all platforms communicating with a centralized server through REST API endpoints.'),
            (23, False, 'The system of Claim 22, wherein the Electron desktop application implements crash recovery comprising: monitoring renderer process crashed and unresponsive events with 2-second delayed restart; implementing a 30-attempt load retry with 3-second intervals; running a watchdog timer every 30 seconds testing renderer responsiveness; and recreating the window automatically upon window close events when the application is not in a quitting state.'),
            (24, False, 'The system of Claim 22, wherein the Electron desktop application implements silent receipt printing by scanning available printers for name patterns matching "POSPrinter" or "80C", falling back to an environment variable for printer name, and printing with silent mode, background graphics enabled, no margins, and no header/footer.'),
            (25, False, 'The system of Claim 22, wherein the feedback interface tracks the originating kiosk type using a URL query parameter (e.g., ?from=kiosk-B), and after feedback submission, redirects the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present.'),
            (26, False, 'The system of Claim 22, wherein the kiosk auto-configuration comprises a PowerShell script that: checks Chrome installation across multiple file paths; sets the AutoplayAllowed registry key; creates a Chrome kiosk shortcut with --kiosk --autoplay-policy=no-user-gesture-required flags; adds the shortcut to the Windows Startup folder; and implements cursor auto-hiding after 3 seconds of inactivity.'),
        ]),
        ('Category F: Security and Infrastructure', [
            (27, True, 'A token-based route protection system for a web application, comprising: generating an officer token persisted to a file on disk for persistent authentication; generating admin and feedback tokens as ephemeral secrets per server start; embedding tokens in URL paths for protected routes (e.g., /admin/{token}, /officer/{token}, /feedback.html/{token}); implementing decoy routes that redirect unauthorized access attempts; and providing a token lookup endpoint for authenticated token retrieval.'),
            (28, False, 'The system of Claim 27, wherein decoy routes for /admin, /officer, /login, /workflow, and /feedback.html (without token) redirect to the application landing page, preventing direct access to protected pages without valid tokens.'),
            (29, False, 'The system of Claim 27, further comprising a self-healing database auto-migration system that on server startup: creates missing tables, adds missing columns via ALTER TABLE, creates missing indexes, drops and recreates unique constraints, backfills new columns from existing data, and seeds default data for empty tables, all operations being idempotent.'),
            (30, False, 'The system of Claim 27, further comprising geographic IP resolution for officer login tracking, wherein private IP addresses (127.x, 192.168.x, 10.x, 172.x) are identified as "Local Network" and public IP addresses are resolved to city, region, country, and GPS coordinates using an external geolocation service, with results stored in the officer session record.'),
        ]),
    ]

    for cat_title, claims in categories:
        doc.add_heading(cat_title, level=2)
        for num, independent, text in claims:
            add_claim(doc, num, text, independent)

    doc.add_page_break()
    doc.add_heading('8. ABSTRACT OF THE DISCLOSURE', level=1)
    doc.add_paragraph(
        'A smart queue management system comprising an AI-powered Flask backend, multi-platform kiosk '
        'terminals (Electron desktop, web, Android mobile), real-time public displays with voice '
        'announcements, and an administrative dashboard. The system implements per-day first-free token '
        'numbering with gap-aware restart, adaptive display with dynamic preview counts, voice '
        'announcements with token character spelling and batch concatenation, AI-powered attendance '
        'analysis and feedback correlation, rate-before-next-token enforcement, and kiosk-type-aware '
        'feedback redirect tracking. The system supports crash recovery, silent receipt printing, '
        'geographic IP tracking, and self-healing database migration.'
    )

    doc.add_heading('9. INVENTOR DECLARATION', level=1)
    doc.add_paragraph(
        'I, Ogwal Richard, hereby declare that I am the original inventor of the Smart Queue '
        'Management System (SMQSS) described in this document, developed under the supervision of '
        'Odongo Steven Eyobu (PhD) at Makerere University. All claims herein are based on original '
        'research and development conducted between January 2025 and August 2026.'
    )
    doc.add_paragraph('')
    for label in ['Inventor: Ogwal Richard', 'Student Number: 2300716574',
                   'Signature: ________________________', 'Date: ________________________',
                   '', 'Advisor: Odongo Steven Eyobu (PhD)',
                   'Signature: ________________________', 'Date: ________________________']:
        p = doc.add_paragraph(label)
        for run in p.runs:
            run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('\n\nDocument prepared for intellectual property protection under the Uganda Industrial Property Act, 2003 and the ARIPO Harare Protocol on Patents.')
    run.italic = True
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'

    doc.save('E:/cmd/test/IP_DOCUMENT.docx')
    print('Created IP_DOCUMENT.docx')

def generate_claims_doc():
    doc = Document()
    setup_styles(doc)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('CLAIMS ONLY - FOR LEGAL FILING')
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('SMART QUEUE MANAGEMENT SYSTEM (SMQSS)')
    run.bold = True
    run.font.size = Pt(14)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('INVENTOR: OGWAL RICHARD | STUDENT NO: 2300716574')
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('MAKERERE UNIVERSITY | SUPERVISOR: ODONGO STEVEN EYOBU (PhD)')
    run.font.size = Pt(12)
    run.font.name = 'Times New Roman'

    doc.add_paragraph('')

    categories = [
        ('CATEGORY A: AI-POWERED QUEUE INTELLIGENCE', [
            (1, True, 'A computer-implemented method for AI-integrated queue management in an educational institution, comprising: receiving token generation requests from a student kiosk terminal; generating queue tokens with per-day first-free numbering; storing token records in a database; transmitting queue data to a real-time public display; receiving officer service actions from an officer dashboard; processing feedback submissions from a feedback interface; and analyzing queue performance data using a large language model (LLM) to generate attendance reports, feedback-officer correlations, and complaint response recommendations.'),
            (2, False, 'The method of Claim 1, wherein the AI analysis includes per-officer anomaly detection with monthly grade computation based on actual working days in the month, where the monthly target is dynamically calculated as 540 minutes multiplied by the number of weekdays in the current month.'),
            (3, False, 'The method of Claim 1, wherein complaint replies are polished by the AI with a selectable tone parameter selected from the group consisting of professional, empathetic, formal, and friendly, constrained to 200 words maximum, preserving factual accuracy, and excluding markdown formatting.'),
            (4, False, 'The method of Claim 1, wherein the AI feedback-officer correlation analysis receives token-based feedback data, per-officer statistics, and general complaint records, and generates pattern analysis identifying improvement recommendations with specific officer identifiers.'),
            (5, False, 'The method of Claim 1, wherein the AI attendance analysis receives structured attendance data including login/logout times, tokens served, availability percentages, and monthly grades, and generates a natural-language report with per-officer observations and actionable recommendations.'),
        ]),
        ('CATEGORY B: VOICE AND REAL-TIME DISPLAY', [
            (6, True, 'A system for real-time public queue display comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; a voice announcement subsystem generating contextual audio messages for called, recalled, and serving tokens; an adaptive token preview algorithm dynamically adjusting the number of preview tokens displayed based on the count of active offices; and a screen health monitor detecting data staleness, API silence, and JavaScript errors to trigger safe reload operations.'),
            (7, False, 'The system of Claim 6, wherein the voice announcement subsystem spells token characters individually (e.g., "A R 0 1" for "AR01") and concatenates multiple token announcements into grammatically correct sentences using conjunction words for the final item in a batch.'),
            (8, False, 'The system of Claim 6, wherein the adaptive token preview algorithm assigns preview token counts as: three or more active offices display one next token per office; two active offices display two next tokens per office; and one active office displays three next tokens.'),
            (9, False, 'The system of Claim 6, wherein the screen health monitor executes at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations.'),
            (10, False, 'The system of Claim 6, wherein voice announcements are deduplicated using a composite key comprising token number, office name, and action type, with a configurable cooldown period preventing repeated announcements of the same token-office-action combination.'),
        ]),
        ('CATEGORY C: TOKEN LIFECYCLE MANAGEMENT', [
            (11, True, 'A computer-implemented method for token lifecycle management in a queue system, comprising: generating tokens with per-day first-free numbering by querying existing tokens for the current date, extracting numeric suffixes, identifying the first unused number in the sequence, and assigning the token with office code prefix and zero-padded numeric suffix; enforcing a unique constraint on the combination of token number and token date; and supporting queue reset operations that atomically expire waiting tokens, delete expired tokens, and return the predicted next token number.'),
            (12, False, 'The method of Claim 11, wherein the queue reset operation performs three atomic operations: setting status to "expired" for all waiting and called tokens, deleting expired and skipped tokens from the current day, and calculating the next available token number by identifying the first gap in the used number sequence.'),
            (13, False, 'The method of Claim 11, wherein priority tokens generated for parent service requests (service code "PS") are sorted before standard tokens in the queue display and serving order, with priority status indicated visually on the receipt and public display.'),
            (14, False, 'The method of Claim 11, further comprising rate-before-next-token enforcement, wherein a student with an unrated completed token is blocked from generating a new token until the previous token\'s feedback is submitted, the blocked state displaying the unrated token number and a direct link to the feedback submission page.'),
            (15, False, 'The method of Claim 11, wherein an office availability gate prevents an administrator from marking an office as unavailable when students are currently waiting, returning a refusal message with the count of waiting students.'),
            (16, False, 'The method of Claim 11, wherein batch operations allow calling, serving, or completing up to ten tokens simultaneously, with the batch size configurable between one and ten, and each operation incrementing a tokens-served counter on the officer\'s active session record.'),
        ]),
        ('CATEGORY D: ATTENDANCE AND ANALYTICS', [
            (17, True, 'A system for attendance tracking in a queue management environment, comprising: recording officer login and logout events with timestamps; calculating daily attendance using a first-login/last-logout method where the effective start time is clamped to no earlier than 8:00 AM and the effective end time is clamped to no later than 5:00 PM; merging multiple sessions within a single day by taking the minimum login time and maximum logout time; and computing monthly attendance targets dynamically based on the actual number of working days in the month.'),
            (18, False, 'The system of Claim 17, wherein the monthly attendance target is computed by counting the number of days in the current month where the day of the week is Monday through Friday, and multiplying by 540 minutes (9 hours).'),
            (19, False, 'The system of Claim 17, further comprising computation of four distinct time metrics: turnaround time (request to completion), service time (service start to completion), queue wait time (request to service start), and call response time (call to service start).'),
            (20, False, 'The system of Claim 17, further comprising three-metric heatmap analytics providing hourly breakdowns of token creation count, average wait duration, and distinct officer presence per office per day, with peak hour and busiest office identification.'),
            (21, False, 'The system of Claim 17, further comprising a tokens-per-hour efficiency metric computed as the total daily served tokens multiplied by 60 and divided by the total daily logged-in minutes, providing a measure of officer productivity.'),
        ]),
        ('CATEGORY E: MULTI-PLATFORM KIOSK ARCHITECTURE', [
            (22, True, 'A multi-platform kiosk system for queue management, comprising: an Electron desktop application configured in fullscreen kiosk mode with frameless window, always-on-top positioning, and display sleep prevention; a web-based interface with virtual keyboard detection and automatic layout adaptation; and a mobile application built with React Native/Expo providing real-time queue display; all platforms communicating with a centralized server through REST API endpoints.'),
            (23, False, 'The system of Claim 22, wherein the Electron desktop application implements crash recovery comprising: monitoring renderer process crashed and unresponsive events with 2-second delayed restart; implementing a 30-attempt load retry with 3-second intervals; running a watchdog timer every 30 seconds testing renderer responsiveness; and recreating the window automatically upon window close events when the application is not in a quitting state.'),
            (24, False, 'The system of Claim 22, wherein the Electron desktop application implements silent receipt printing by scanning available printers for name patterns matching "POSPrinter" or "80C", falling back to an environment variable for printer name, and printing with silent mode, background graphics enabled, no margins, and no header/footer.'),
            (25, False, 'The system of Claim 22, wherein the feedback interface tracks the originating kiosk type using a URL query parameter (e.g., ?from=kiosk-B), and after feedback submission, redirects the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present.'),
            (26, False, 'The system of Claim 22, wherein the kiosk auto-configuration comprises a PowerShell script that: checks Chrome installation across multiple file paths; sets the AutoplayAllowed registry key; creates a Chrome kiosk shortcut with --kiosk --autoplay-policy=no-user-gesture-required flags; adds the shortcut to the Windows Startup folder; and implements cursor auto-hiding after 3 seconds of inactivity.'),
        ]),
        ('CATEGORY F: SECURITY AND INFRASTRUCTURE', [
            (27, True, 'A token-based route protection system for a web application, comprising: generating an officer token persisted to a file on disk for persistent authentication; generating admin and feedback tokens as ephemeral secrets per server start; embedding tokens in URL paths for protected routes (e.g., /admin/{token}, /officer/{token}, /feedback.html/{token}); implementing decoy routes that redirect unauthorized access attempts; and providing a token lookup endpoint for authenticated token retrieval.'),
            (28, False, 'The system of Claim 27, wherein decoy routes for /admin, /officer, /login, /workflow, and /feedback.html (without token) redirect to the application landing page, preventing direct access to protected pages without valid tokens.'),
            (29, False, 'The system of Claim 27, further comprising a self-healing database auto-migration system that on server startup: creates missing tables, adds missing columns via ALTER TABLE, creates missing indexes, drops and recreates unique constraints, backfills new columns from existing data, and seeds default data for empty tables, all operations being idempotent.'),
            (30, False, 'The system of Claim 27, further comprising geographic IP resolution for officer login tracking, wherein private IP addresses (127.x, 192.168.x, 10.x, 172.x) are identified as "Local Network" and public IP addresses are resolved to city, region, country, and GPS coordinates using an external geolocation service, with results stored in the officer session record.'),
        ]),
    ]

    for cat_title, claims in categories:
        doc.add_heading(cat_title, level=1)
        for num, independent, text in claims:
            add_claim(doc, num, text, independent)

    doc.add_page_break()
    doc.add_heading('INDEPENDENT CLAIMS SUMMARY', level=1)
    add_table(doc,
        ['Category', 'Claim', 'Type'],
        [
            ['A', 'Claim 1', 'AI-Powered Queue Intelligence'],
            ['B', 'Claim 6', 'Voice and Real-Time Display'],
            ['C', 'Claim 11', 'Token Lifecycle Management'],
            ['D', 'Claim 17', 'Attendance and Analytics'],
            ['E', 'Claim 22', 'Multi-Platform Kiosk Architecture'],
            ['F', 'Claim 27', 'Security and Infrastructure'],
        ]
    )
    p = doc.add_paragraph()
    run = p.add_run('Total Claims: 30 (6 Independent + 24 Dependent)')
    run.bold = True
    run.font.name = 'Times New Roman'

    doc.add_heading('INVENTOR DECLARATION', level=1)
    doc.add_paragraph(
        'I, Ogwal Richard, hereby declare that I am the original inventor of the Smart Queue '
        'Management System (SMQSS) described in this document, developed under the supervision of '
        'Odongo Steven Eyobu (PhD) at Makerere University. All claims herein are based on original '
        'research and development conducted between January 2025 and August 2026.'
    )
    doc.add_paragraph('')
    for label in ['Inventor: Ogwal Richard', 'Student Number: 2300716574',
                   'Signature: ________________________', 'Date: ________________________',
                   '', 'Advisor: Odongo Steven Eyobu (PhD)',
                   'Signature: ________________________', 'Date: ________________________']:
        p = doc.add_paragraph(label)
        for run in p.runs:
            run.font.name = 'Times New Roman'

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('\n\nClaims prepared for intellectual property protection under the Uganda Industrial Property Act, 2003 and the ARIPO Harare Protocol on Patents.')
    run.italic = True
    run.font.size = Pt(10)
    run.font.name = 'Times New Roman'

    doc.save('E:/cmd/test/IP_CLAIMS_ONLY.docx')
    print('Created IP_CLAIMS_ONLY.docx')

if __name__ == '__main__':
    generate_full_doc()
    generate_claims_doc()
    print('Done!')
