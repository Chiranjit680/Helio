# Functional Requirements (FR)

## Module 0: Intelligence Layer (Core AI Orchestrator)
The Intelligence Layer acts as the autonomous brain of Helio — similar to a *Jarvis-like orchestration engine* — with full visibility across all modules. It does not replace workflows; rather, it enhances them with proactive, context-aware intelligence.

**FR-AI-01 (Unified Context Engine):** The system shall maintain global context across Email, HR, Finance, Vendor, Meetings, Documents, and Inventory modules to enable cross-domain reasoning.

**FR-AI-02 (Proactive Suggestions):** The system shall proactively suggest actions such as drafting replies, initiating workflows, escalating anomalies, or recommending approvals.

**FR-AI-03 (Natural Language Command Center):** Users shall be able to issue natural language commands like “Generate an onboarding report for January hires” or “Show me all pending invoices above ₹50,000,” which the AI shall interpret and execute.

**FR-AI-04 (Workflow Auto-Healing):** When a workflow fails (e.g., API outage), the system shall intelligently retry, reroute, or suggest alternate paths.

**FR-AI-05 (Cross-Module Automation):** The AI shall create automations that span multiple modules (e.g., "If email mentions a vendor invoice, auto-check budget and vendor status").

**FR-AI-06 (Insight & Reasoning Engine):** The system shall generate insights such as anomalies, patterns, summaries, and strategic recommendations by analyzing multi-module data.

**FR-AI-07 (User Preference Learning):** Over time, the system shall learn user preferences (working hours, meeting habits, approval style) to personalize automation behavior.

---
................................................................................................................................................

## Module 1: Email Automation
Derived from handwritten note: "Email Read Watcher -> Analyzer -> Summarizing"

**FR-EMAIL-01 (Ingestion):** The system shall connect to email providers (Gmail/Outlook)  to detect new incoming messages in real-time.

**FR-EMAIL-02 (Sender Analysis):** The system shall analyze the sender's metadata (domain, frequency) to categorize the email (e.g., "Internal", "Client", "Spam") and also should capture the email of the sneder.

**FR-EMAIL-03 (Content Summarization):** The system shall use an LLM to generate a 3-bullet point summary of long email threads.

**FR-EMAIL-04 (Intent Recognition):** The system shall classify the email intent (e.g., "Invoice Attached", "Support Request", "Meeting Request") to trigger downstream workflows.
**FR-EMAIL-06 (Importance analysis):** The system shall automatically analyze the importance and classify it as, priority 1, 2 and 3.

**FR-EMAIL-06 (Attachment Processing):** The system shall automatically detach files (PDFs/Images) and send them to the Document Processor.

---

## Module 2: Employee Onboarding
Derived from handwritten note & MD file: "Doc collection -> Validation -> AI Extraction -> Asset Assignment"

**FR-HR-01 (Doc Collection):** The system shall provide a secure upload portal for new hires to submit required IDs (Passport, Tax Forms).

**FR-HR-02 (Auto-Validation):** The system shall check if uploaded files are correct or not and should request human validation

**FR-HR-03 (Data Extraction):** The system shall extract structured fields (Full Name, ID Number, Address) from documents to populate the Employee Database.

**FR-HR-04 (Asset Ticketing):** Upon approval, the system shall automatically generate IT tickets (e.g., via Jira/Slack) for laptop and account provisioning.

**FR-HR-05 (Account Creation):** The system shall trigger API calls to create a new employee account



---

## Module 3: Invoice Processing
Derived from handwritten note: "Capture -> Classification -> OCR -> Vendor Verification -> Budget Check"

**FR-FIN-01 (Multi-Channel Capture):** The system shall ingest invoices via Email attachments and direct manual uploads.

**FR-FIN-02 (Intelligent OCR):** The system shall extract Vendor Name, Invoice Date, Line Items, and Total Amount regardless of the invoice layout.

**FR-FIN-03 (Vendor Validation):** The system shall cross-reference the extracted Vendor Name/Bank Details against the "Approved Vendors" database to prevent fraud.

**FR-FIN-04 (Policy Logic):** The system shall apply a logic check:
- If Total < Budget & Trusted Vendor → Auto-Approve.
- If Total > Budget OR Unknown Vendor → Flag for Manager Review.

**FR-FIN-05 (Duplicate Check):** The system shall flag invoices with identical Invoice Numbers or Date+Amount combinations to prevent double payment.

---

## Module 4: Vendor Onboarding


**FR-VEND-01 (Self-Service Portal):** The system shall provide a link for vendors to upload Tax Certificates, Banking Details, and Company Registration via email.

**FR-VEND-02 (Compliance Check):** The system shall verify Tax IDs against public formats (e.g., GSTIN/EIN regex) and check for expiration dates on certifications.

**FR-VEND-03 (Approval Routing):** The system shall route completed vendor profiles to the Procurement Head for final sign-off before allowing payments.

---

## Module 5: Meeting Scheduling
Derived from handwritten note: "Meeting Scheduling -> Requirements capture -> Slot booking"
Functional Requirements: Smart Meeting Scheduler (Boss Mode)
Module Type: Helio Workflow Template Architecture: Option A (Engine-Driven) Dependencies: Google Calendar API, OpenAI API (Universal AI Node)

1. Workflow Definition Requirements
Since this follows the "Option A" architecture, the primary requirement is that the Engine can execute this specific chain of nodes based on a JSON configuration.

FR-MEET-01 (Natural Language Trigger): The system shall accept a raw text string from the user (e.g., "Meeting with Apurva next Tuesday at 2 PM") as the workflow input payload.

FR-MEET-02 (AI Parsing Node): The Engine must execute a Universal AI Node configured to extract structured data from the input text.

Input: Raw Text + Date/Time Context.

Output: JSON object {"subject": str, "start_time": ISO8601, "duration_minutes": int, "participants": [email]}.

FR-MEET-03 (Availability Check Node): The Engine must execute a Calendar Query Node that checks the "Free/Busy" status of the Host (User) for the requested slot.

Constraint: If status is BUSY, the workflow must branch to an Error/Termination state.

Constraint: If status is FREE, the workflow proceeds to booking.

FR-MEET-04 (Auto-Booking Node): The Engine must execute a Calendar Action Node to create the event.

Requirement: Must set conferenceDataVersion=1 (or equivalent) to auto-generate a Google Meet link.

Requirement: Must add extracted emails to the attendees list so the provider handles notifications.

2. API Integration Requirements (The "Nodes")
These are the specific "Building Blocks" your developers need to implement within the Engine.

A. The Google Calendar Node

FR-NODE-GCAL-01 (Authentication): The node shall handle OAuth2 (or Service Account) authentication using credentials stored in the user's encrypted settings.

FR-NODE-GCAL-02 (Check Availability): The node shall implement the events.list method (filtered by timeMin and timeMax) to detect conflicts.

FR-NODE-GCAL-03 (Create Event): The node shall implement the events.insert method. It must accept summary, start, end, and attendees as dynamic variables from previous nodes.



---

## Module 6: Document Management (RAG)
Derived from handwritten note: "Doc upload -> Categorization -> RAG Implementation"

**FR-DOC-01 (Smart Tagging):** Upon upload, the system shall generate metadata tags (e.g., "Contract", "Q3 Report", "NDA") based on file content.

**FR-DOC-02 (Vector Embedding):** The system shall chunk text documents and store their embeddings in a Vector Database (e.g., Pinecone/pgvector) for semantic search.

**FR-DOC-03 (Natural Language Search):** Users shall be able to ask questions like "What is the termination clause in the Acme contract?" and receive an answer with citations.

---

## Module 7: Payroll Automation
Derived from handwritten note: "Payroll automation"

**FR-PAY-01 (Salary Calculation):** The system shall calculate net pay based on Gross Salary, Tax Deductions, and Leave Days (pulled from the Leave module).

**FR-PAY-02 (Payslip Generation):** The system shall generate a password-protected PDF payslip for every employee.

**FR-PAY-03 (Dispatch):** The system shall automatically email payslips to employees on the scheduled payday.

**FR-PAY-04 (Anomaly Detection):** The system shall flag payroll variances (e.g., "Salary increased by >10%") for Admin review before finalization.

---

## Module 8: Inventory Management
Requested explicitly by user

**FR-INV-01 (Stock Tracking):** The system shall maintain real-time counts of physical assets/SKUs.

**FR-INV-02 (Low Stock Alerts):** The system shall trigger a notification when stock levels fall below a defined Reorder_Point.

**FR-INV-03 (Auto-Reorder Workflow):** When the "Low Stock" alert triggers, the system shall optionally draft a Purchase Order for the preferred vendor.

**FR-INV-04 (Usage Analytics):** The system shall provide a dashboard showing "Fastest Moving Items" and "Stagnant Stock."

---

# Non-Functional Requirements (NFR)

## Performance & Scalability
**NFR-PERF-01:** The system shall process an uploaded document (OCR + Extraction) in under 5 seconds for files < 5MB.

**NFR-PERF-02:** The RAG Search response time shall be under 2 seconds for the user.

**NFR-SCAL-01:** The backend shall support concurrent processing of at least 50 active workflows without degradation.

## Reliability & Availability
**NFR-REL-01 (Retry Logic):** If an external API (e.g., Gmail, OpenAI) fails, the system shall retry the operation 3 times with exponential backoff before marking the workflow as "Failed."

**NFR-REL-02 (State Persistence):** If the server restarts, paused workflows (e.g., "Waiting for Approval") must resume from their exact state without data loss.

## Security & Compliance
**NFR-SEC-01 (Data Encryption):** All documents stored in the system must be encrypted at rest (AES-256).

**NFR-SEC-02 (PII Redaction):** The system shall optionally redact sensitive fields (SSN, Bank Numbers) from logs and AI prompts.

**NFR-SEC-03 (Access Control):** Role-Based Access Control (RBAC) must ensure that "HR" users cannot see "Finance" workflows, and vice versa.

## Usability
**NFR-USE-01:** The Workflow Builder shall support "Drag and Drop" interactions with visual feedback for valid connections.

**NFR-USE-02:** The system shall provide a clear "Audit Log" for every action taken by the AI, explaining why a decision was made (Explainability).

