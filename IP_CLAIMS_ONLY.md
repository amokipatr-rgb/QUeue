# SMQSS — Claims Summary (for Legal Filing)

**10 Claims | 10 Independent Claims**

---

## Claim 1 — AI-Integrated Queue Management System

A computer-implemented method for AI-integrated queue management in an educational institution, comprising: receiving token generation requests from a student kiosk terminal; generating queue tokens with per-day first-free numbering; storing token records in a database; transmitting queue data to a real-time public display; receiving officer service actions from an officer dashboard; processing feedback submissions from a feedback interface; and analyzing queue performance data using a large language model (LLM) to generate attendance reports, feedback-officer correlations, and complaint response recommendations, wherein the AI analysis includes per-officer anomaly detection with monthly grade computation based on actual working days in the month, where the monthly target is dynamically calculated as 540 minutes multiplied by the number of weekdays in the current month; wherein complaint replies are polished by the AI with a selectable tone parameter selected from the group consisting of professional, empathetic, formal, and friendly, constrained to 200 words maximum, preserving factual accuracy, and excluding markdown formatting; wherein the AI feedback-officer correlation analysis receives token-based feedback data, per-officer statistics, and general complaint records, and generates pattern analysis identifying improvement recommendations with specific officer identifiers; and wherein the AI attendance analysis receives structured attendance data including login/logout times, tokens served, availability percentages, and monthly grades, and generates a natural-language report with per-officer observations and actionable recommendations.

---

## Claim 2 — Real-Time Public Display with Adaptive Voice Announcements

A system for real-time public queue display comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; a voice announcement subsystem generating contextual audio messages for called, recalled, and serving tokens; an adaptive token preview algorithm dynamically adjusting the number of preview tokens displayed based on the count of active offices; and a screen health monitor detecting data staleness, API silence, and JavaScript errors to trigger safe reload operations, wherein the voice announcement subsystem spells token characters individually (e.g., "A R 0 1" for "AR01") and concatenates multiple token announcements into grammatically correct sentences using conjunction words for the final item in a batch; wherein the adaptive token preview algorithm assigns preview token counts as: three or more active offices display one next token per office; two active offices display two next tokens per office; and one active office displays three next tokens; wherein the screen health monitor executes at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations; and wherein voice announcements are deduplicated using a composite key comprising token number, office name, and action type, with a configurable cooldown period preventing repeated announcements of the same token-office-action combination.

---

## Claim 3 — Per-Day First-Free Token Lifecycle Management

A computer-implemented method for token lifecycle management in a queue system, comprising: generating tokens with per-day first-free numbering by querying existing tokens for the current date, extracting numeric suffixes, identifying the first unused number in the sequence, and assigning the token with office code prefix and zero-padded numeric suffix; enforcing a unique constraint on the combination of token number and token date; and supporting queue reset operations that atomically expire waiting tokens, delete expired tokens, and return the predicted next token number, wherein the queue reset operation performs three atomic operations: setting status to 'expired' for all waiting and called tokens, deleting expired and skipped tokens from the current day, and calculating the next available token number by identifying the first gap in the used number sequence; wherein priority tokens generated for parent service requests (service code 'PS') are sorted before standard tokens in the queue display and serving order, with priority status indicated visually on the receipt and public display; further comprising rate-before-next-token enforcement, wherein a student with an unrated completed token is blocked from generating a new token until the previous token's feedback is submitted, the blocked state displaying the unrated token number and a direct link to the feedback submission page; wherein an office availability gate prevents an administrator from marking an office as unavailable when students are currently waiting, returning a refusal message with the count of waiting students; and wherein batch operations allow calling, serving, or completing up to ten tokens simultaneously, with the batch size configurable between one and ten, and each operation incrementing a tokens-served counter on the officer's active session record.

---

## Claim 4 — Attendance Tracking with Office-Hours Clamping and Analytics

A system for attendance tracking in a queue management environment, comprising: recording officer login and logout events with timestamps; calculating daily attendance using a first-login/last-logout method where the effective start time is clamped to no earlier than 8:00 AM and the effective end time is clamped to no later than 5:00 PM; merging multiple sessions within a single day by taking the minimum login time and maximum logout time; and computing monthly attendance targets dynamically based on the actual number of working days in the month, wherein the monthly attendance target is computed by counting the number of days in the current month where the day of the week is Monday through Friday, and multiplying by 540 minutes (9 hours); further comprising computation of four distinct time metrics: turnaround time (request to completion), service time (service start to completion), queue wait time (request to service start), and call response time (call to service start); further comprising three-metric heatmap analytics providing hourly breakdowns of token creation count, average wait duration, and distinct officer presence per office per day, with peak hour and busiest office identification; and further comprising a tokens-per-hour efficiency metric computed as the total daily served tokens multiplied by 60 and divided by the total daily logged-in minutes, providing a measure of officer productivity.

---

## Claim 5 — Multi-Platform Kiosk Architecture with Crash Recovery

A multi-platform kiosk system for queue management, comprising: an Electron desktop application configured in fullscreen kiosk mode with frameless window, always-on-top positioning, and display sleep prevention; a web-based interface with virtual keyboard detection and automatic layout adaptation; and a mobile application built with React Native/Expo providing real-time queue display; all platforms communicating with a centralized server through REST API endpoints, wherein the Electron desktop application implements crash recovery comprising: monitoring renderer process crashed and unresponsive events with 2-second delayed restart; implementing a 30-attempt load retry with 3-second intervals; running a watchdog timer every 30 seconds testing renderer responsiveness; and recreating the window automatically upon window close events when the application is not in a quitting state; wherein the Electron desktop application implements silent receipt printing by scanning available printers for name patterns matching "POSPrinter" or "80C", falling back to an environment variable for printer name, and printing with silent mode, background graphics enabled, no margins, and no header/footer; wherein the feedback interface tracks the originating kiosk type using a URL query parameter (e.g., ?from=kiosk-B), and after feedback submission, redirects the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present; and wherein the kiosk auto-configuration comprises a PowerShell script that: checks Chrome installation across multiple file paths; sets the AutoplayAllowed registry key; creates a Chrome kiosk shortcut with --kiosk --autoplay-policy=no-user-gesture-required flags; adds the shortcut to the Windows Startup folder; and implements cursor auto-hiding after 3 seconds of inactivity.

---

## Claim 6 — Token-Based Route Protection with Self-Healing Database

A token-based route protection system for a web application, comprising: generating an officer token persisted to a file on disk for persistent authentication; generating admin and feedback tokens as ephemeral secrets per server start; embedding tokens in URL paths for protected routes (e.g., /admin/{token}, /officer/{token}, /feedback.html/{token}); implementing decoy routes that redirect unauthorized access attempts; and providing a token lookup endpoint for authenticated token retrieval, wherein decoy routes for /admin, /officer, /login, /workflow, and /feedback.html (without token) redirect to the application landing page, preventing direct access to protected pages without valid tokens; further comprising a self-healing database auto-migration system that on server startup: creates missing tables, adds missing columns via ALTER TABLE, creates missing indexes, drops and recreates unique constraints, backfills new columns from existing data, and seeds default data for empty tables, all operations being idempotent; and further comprising geographic IP resolution for officer login tracking, wherein private IP addresses (127.x, 192.168.x, 10.x, 172.x) are identified as "Local Network" and public IP addresses are resolved to city, region, country, and GPS coordinates using an external geolocation service, with results stored in the officer session record.

---

## Claim 7 — Kiosk-Type-Aware Feedback Redirect System

A feedback redirect system for a multi-kiosk queue management environment, comprising: generating a receipt with a feedback URL encoded with a kiosk-type query parameter (e.g., /r/{token}?from=kiosk-B); encoding the same URL as a QR code on the receipt; upon QR code scan or URL access, redirecting to a feedback page that reads the kiosk-type parameter; processing feedback submission on the feedback page; and after submission, redirecting the user to the kiosk page corresponding to the originating kiosk type, defaulting to a standard kiosk page when no parameter is present, wherein the kiosk-type parameter propagates through all redirect hops to ensure the user returns to the correct kiosk interface after feedback completion.

---

## Claim 8 — Voice Announcement Batch Concatenation and Deduplication

A voice announcement subsystem for a queue management display, comprising: receiving a batch of token numbers to announce; spelling each token character individually (e.g., "A R 0 1" for "AR01"); concatenating multiple token announcements into a single grammatically correct sentence using conjunction words for the final item in a batch (e.g., "Tokens A R 0 1, A R 0 2, and A R 0 3, please go to Admissions Office"); generating contextual announcement types for called, recalled, and serving tokens with distinct templates; deduplicating announcements using a composite key comprising token number, office name, and action type; applying a configurable cooldown period preventing repeated announcements of the same token-office-action combination; and queuing announcements sequentially in an audio playback queue to prevent announcement overlap, ensuring each announcement completes before the next begins.

---

## Claim 9 — Rate-Before-Next-Token Enforcement with QR-Coded Receipt

A rate-before-next-token enforcement system for a queue management environment, comprising: upon service completion, generating a receipt containing a QR code encoding a feedback URL; displaying a mandatory notice on the receipt indicating that rating is required before requesting a new token; upon subsequent token generation request, checking whether the student has any unrated completed tokens; if an unrated token exists, blocking the new token generation and displaying the unrated token number with a direct link to the feedback submission page; and upon feedback submission for the unrated token, unblocking token generation and allowing the student to proceed, wherein the feedback URL encodes the originating kiosk type to ensure redirect to the correct kiosk after submission.

---

## Claim 10 — Adaptive Display with Dynamic Preview and Screen Health Monitoring

A public display system for queue management, comprising: a display terminal receiving queue data from a centralized server at regular polling intervals; an adaptive token preview algorithm that dynamically adjusts the number of preview tokens displayed based on the count of active offices, wherein three or more active offices display one next token per office, two active offices display two next tokens per office, and one active office displays three next tokens; a screen health monitor executing at 15-second intervals, tracking data freshness via last-fetch timestamps, monitoring API response silence, counting consecutive JavaScript errors with a threshold of five errors triggering reload, and implementing a 30-second cooldown between reload operations; and a voice announcement subsystem that generates contextual audio messages, spells token characters individually, concatenates multiple token announcements into grammatically correct sentences, deduplicates announcements using a composite key, and queues announcements sequentially to prevent overlap.

---

## Summary

| Claim | Category | Key Innovation |
|-------|----------|----------------|
| 1 | AI | LLM-powered queue intelligence with anomaly detection and tone selection |
| 2 | Display | Adaptive preview + character-spelling voice announcements + deduplication |
| 3 | Tokens | First-free numbering, gap-aware restart, priority tokens, rate enforcement |
| 4 | Attendance | Office-hours clamping, heatmap analytics, tokens-per-hour efficiency |
| 5 | Kiosk | Electron crash recovery, silent printing, auto-configuration |
| 6 | Security | Token-based routes, decoy redirects, self-healing DB, geo IP |
| 7 | Feedback | Kiosk-type-aware redirect chain with QR-encoded feedback URLs |
| 8 | Voice | Batch concatenation, sentence grammar, deduplication, sequential queue |
| 9 | Enforcement | QR receipt → rate → unblock token generation flow |
| 10 | Display | Dynamic preview algorithm + screen health monitoring |

---

## Inventor Declaration

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
