# INTELLECTUAL PROPERTY DOCUMENT

## SMART QUEUE MANAGEMENT SYSTEM (SMQSS)

### A System and Method for AI-Integrated Queue Management with Real-Time Voice Announcements, Adaptive Display, and Multi-Platform Kiosk Architecture

---

**Application Type:** Software Patent / Utility Model  
**Filing Jurisdiction:** Uganda Registration Services Bureau (URSB) / African Regional Intellectual Property Organization (ARIPO)  
**Inventor:** Ogwal Richard (Student Number: 2300716574)  
**Advisor:** Odongo Steven Eyobu (PhD)  
**Institution:** Makerere University, College of Computing and Information Sciences  
**Version:** 2.1.0  
**Date:** August 2026  
**Prior Art Search:** Conducted August 2026  

---

## 1. ABSTRACT

A smart queue management system (SMQSS) comprising an AI-powered backend server, multi-platform kiosk terminals, real-time public display screens, and an officer dashboard, all communicating through a centralized hub-and-spoke architecture. The system introduces novel methods for per-day first-free token numbering with gap-aware restart, adaptive public display with dynamic token preview counts based on active office density, voice announcements using token character spelling with batch concatenation, AI-integrated attendance analysis with anomaly detection, and a rate-before-next-token enforcement mechanism. The system supports Electron desktop kiosks with crash recovery and silent receipt printing, web-based interfaces with virtual keyboard adaptation, and Android mobile applications, all synchronized to server time in the Africa/Nairobi timezone.

**Keywords:** Queue management, artificial intelligence, token system, voice announcements, real-time display, kiosk, attendance tracking, Flutter, Electron, Python, Flask

---

## 2. FIELD OF INVENTION

The present invention relates to the field of queue management systems, specifically to computer-implemented methods and systems for managing service queues in educational institutions, government offices, and public service centers. More particularly, the invention relates to AI-integrated queue management with real-time voice announcements, adaptive display algorithms, multi-platform kiosk architecture, and comprehensive attendance analytics.

---

## 3. BACKGROUND OF THE INVENTION

### 3.1 Prior Art

Traditional queue management systems suffer from several limitations:

1. **Static Token Numbering:** Existing systems use sequential numbering that does not account for queue resets, leading to confusion when tokens are expired or skipped.

2. **Passive Display Systems:** Current public displays show fixed information without adapting to real-time conditions such as the number of active offices or current queue density.

3. **No AI Integration:** Prior art systems lack artificial intelligence capabilities for analyzing attendance patterns, correlating feedback with officer performance, and generating intelligent complaint responses.

4. **Limited Voice Support:** Existing voice announcement systems use simple text-to-speech without optimization for token number pronunciation, batch announcement concatenation, or deduplication.

5. **Single-Platform Limitation:** Most queue systems are designed for a single platform (web or desktop) without supporting multi-platform deployment across Electron desktop apps, web browsers, and mobile devices.

6. **No Rate Enforcement:** Existing systems do not enforce feedback submission before allowing new token generation, leading to low feedback response rates.

### 3.2 Deficiencies in Prior Art

| Deficiency | Prior Art Approach | Present Invention |
|-----------|-------------------|-------------------|
| Token numbering | Sequential, no reset handling | Per-day first-free with gap-aware restart |
| Display adaptation | Fixed layout | Dynamic preview count based on active office density |
| AI integration | None | LLM-powered attendance analysis, feedback correlation, complaint polishing |
| Voice announcements | Basic TTS | Character spelling, batch concatenation, deduplication, audio queue |
| Platform support | Single platform | Electron + Web + Android mobile |
| Feedback enforcement | Optional | Rate-before-next-token blocking with direct feedback linking |
| Attendance tracking | Simple login/logout | First-login/last-logout clamped to office hours with multi-session merging |
| Crash recovery | Basic restart | 30-attempt retry, watchdog timer, window recreation, cache clearing |

---

## 4. SUMMARY OF THE INVENTION

The present invention provides a smart queue management system comprising:

**A.** A centralized Flask-based backend server with MySQL database, implementing per-day first-free token numbering, attendance calculation with office-hours clamping, and AI-powered analytics through GROQ LLM integration.

**B.** Multi-platform kiosk terminals including Electron desktop applications with crash recovery, silent receipt printing, and kiosk mode; web-based interfaces with virtual keyboard adaptation; and Android mobile applications built with React Native/Expo.

**C.** Real-time public display screens with adaptive token preview algorithms, contextual voice announcements using edge-tts with token character spelling, batch concatenation, and deduplication.

**D.** An officer dashboard with PIN authentication, batch token operations (call/serve/complete up to 10 tokens), status logging, and peer rating capabilities.

**E.** A feedback system with QR-coded receipts, opaque URL redirects, rate-before-next-token enforcement, and kiosk-type-aware redirect tracking.

**F.** An administrative dashboard with AI-powered attendance analysis, feedback-officer correlation, complaint management with AI-polished responses, heatmap analytics, and multi-week trend analysis.

---

## 5. BRIEF DESCRIPTION OF DRAWINGS

| Figure | Description |
|--------|-------------|
| FIG. 1 | System Architecture Diagram — Hub-and-spoke architecture with Flask server as central hub |
| FIG. 2 | Token Lifecycle Flowchart — From generation through service completion and feedback |
| FIG. 3 | Adaptive Display Algorithm — Dynamic preview count calculation based on active office count |
| FIG. 4 | Attendance Calculation Flowchart — First-login/last-logout with office-hours clamping |
| FIG. 5 | AI Integration Diagram — GROQ LLM interfaces for attendance, feedback, and complaints |
| FIG. 6 | Multi-Platform Architecture — Electron, Web, and Mobile component relationships |
| FIG. 7 | Voice Announcement Pipeline — TTS generation, deduplication, and audio queue management |
| FIG. 8 | Kiosk Crash Recovery State Machine — Retry, watchdog, and window recreation logic |
| FIG. 9 | Feedback Flow with Kiosk Tracking — QR code → redirect → rating → kiosk-type-aware return |
| FIG. 10 | Database Schema — Entity relationship diagram for token, officer, session, and feedback tables |

---

## 6. DETAILED DESCRIPTION

### 6.1 System Architecture

The SMQSS system employs a hub-and-spoke architecture where a centralized Flask server (`app.py`, approximately 5,000 lines) manages all state and communication. Six interconnected components communicate exclusively through REST API endpoints:

1. **Student Kiosk** (`student-token.html`, `student-kiosk-B.html`): 3-step guided wizard with AI assistant typewriter interface for token generation.

2. **Public Display** (`public-display.html`, approximately 1,650 lines): TV-optimized real-time display with voice announcements, news ticker, and recall banners.

3. **Officer Dashboard** (`officer-dashboard.html`): PIN-authenticated interface for queue operations including batch call/serve/complete.

4. **Admin Dashboard** (`admin-dashboard.html`): CRUD operations, analytics, attendance monitoring, and AI-powered analysis.

5. **Feedback System** (`feedback.html`): Token-lookup rating interface with typewriter AI guidance and kiosk-type-aware redirects.

6. **Mobile Application** (`smqss-mobile/`): React Native/Expo application mirroring the public display for Android devices.

### 6.2 Per-Day First-Free Token Numbering (Claim 11)

The system implements a novel token numbering algorithm that ensures gap-free numbering within each day while supporting queue resets:

**Algorithm:**
```
1. Query all token numbers for the given office on the current date
2. Extract numeric suffix from each token number (e.g., "AR" + "01" → 1)
3. Build set of used numbers
4. Starting from 1, find first unused number
5. Assign token: office_code + padded_number (e.g., "AR01")
6. Unique constraint: (token_number, token_date) — per-day uniqueness only
```

This approach allows queue resets to recycle numbers from the beginning rather than continuing from the last assigned number, preventing confusion when tokens are expired or skipped.

### 6.3 Adaptive Public Display Algorithm (Claim 8)

The public display implements a dynamic "Up Next" preview algorithm that adjusts the number of preview tokens based on the density of active offices:

```
Active offices ≥ 3: Show 1 next token per office
Active offices = 2: Show 2 next tokens per office
Active offices = 1: Show 3 next tokens per office
```

This algorithm ensures that the display remains balanced and informative regardless of how many offices are currently serving students, preventing information overload when many offices are active and maximizing useful information when few offices are active.

### 6.4 Voice Announcement Pipeline (Claims 6-10)

The voice announcement system implements a multi-stage pipeline:

**Stage 1: Token Spelling**
Token numbers are character-spoken for clarity: "AR01" → "A R 0 1" using `token.split('').join(' ')`.

**Stage 2: Contextual Message Generation**
Three announcement types with distinct templates:
- Called: "Token [N], please go to [Office]"
- Recall: "Token [N], please return to [Office]"  
- Serving: "Token [N], you are now being served at [Office]"

**Stage 3: Batch Concatenation**
Multiple tokens are concatenated into a single grammatically correct sentence: "Tokens A R 0 1, A R 0 2, and A R 0 3, please go to Admissions Office."

**Stage 4: Deduplication**
Recent announcements tracked with composite key `token|officeName|actionType` and 1-second cooldown prevent duplicate announcements.

**Stage 5: Audio Queue**
Sequential audio playback queue using invisible `<video>` elements prevents announcement overlap, ensuring each announcement completes before the next begins.

### 6.5 Attendance Calculation (Claims 17-21)

The attendance system implements a sophisticated calculation that handles multiple sessions per day:

**Algorithm:**
```
For each day:
  1. Collect all login/logout times across all sessions
  2. first_login = min(all logins)
  3. last_logout = max(all logouts)
  4. effective_start = max(first_login, 8:00 AM)
  5. effective_end = min(last_logout, 5:00 PM)
  6. duration = max(0, (effective_end - effective_start).total_seconds() / 60)
```

**Monthly Target Calculation:**
```
days_in_month = calendar.monthrange(year, month)[1]
working_days = count of days where weekday < 5 (Mon-Fri)
monthly_target = 540 minutes × working_days
```

**Four Distinct Time Metrics:**
1. `avg_turnaround_minutes`: requested_at → completed_at
2. `avg_service_minutes`: serving_started_at → completed_at
3. `avg_queue_wait_before_service_minutes`: requested_at → serving_started_at
4. `avg_response_after_call_minutes`: called_at → serving_started_at

### 6.6 AI Integration (Claims 1-5)

The system integrates GROQ LLM (model: `openai/gpt-oss-120b`) for three distinct AI-powered functions:

**A. AI Complaint Reply Generation**
Admin drafts are polished by AI with selectable tone (professional, empathetic, formal, friendly), constrained to 200 words, no markdown, fact-preserving.

**B. AI Weekly Attendance Analysis**
Structured officer attendance data (login/logout times, tokens served, availability percentages, monthly grades) is formatted and sent to AI for natural-language report with per-officer observations, anomaly detection, and actionable recommendations.

**C. AI Feedback-Officer Correlation Analysis**
Token-based feedback, per-officer statistics, and general complaints are correlated by AI for pattern analysis and improvement recommendations.

### 6.7 Multi-Platform Kiosk Architecture (Claims 22-26)

**Electron Desktop Kiosk:**
- Fullscreen frameless always-on-top window
- `powerSaveBlocker.start('prevent-display-sleep')` for continuous display
- Crash recovery with 30-attempt retry at 3-second intervals
- Watchdog timer testing renderer responsiveness every 30 seconds
- HTTP cache clearing on startup for fresh content
- Silent POS receipt printing with automatic printer detection

**Web Interface:**
- Virtual keyboard detection via `window.visualViewport.resize`
- Automatic layout restructuring when keyboard opens
- `scrollInputIntoView()` for focused input visibility

**Android Mobile:**
- React Native/Expo application with same layout as TV display
- Real-time polling at 2-second/3-second/10-second intervals
- Voice announcements via edge-tts
- Offline/online detection with animated banners

### 6.8 Feedback System with Kiosk Tracking (Claim 25)

The feedback system implements kiosk-type-aware redirect tracking:

**Flow:**
```
1. Kiosk generates receipt with feedback URL: /r/{token}?from={kiosk-type}
2. QR code encodes the same URL
3. User scans QR → /r/{token}?from={kiosk-type}
4. Server redirects to /feedback.html/{secret_token}/{token}?from={kiosk-type}
5. Feedback page reads ?from= parameter
6. After submission: redirects to originating kiosk type
   - from=kiosk-B → /student-kiosk-B.html
   - No parameter → /student-token.html (default)
```

### 6.9 Security Architecture (Claims 27-30)

**Token-Based Route Protection:**
- Officer tokens: Persistent (written to `.officer_token` file)
- Admin tokens: Ephemeral (generated per server start)
- Feedback tokens: Ephemeral (generated per server start)
- Decoy routes redirect unauthorized access attempts

**Database Auto-Migration:**
Server startup performs idempotent schema management:
- Creates missing tables
- Adds missing columns via `ALTER TABLE`
- Creates missing indexes
- Drops and recreates unique constraints
- Backfills new columns from existing data
- Seeds default data for empty tables

---

## 7. CLAIMS

### Claim 1 (Independent) — AI-Integrated Queue Management System

A computer-implemented method for AI-integrated queue management in an educational institution, comprising: receiving token generation requests from a student kiosk terminal; generating queue tokens with per-day first-free numbering; storing token records in a database; transmitting queue data to a real-time public display; receiving officer service actions from an officer dashboard; processing feedback submissions from a feedback interface; and analyzing queue performance data using a large language model (LLM) to generate attendance reports, feedback-officer correlations, and complaint response recommendations, wherein the AI analysis includes per-officer anomaly detection with monthly grade computation based on actual working days in the month, where the monthly target is dynamically calculated as 540 minutes multiplied by the number of weekdays in the current month; wherein complaint replies are polished by the AI with a selectable tone parameter selected from the group consisting of professional, empathetic, formal, and friendly, constrained to 200 words maximum, preserving factual accuracy, and excluding markdown formatting; wherein the AI feedback-officer correlation analysis receives token-based feedback data, per-officer statistics, and general complaint records, and generates pattern analysis identifying improvement recommendations with specific officer identifiers; and wherein the AI attendance analysis receives structured attendance data including login/logout times, tokens served, availability percentages, and monthly grades, and generates a natural-language report with per-officer observations and actionable recommendations.

### Claim 2 (Independent) — Real-Time Public Display with Adaptive Voice Announcements

A system for real-time public queue display comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; a voice announcement subsystem generating contextual audio messages for called, recalled, and serving tokens; an adaptive token preview algorithm dynamically adjusting the number of preview tokens displayed based on the count of active offices; and a screen health monitor detecting data staleness, API silence, and JavaScript errors to trigger safe reload operations, wherein the voice announcement subsystem spells token characters individually (e.g., "A R 0 1" for "AR01") and concatenates multiple token announcements into grammatically correct sentences using conjunction words for the final item in a batch; wherein the adaptive token preview algorithm assigns preview token counts as: three or more active offices display one next token per office; two active offices display two next tokens per office; and one active office displays three next tokens; wherein the screen health monitor executes at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations; and wherein voice announcements are deduplicated using a composite key comprising token number, office name, and action type, with a configurable cooldown period preventing repeated announcements of the same token-office-action combination.

### Claim 3 (Independent) — Per-Day First-Free Token Lifecycle Management

A computer-implemented method for token lifecycle management in a queue system, comprising: generating tokens with per-day first-free numbering by querying existing tokens for the current date, extracting numeric suffixes, identifying the first unused number in the sequence, and assigning the token with office code prefix and zero-padded numeric suffix; enforcing a unique constraint on the combination of token number and token date; and supporting queue reset operations that atomically expire waiting tokens, delete expired tokens, and return the predicted next token number, wherein the queue reset operation performs three atomic operations: setting status to 'expired' for all waiting and called tokens, deleting expired and skipped tokens from the current day, and calculating the next available token number by identifying the first gap in the used number sequence; wherein priority tokens generated for parent service requests (service code 'PS') are sorted before standard tokens in the queue display and serving order, with priority status indicated visually on the receipt and public display; further comprising rate-before-next-token enforcement, wherein a student with an unrated completed token is blocked from generating a new token until the previous token's feedback is submitted, the blocked state displaying the unrated token number and a direct link to the feedback submission page; wherein an office availability gate prevents an administrator from marking an office as unavailable when students are currently waiting, returning a refusal message with the count of waiting students; and wherein batch operations allow calling, serving, or completing up to ten tokens simultaneously, with the batch size configurable between one and ten, and each operation incrementing a tokens-served counter on the officer's active session record.

### Claim 4 (Independent) — Attendance Tracking with Office-Hours Clamping and Analytics

A system for attendance tracking in a queue management environment, comprising: recording officer login and logout events with timestamps; calculating daily attendance using a first-login/last-logout method where the effective start time is clamped to no earlier than 8:00 AM and the effective end time is clamped to no later than 5:00 PM; merging multiple sessions within a single day by taking the minimum login time and maximum logout time; and computing monthly attendance targets dynamically based on the actual number of working days in the month, wherein the monthly attendance target is computed by counting the number of days in the current month where the day of the week is Monday through Friday, and multiplying by 540 minutes (9 hours); further comprising computation of four distinct time metrics: turnaround time (request to completion), service time (service start to completion), queue wait time (request to service start), and call response time (call to service start); further comprising three-metric heatmap analytics providing hourly breakdowns of token creation count, average wait duration, and distinct officer presence per office per day, with peak hour and busiest office identification; and further comprising a tokens-per-hour efficiency metric computed as the total daily served tokens multiplied by 60 and divided by the total daily logged-in minutes, providing a measure of officer productivity.

### Claim 5 (Independent) — Multi-Platform Kiosk Architecture with Crash Recovery

A multi-platform kiosk system for queue management, comprising: an Electron desktop application configured in fullscreen kiosk mode with frameless window, always-on-top positioning, and display sleep prevention; a web-based interface with virtual keyboard detection and automatic layout adaptation; and a mobile application built with React Native/Expo providing real-time queue display; all platforms communicating with a centralized server through REST API endpoints, wherein the Electron desktop application implements crash recovery comprising: monitoring renderer process crashed and unresponsive events with 2-second delayed restart; implementing a 30-attempt load retry with 3-second intervals; running a watchdog timer every 30 seconds testing renderer responsiveness; and recreating the window automatically upon window close events when the application is not in a quitting state; wherein the Electron desktop application implements silent receipt printing by scanning available printers for name patterns matching "POSPrinter" or "80C", falling back to an environment variable for printer name, and printing with silent mode, background graphics enabled, no margins, and no header/footer; wherein the feedback interface tracks the originating kiosk type using a URL query parameter (e.g., ?from=kiosk-B), and after feedback submission, redirects the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present; and wherein the kiosk auto-configuration comprises a PowerShell script that: checks Chrome installation across multiple file paths; sets the AutoplayAllowed registry key; creates a Chrome kiosk shortcut with --kiosk --autoplay-policy=no-user-gesture-required flags; adds the shortcut to the Windows Startup folder; and implements cursor auto-hiding after 3 seconds of inactivity.

### Claim 6 (Independent) — Token-Based Route Protection with Self-Healing Database

A token-based route protection system for a web application, comprising: generating an officer token persisted to a file on disk for persistent authentication; generating admin and feedback tokens as ephemeral secrets per server start; embedding tokens in URL paths for protected routes (e.g., /admin/{token}, /officer/{token}, /feedback.html/{token}); implementing decoy routes that redirect unauthorized access attempts; and providing a token lookup endpoint for authenticated token retrieval, wherein decoy routes for /admin, /officer, /login, /workflow, and /feedback.html (without token) redirect to the application landing page, preventing direct access to protected pages without valid tokens; further comprising a self-healing database auto-migration system that on server startup: creates missing tables, adds missing columns via ALTER TABLE, creates missing indexes, drops and recreates unique constraints, backfills new columns from existing data, and seeds default data for empty tables, all operations being idempotent; and further comprising geographic IP resolution for officer login tracking, wherein private IP addresses (127.x, 192.168.x, 10.x, 172.x) are identified as "Local Network" and public IP addresses are resolved to city, region, country, and GPS coordinates using an external geolocation service, with results stored in the officer session record.

### Claim 7 (Independent) — Kiosk-Type-Aware Feedback Redirect System

A feedback redirect system for a multi-kiosk queue management environment, comprising: generating a receipt with a feedback URL encoded with a kiosk-type query parameter (e.g., /r/{token}?from=kiosk-B); encoding the same URL as a QR code on the receipt; upon QR code scan or URL access, redirecting to a feedback page that reads the kiosk-type parameter; processing feedback submission on the feedback page; and after submission, redirecting the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present, wherein the kiosk-type parameter propagates through all redirect hops to ensure the user returns to the correct kiosk interface after feedback completion.

### Claim 8 (Independent) — Voice Announcement Batch Concatenation and Deduplication

A voice announcement subsystem for a queue management display, comprising: receiving a batch of token numbers to announce; spelling each token character individually (e.g., "A R 0 1" for "AR01"); concatenating multiple token announcements into a single grammatically correct sentence using conjunction words for the final item in a batch (e.g., "Tokens A R 0 1, A R 0 2, and A R 0 3, please go to Admissions Office"); generating contextual announcement types for called, recalled, and serving tokens with distinct templates; deduplicating announcements using a composite key comprising token number, office name, and action type; applying a configurable cooldown period preventing repeated announcements of the same token-office-action combination; and queuing announcements sequentially in an audio playback queue to prevent announcement overlap, ensuring each announcement completes before the next begins.

### Claim 9 (Independent) — Rate-Before-Next-Token Enforcement with QR-Coded Receipt

A rate-before-next-token enforcement system for a queue management environment, comprising: upon service completion, generating a receipt containing a QR code encoding a feedback URL; displaying a mandatory notice on the receipt indicating that rating is required before requesting a new token; upon subsequent token generation request, checking whether the student has any unrated completed tokens; if an unrated token exists, blocking the new token generation and displaying the unrated token number with a direct link to the feedback submission page; and upon feedback submission for the unrated token, unblocking token generation and allowing the student to proceed, wherein the feedback URL encodes the originating kiosk type to ensure redirect to the correct kiosk after submission.

### Claim 10 (Independent) — Adaptive Display with Dynamic Preview and Screen Health Monitoring

A public display system for queue management, comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; an adaptive token preview algorithm that dynamically adjusts the number of preview tokens displayed based on the count of active offices, wherein three or more active offices display one next token per office, two active offices display two next tokens per office, and one active office displays three next tokens; a screen health monitor executing at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations; and a voice announcement subsystem that generates contextual audio messages, spells token characters individually, concatenates multiple token announcements into grammatically correct sentences, deduplicates announcements using a composite key, and queues announcements sequentially to prevent overlap.

---

## 8. ABSTRACT OF THE DISCLOSURE

A smart queue management system comprising an AI-powered Flask backend, multi-platform kiosk terminals (Electron desktop, web, Android mobile), real-time public displays with voice announcements, and an administrative dashboard. The system implements per-day first-free token numbering with gap-aware restart, adaptive display with dynamic preview counts, voice announcements with token character spelling and batch concatenation, AI-powered attendance analysis and feedback correlation, rate-before-next-token enforcement, and kiosk-type-aware feedback redirect tracking. The system supports crash recovery, silent receipt printing, geographic IP tracking, and self-healing database migration.

---

## 9. INVENTOR DECLARATION

I, Ogwal Richard, hereby declare that I am the original inventor of the Smart Queue Management System (SMQSS) described in this document, developed under the supervision of Odongo Steven Eyobu (PhD) at Makerere University. All claims herein are based on original research and development conducted between January 2025 and August 2026.

**Inventor:** Ogwal Richard  
**Student Number:** 2300716574  
**Signature:** ________________________  
**Date:** ________________________  

**Advisor:** Odongo Steven Eyobu (PhD)  
**Signature:** ________________________  
**Date:** ________________________  

---

*Document prepared for intellectual property protection under the Uganda Industrial Property Act, 2003 and the ARIPO Harare Protocol on Patents.*
