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

**Claim 1:**  
A computer-implemented Smart Queue Management System (SMQSS) for managing service queues and service delivery, comprising a centralized server, one or more user terminals, one or more service-officer interfaces, one or more public queue-display terminals, and a feedback interface, wherein the centralized server is configured to receive a service request from a person seeking service; capture identifying information of the person; generate and associate a queue token with the service request; manage the queue token from issuance through service completion; determine and control service order according to queue and service-priority rules; communicate queue status and service-call information in real time; and maintain a service transaction linking the person, queue token, service office, service officer, and service outcome.

**Claim 2:**  
The system of claim 1, wherein the queue management mechanism is configured to determine availability of a service office and/or service officer before allocating a queue token, capture the name of the person requesting service, associate the person's name with the allocated queue token and requested service, and, when the token is called, generate and communicate a service notification identifying the person by name together with the corresponding queue token and service office, thereby linking the person's identity, service request, token, service capacity, and service call within the same queue transaction.

**Claim 3:**  
The system of claim 1, wherein the token management mechanism is configured to generate and assign queue tokens to persons requesting services, associate each token with the corresponding person and service transaction, maintain the token through defined service states comprising waiting, called, serving, completed, cancelled, expired, or skipped, apply configurable service-priority rules to determine service order, and perform controlled queue-reset operations for managing active queue transactions.

**Claim 4:**  
The system of claim 1, wherein the feedback mechanism is configured to associate the person's identity and queue token with a corresponding completed service transaction and enable the person to rate service delivery and submit suggestions, comments, complaints, or recommendations, thereby providing a transaction-linked service evaluation and digital suggestion-and-complaint mechanism, and wherein the system identifies an outstanding unrated completed transaction and controls issuance of a subsequent queue token until the required feedback has been submitted.

**Claim 5:**  
The system of claim 1, further comprising a receipt and feedback-routing mechanism configured to generate a printed or electronic receipt containing the queue token and a machine-readable code providing access to a corresponding feedback interface, wherein the receipt or code identifies an originating kiosk or service transaction and the originating identifier is preserved throughout the feedback process to return the person to the corresponding kiosk interface following feedback submission.

**Claim 6:**  
The system of claim 1, further comprising a real-time public display and voice-announcement mechanism configured to dynamically determine and adjust a number of forthcoming queue tokens displayed according to a number of active service offices, generate contextual voice announcements corresponding to queue events, identify a called person by name together with the person's queue token and service office, convert token identifiers into individually spoken characters, combine multiple queue announcements into a structured audio message, suppress repeated announcements of the same queue event, and sequentially process announcements to prevent overlapping audio.

**Claim 7:**  
The system of claim 1, further comprising an artificial-intelligence analytics mechanism configured to receive and correlate attendance, queue, service, feedback, and complaint data to generate service-provider-specific performance observations, attendance analysis, service-efficiency analysis, relationships between service delivery and user feedback, service-improvement recommendations, or assisted responses to complaints; and a multilingual localization mechanism configured to permit persons to interact with the system in a selected language from a plurality of national, official, local, institutional, and community languages, including Ugandan languages, wherein queue instructions, token information, service-status information, feedback functions, notifications, public-display information, voice announcements, and receipts are provided in the selected language while maintaining the underlying queue and service transaction.

**Claim 8:**  
The system of claim 1, further comprising a multi-platform architecture supporting desktop kiosk, web, and mobile interfaces communicating with the centralized server through application programming interfaces, wherein the architecture further provides automatic recovery of failed or unresponsive kiosk and public-display interfaces and automated database recovery and migration for maintaining operational data and system functions required for continued queue-management and service-delivery operation.

---

## 8. ABSTRACT OF THE DISCLOSURE

A computer-implemented Smart Queue Management System (SMQSS) for managing service queues and service delivery, comprising a centralized server, user terminals, service-officer interfaces, public queue-display terminals, and a feedback interface. The system captures identifying information of persons seeking service, generates and manages queue tokens through defined service states, determines service order according to queue and service-priority rules, and communicates queue status and service-call information in real time. The system links person identity, service request, token, service capacity, and service call within each queue transaction. Further mechanisms include transaction-linked feedback with rate-before-next-token enforcement, receipt and feedback-routing with kiosk-type preservation, real-time public display with adaptive voice announcements and token character spelling, AI-powered analytics for attendance and service performance, multilingual localization across national and community languages, multi-platform architecture with automatic crash recovery, and automated database migration for operational continuity.

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
