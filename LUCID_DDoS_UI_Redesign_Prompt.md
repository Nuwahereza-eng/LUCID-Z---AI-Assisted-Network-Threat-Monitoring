# LUCID-DDoS UI Redesign Prompt

Act as a world-class Senior UI/UX Designer and Frontend Engineer who builds award-winning cybersecurity SaaS products and enterprise AI dashboards.

## Project

**LUCID-DDoS** is an AI-powered network threat detection platform being developed for the IBM Z Datathon 2026.

The application is already running, and the CNN model is trained and making predictions. The current UI needs a major visual improvement. Transform the existing interface into a polished, production-quality cybersecurity command center.

## 1. Design Inspiration

Use the design principles of these products as inspiration:

- **IBM Cloud and IBM Security:** enterprise credibility, structured layouts, clear information hierarchy, restrained color.
- **CrowdStrike Falcon:** security operations, threat visibility, actionable alerts.
- **Microsoft Defender:** clean security analytics, severity indicators, readable incident information.
- **Datadog:** monitoring dashboards, time-series charts, operational metrics.
- **Linear:** excellent spacing, typography, subtle borders, polished interactions.

Create an original LUCID-DDoS identity. Do not copy logos, proprietary assets, or exact layouts.

## 2. Visual Direction

Create a sophisticated dark cybersecurity interface.

Suggested palette:

- Background: deep charcoal/navy, approximately `#0B1020`.
- Main panels: approximately `#111827`.
- Borders: subtle slate, approximately `#273449`.
- Primary accent: electric cyan, approximately `#22D3EE`.
- Secondary accent: indigo, approximately `#818CF8`.
- Threat indicators: restrained red for critical threats, amber for warnings, green for healthy status.
- Text: high-contrast white and accessible muted gray.

Use a modern sans-serif font such as Inter or IBM Plex Sans.

Avoid:

- Generic black-and-grey boxes everywhere.
- Excessive gradients, neon effects, or colors.
- Giant headings and oversized empty cards.
- Excessive rounded corners.
- Unnecessary animations, decorative charts, or fake metrics.
- Generic AI-generated landing-page styling.

The result should feel like a real enterprise security product, not a student template.

## 3. Application Layout

### Sidebar

Include:

- LUCID-DDoS logo and product name.
- Overview.
- Live Traffic.
- Threat Detection.
- Traffic Analysis.
- Model Performance.
- Events / Alerts.
- Settings.
- Compact user/profile section at the bottom.

Use clear Lucide icons, consistent spacing, active navigation indicators, and a collapsible sidebar where appropriate.

### Top Bar

Include:

- Current page title and breadcrumbs.
- System health indicator.
- Model status.
- IBM Z integration status.
- Last-updated timestamp.
- Refresh action where appropriate.

### Main Overview Dashboard

Create a polished command center with the following sections.

#### A. Executive metrics

- Total traffic flows processed.
- Benign flows.
- Suspected DDoS flows.
- Detection rate or another correctly defined model metric.
- Average inference latency.

Each metric card should have a clear label, prominent value, compact icon, and comparisons only when real historical data exists.

#### B. Traffic analytics

- A polished time-series chart showing traffic volume over time.
- Separate benign and suspected malicious traffic when supported by the data.
- Useful time filters.
- Tooltips, readable axes, and responsive chart sizing.

#### C. Threat monitoring panel

- Recent classifications and alerts.
- Severity, timestamp, prediction, confidence when available, and relevant traffic-flow identifiers.
- Clear empty, loading, and error states.
- Clicking an event should open useful details if supported.

#### D. Model health panel

- Model loading and inference status.
- Measured inference latency.
- Precision, recall, F1-score, and false-positive rate when validated results are available.
- A clear distinction between offline evaluation metrics and live operational metrics.

#### E. IBM Z integration panel

- Connection status based on an actual connectivity check.
- Integration method or endpoint name where appropriate.
- Last successful request and response status if available.
- If IBM Z is unavailable, show **Not connected** or **Simulation mode** honestly.
- Never imply that the model runs on IBM Z unless it genuinely does.

## 4. Live Traffic Page

Design a professional traffic-monitoring interface with:

- A filterable, searchable traffic-flow table.
- Classification badges for benign and suspected DDoS traffic.
- Timestamps, relevant flow features, and confidence where available.
- Pagination or virtualization if needed.
- A detailed event drawer or page.
- Clear indicators for stale data and processing failures.

Do not expose sensitive information unnecessarily.

## 5. Threat Detection Page

Include:

- Recent detections.
- Severity and confidence indicators.
- Filtering by classification and time range.
- Traffic-flow details.
- A concise explanation of why an event was flagged, using only available model inputs or explainability outputs.
- A safe, clearly labelled way to replay existing labelled test samples if supported.

Do not claim that a detection automatically blocks an attack unless blocking is genuinely implemented.

## 6. Model Performance Page

Present measured model evaluation results professionally:

- Confusion matrix.
- Precision, recall, F1-score, and false-positive rate.
- Inference latency distribution.
- Dataset and evaluation context.
- A clear distinction between training, validation, and test results.

Use the existing evaluation pipeline where available. Never invent numbers or display hardcoded placeholder metrics as actual performance.

## 7. Technical Constraints

Before changing anything:

1. Inspect the existing project structure and identify the frontend framework, routes, components, styles, API endpoints, and data contracts.
2. Identify which existing features already work.
3. Preserve the CNN model, preprocessing pipeline, backend APIs, prediction logic, and deployment configuration.
4. Reuse existing dependencies and UI libraries where possible.
5. Do not rewrite the entire application or install unnecessary packages.
6. Do not replace real API data with hardcoded demo data.
7. Do not break existing routes, environment variables, or deployment.
8. Make changes incrementally and explain the main files being modified.

If the frontend is Streamlit, improve the existing Streamlit application using supported styling and components rather than migrating frameworks unless there is a compelling reason. If it already uses React or Next.js, work within the existing stack.

## 8. UX and Quality Requirements

- Responsive on desktop, tablet, and mobile.
- Consistent spacing and typography.
- Accessible contrast and keyboard navigation.
- Smooth but restrained transitions.
- Professional tables, charts, tooltips, dialogs, and status indicators.
- Skeleton loading states where appropriate.
- Useful empty states and clear error messages.
- No broken links or nonfunctional buttons.
- No fake live updates or simulated IBM Z connectivity presented as real.
- Maintainable, reusable components rather than duplicated markup.

## 9. Implementation Workflow

Work in this order:

### Phase 1: Audit

Inspect the existing frontend and report the current stack and key problems.

### Phase 2: Plan

Propose a concise redesign plan and identify the minimum files that need changes.

### Phase 3: Implement

Implement the redesign directly in the existing project.

### Phase 4: Verify

Run available checks, launch the application, inspect the main pages, and fix visual or functional regressions.

### Phase 5: Report

Summarize what changed, what still works, any remaining issues, and the exact command to run the application.

Prioritize a complete, coherent, polished dashboard over implementing many unfinished pages.

The final result should look like a premium AI cybersecurity operations platform that can confidently be demonstrated to IBM Z Datathon judges. Start by inspecting the current codebase, then implement the redesign. Do not stop after providing mockups or a design proposal.
