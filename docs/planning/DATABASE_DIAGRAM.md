# Sakthi Ledger — Target Database Architecture and Diagram

## 1. Architecture decision

The target enterprise system uses a relational transactional system of record, object storage for files, and derived analytical/read models.

- **Primary transactional database:** PostgreSQL-class relational database.
- **Document/object storage:** encrypted object storage for KYC, agreements, receipts, report artifacts, photographs, and attachments.
- **Cache/queues:** optional Redis-class service for sessions, idempotency, job state, and real-time counters.
- **Search:** database search initially; dedicated search index only when volume justifies it.
- **Analytics:** derived/materialized views or warehouse later; never a second mutable source of truth.

Rationale: payments, allocations, disbursements, approvals, reversals, day close, permissions, and immutable report snapshots require transactions, referential integrity, durable constraints, and clear audit relationships.

The existing Mongo/in-memory structures are treated as prototype data only and require migration into the target model before production.

## 2. Global conventions

- Primary keys: UUID/ULID internal IDs.
- Human-readable IDs: separately unique (`customer_no`, `loan_no`, `receipt_no`).
- Money: fixed-precision decimal or integer paise; never binary floating point.
- Time: UTC timestamp with timezone; business date stored separately where required.
- Soft-deactivation for master data; financial transactions are never deleted.
- Every mutable business record includes created/updated actor and timestamp.
- Version column supports optimistic concurrency.
- Sensitive values are encrypted at field/object level and access is audited.
- Status fields use constrained lifecycle values and transition services.

## 3. Organization, identity, and access

```mermaid
erDiagram
    ORGANIZATION ||--o{ AREA : operates
    AREA ||--o{ ROUTE : contains
    ORGANIZATION ||--o{ USER_ACCOUNT : employs
    USER_ACCOUNT ||--o{ USER_ROLE : receives
    ROLE ||--o{ USER_ROLE : assigned
    ROLE ||--o{ ROLE_PERMISSION : grants
    PERMISSION ||--o{ ROLE_PERMISSION : included
    USER_ACCOUNT ||--o{ USER_SCOPE : constrained_by
    AREA ||--o{ USER_SCOPE : scopes
    ROUTE ||--o{ USER_SCOPE : scopes
    USER_ACCOUNT ||--o{ SESSION : authenticates

    ORGANIZATION {
      uuid id PK
      string legal_name
      string display_name
      string timezone
      string currency
      string business_date_policy
      boolean active
    }
    AREA {
      uuid id PK
      uuid organization_id FK
      string code UK
      string name
      boolean active
    }
    ROUTE {
      uuid id PK
      uuid area_id FK
      string code UK
      string name
      boolean active
    }
    USER_ACCOUNT {
      uuid id PK
      uuid organization_id FK
      string user_no UK
      string username UK
      string name
      string email
      string mobile
      string password_hash
      boolean active
      timestamptz last_login_at
    }
    ROLE {
      uuid id PK
      string code UK
      string name
      boolean system_role
    }
    PERMISSION {
      uuid id PK
      string code UK
      string description
      string sensitivity
    }
    USER_ROLE {
      uuid user_id FK
      uuid role_id FK
    }
    ROLE_PERMISSION {
      uuid role_id FK
      uuid permission_id FK
    }
    USER_SCOPE {
      uuid id PK
      uuid user_id FK
      uuid area_id FK
      uuid route_id FK
      string scope_type
    }
    SESSION {
      uuid id PK
      uuid user_id FK
      string token_hash
      timestamptz expires_at
      timestamptz revoked_at
    }
```

## 4. Customer CRM and identity

```mermaid
erDiagram
    CUSTOMER ||--o{ CUSTOMER_CONTACT : has
    CUSTOMER ||--o{ CUSTOMER_ADDRESS : has
    CUSTOMER ||--o{ CUSTOMER_KYC : verifies
    CUSTOMER_KYC ||--o{ KYC_VERIFICATION_EVENT : records
    CUSTOMER ||--o{ CUSTOMER_RELATIONSHIP : source
    CUSTOMER ||--o{ CUSTOMER_RELATIONSHIP : target
    CUSTOMER ||--o{ EMPLOYMENT : has
    CUSTOMER ||--o{ BUSINESS_PROFILE : operates
    CUSTOMER ||--o{ INCOME_SOURCE : earns
    CUSTOMER ||--o{ HOUSEHOLD_EXPENSE : spends
    CUSTOMER ||--o{ CUSTOMER_CONSENT : grants
    CUSTOMER ||--o{ CUSTOMER_RISK_ASSESSMENT : assessed
    CUSTOMER ||--o{ CREDIT_SCORE : scored
    CUSTOMER ||--o{ CUSTOMER_LOCATION : located
    CUSTOMER ||--o{ FOLLOW_UP : requires
    CUSTOMER ||--o{ COMMUNICATION : receives
    CUSTOMER ||--o{ FIELD_VISIT : visited
    CUSTOMER ||--o{ NOTE : noted
    CUSTOMER ||--o{ DOCUMENT_LINK : owns

    CUSTOMER {
      uuid id PK
      string customer_no UK
      uuid organization_id FK
      uuid area_id FK
      uuid route_id FK
      uuid assigned_collector_id FK
      string full_name
      string preferred_language
      date date_of_birth
      string relationship_status
      string tier
      string kyc_status
      timestamptz created_at
      int version
    }
    CUSTOMER_CONTACT {
      uuid id PK
      uuid customer_id FK
      string type
      string normalized_value
      boolean primary_contact
      boolean verified
      boolean active
    }
    CUSTOMER_ADDRESS {
      uuid id PK
      uuid customer_id FK
      string type
      string line1
      string locality
      string district
      string state
      string postal_code
      decimal latitude
      decimal longitude
      string verification_status
    }
    CUSTOMER_KYC {
      uuid id PK
      uuid customer_id FK
      string document_type
      string identifier_hash UK
      bytes identifier_ciphertext
      string masked_identifier
      string status
      date expires_on
      uuid document_id FK
    }
    KYC_VERIFICATION_EVENT {
      uuid id PK
      uuid customer_kyc_id FK
      string from_status
      string to_status
      uuid actor_id FK
      string reason
      timestamptz occurred_at
    }
    CUSTOMER_RELATIONSHIP {
      uuid id PK
      uuid source_customer_id FK
      uuid target_customer_id FK
      string related_person_name
      string relationship_type
      string responsibility_type
      string verification_status
    }
    EMPLOYMENT {
      uuid id PK
      uuid customer_id FK
      string employer
      string occupation
      date start_date
      decimal monthly_income
      string verification_status
      boolean current
    }
    BUSINESS_PROFILE {
      uuid id PK
      uuid customer_id FK
      string business_name
      string sector
      date started_on
      decimal monthly_revenue
      decimal monthly_profit
      string verification_status
    }
    INCOME_SOURCE {
      uuid id PK
      uuid customer_id FK
      string source_type
      decimal amount
      string frequency
      string reliability
      string verification_status
    }
    HOUSEHOLD_EXPENSE {
      uuid id PK
      uuid customer_id FK
      string category
      decimal amount
      string frequency
    }
    CUSTOMER_CONSENT {
      uuid id PK
      uuid customer_id FK
      string consent_type
      string status
      string channel
      timestamptz granted_at
      timestamptz revoked_at
    }
    CUSTOMER_RISK_ASSESSMENT {
      uuid id PK
      uuid customer_id FK
      decimal score
      string risk_level
      string model_version
      json factors
      timestamptz assessed_at
    }
    CREDIT_SCORE {
      uuid id PK
      uuid customer_id FK
      string source
      decimal score
      string scale
      date retrieved_on
      date expires_on
      uuid report_document_id FK
    }
    CUSTOMER_LOCATION {
      uuid id PK
      uuid customer_id FK
      string location_type
      decimal latitude
      decimal longitude
      decimal accuracy_meters
      string source
      timestamptz captured_at
      uuid captured_by FK
    }
```

## 5. Loan origination, approval, and servicing

```mermaid
erDiagram
    CUSTOMER ||--o{ LOAN_APPLICATION : applies
    LOAN_PRODUCT ||--o{ LOAN_APPLICATION : requested_as
    LOAN_APPLICATION ||--o{ APPLICATION_STAGE_EVENT : progresses
    LOAN_APPLICATION ||--o{ CREDIT_ASSESSMENT : assessed
    LOAN_APPLICATION ||--o{ POLICY_DEVIATION : deviates
    LOAN_APPLICATION ||--o{ APPROVAL_REQUEST : requires
    APPROVAL_REQUEST ||--o{ APPROVAL_DECISION : receives
    LOAN_APPLICATION ||--o| LOAN_ACCOUNT : becomes
    LOAN_PRODUCT ||--o{ LOAN_ACCOUNT : governs
    LOAN_ACCOUNT ||--|{ REPAYMENT_INSTALLMENT : schedules
    LOAN_ACCOUNT ||--o{ LOAN_ASSIGNMENT : assigned
    LOAN_ACCOUNT ||--o{ LOAN_STATUS_EVENT : changes
    LOAN_ACCOUNT ||--o{ DISBURSEMENT : disburses
    LOAN_ACCOUNT ||--o{ PAYMENT_ALLOCATION : receives
    LOAN_ACCOUNT ||--o{ PROMISE_TO_PAY : promises
    LOAN_ACCOUNT ||--o{ DELINQUENCY_CASE : escalates
    LOAN_ACCOUNT ||--o{ DOCUMENT_LINK : documents

    LOAN_PRODUCT {
      uuid id PK
      string code UK
      string name
      string scheme_type
      int default_term
      decimal min_principal
      decimal max_principal
      decimal default_rate
      json repayment_policy
      boolean active
      int version
    }
    LOAN_APPLICATION {
      uuid id PK
      string application_no UK
      uuid customer_id FK
      uuid product_id FK
      decimal requested_principal
      decimal recommended_principal
      decimal proposed_rate
      int proposed_term
      string stage
      string status
      uuid owner_id FK
      timestamptz submitted_at
      int version
    }
    APPLICATION_STAGE_EVENT {
      uuid id PK
      uuid application_id FK
      string from_stage
      string to_stage
      uuid actor_id FK
      string reason
      timestamptz occurred_at
    }
    CREDIT_ASSESSMENT {
      uuid id PK
      uuid application_id FK
      decimal monthly_income
      decimal monthly_expense
      decimal existing_obligations
      decimal disposable_income
      decimal recommended_payment
      string outcome
      json factors
    }
    POLICY_DEVIATION {
      uuid id PK
      uuid application_id FK
      string policy_code
      string description
      string severity
      string status
    }
    LOAN_ACCOUNT {
      uuid id PK
      string loan_no UK
      uuid application_id FK
      uuid customer_id FK
      uuid product_id FK
      decimal principal
      decimal interest_rate
      int term
      date disbursement_date
      date maturity_date
      string status
      decimal principal_outstanding
      decimal total_outstanding
      int dpd
      string health
      int version
    }
    REPAYMENT_INSTALLMENT {
      uuid id PK
      uuid loan_id FK
      int sequence_no
      date due_date
      decimal principal_due
      decimal interest_due
      decimal charge_due
      decimal amount_paid
      string status
    }
    LOAN_ASSIGNMENT {
      uuid id PK
      uuid loan_id FK
      uuid collector_id FK
      uuid route_id FK
      date effective_from
      date effective_to
    }
    LOAN_STATUS_EVENT {
      uuid id PK
      uuid loan_id FK
      string from_status
      string to_status
      string reason
      uuid actor_id FK
      timestamptz occurred_at
    }
    DISBURSEMENT {
      uuid id PK
      string disbursement_no UK
      uuid loan_id FK
      decimal amount
      string mode
      string external_reference
      date business_date
      string status
      uuid posted_by FK
      timestamptz posted_at
    }
```

## 6. Payments, collections, cash, and delinquency

```mermaid
erDiagram
    LOAN_ACCOUNT ||--o{ PAYMENT : paid
    CUSTOMER ||--o{ PAYMENT : makes
    PAYMENT ||--|{ PAYMENT_ALLOCATION : allocates
    REPAYMENT_INSTALLMENT ||--o{ PAYMENT_ALLOCATION : satisfies
    PAYMENT ||--o| RECEIPT : proves
    PAYMENT ||--o{ PAYMENT_REVERSAL : reverses
    USER_ACCOUNT ||--o{ COLLECTION_ASSIGNMENT : receives
    ROUTE ||--o{ COLLECTION_ASSIGNMENT : follows
    COLLECTION_ASSIGNMENT ||--o{ COLLECTION_TASK : includes
    CUSTOMER ||--o{ COLLECTION_TASK : concerns
    LOAN_ACCOUNT ||--o{ COLLECTION_TASK : concerns
    COLLECTION_TASK ||--o{ PROMISE_TO_PAY : records
    COLLECTION_TASK ||--o{ FIELD_VISIT : records
    USER_ACCOUNT ||--o{ CASH_HANDOVER : hands_over
    BUSINESS_DAY ||--o{ CASH_HANDOVER : groups
    BUSINESS_DAY ||--o{ RECONCILIATION_ITEM : reconciles
    BUSINESS_DAY ||--o| DAY_CLOSE : closes
    LOAN_ACCOUNT ||--o{ DELINQUENCY_CASE : creates
    DELINQUENCY_CASE ||--o{ RECOVERY_ACTION : receives

    PAYMENT {
      uuid id PK
      string transaction_no UK
      uuid customer_id FK
      uuid loan_id FK
      decimal amount
      string mode
      string external_reference
      uuid collector_id FK
      date business_date
      string status
      string idempotency_key UK
      timestamptz posted_at
      uuid posted_by FK
    }
    PAYMENT_ALLOCATION {
      uuid id PK
      uuid payment_id FK
      uuid loan_id FK
      uuid installment_id FK
      string component
      decimal amount
    }
    RECEIPT {
      uuid id PK
      string receipt_no UK
      uuid payment_id FK
      string status
      uuid artifact_id FK
      timestamptz issued_at
    }
    PAYMENT_REVERSAL {
      uuid id PK
      uuid original_payment_id FK
      string reversal_transaction_no UK
      decimal amount
      string reason
      uuid approval_request_id FK
      uuid posted_by FK
      timestamptz posted_at
    }
    COLLECTION_ASSIGNMENT {
      uuid id PK
      date business_date
      uuid collector_id FK
      uuid route_id FK
      string status
      decimal demand_amount
      decimal collected_amount
    }
    COLLECTION_TASK {
      uuid id PK
      uuid assignment_id FK
      uuid customer_id FK
      uuid loan_id FK
      int sequence_no
      decimal due_amount
      string outcome
      string status
    }
    PROMISE_TO_PAY {
      uuid id PK
      uuid customer_id FK
      uuid loan_id FK
      uuid collection_task_id FK
      decimal promised_amount
      date promised_date
      string status
      uuid owner_id FK
    }
    FIELD_VISIT {
      uuid id PK
      uuid customer_id FK
      uuid collection_task_id FK
      uuid collector_id FK
      string purpose
      string outcome
      decimal latitude
      decimal longitude
      decimal accuracy_meters
      timestamptz visited_at
    }
    CASH_HANDOVER {
      uuid id PK
      string handover_no UK
      uuid business_day_id FK
      uuid collector_id FK
      uuid received_by FK
      decimal expected_amount
      decimal physical_amount
      decimal variance
      string status
      timestamptz handed_over_at
    }
    BUSINESS_DAY {
      uuid id PK
      date business_date UK
      string status
      decimal opening_cash
      uuid opened_by FK
      timestamptz opened_at
    }
    RECONCILIATION_ITEM {
      uuid id PK
      uuid business_day_id FK
      string source_type
      uuid source_id
      decimal expected_amount
      decimal actual_amount
      decimal variance
      string status
      string resolution
    }
    DAY_CLOSE {
      uuid id PK
      string close_no UK
      uuid business_day_id FK
      decimal expected_close
      decimal physical_close
      decimal variance
      string status
      uuid approval_request_id FK
      uuid closed_by FK
      timestamptz closed_at
    }
    DELINQUENCY_CASE {
      uuid id PK
      uuid loan_id FK
      string ageing_bucket
      int dpd
      decimal amount_at_risk
      string strategy
      uuid owner_id FK
      string status
    }
    RECOVERY_ACTION {
      uuid id PK
      uuid case_id FK
      string action_type
      string outcome
      uuid actor_id FK
      timestamptz occurred_at
    }
```

## 7. Communications, tasks, documents, and timeline

```mermaid
erDiagram
    CUSTOMER ||--o{ COMMUNICATION : receives
    CUSTOMER ||--o{ FOLLOW_UP : has
    FOLLOW_UP ||--o{ REMINDER : schedules
    CUSTOMER ||--o{ NOTE : has
    DOCUMENT ||--o{ DOCUMENT_VERSION : versions
    DOCUMENT ||--o{ DOCUMENT_LINK : links
    FILE_OBJECT ||--o{ DOCUMENT_VERSION : stores
    FILE_OBJECT ||--o{ ATTACHMENT : stores
    COMMUNICATION ||--o{ ATTACHMENT : attaches
    FIELD_VISIT ||--o{ ATTACHMENT : attaches
    NOTE ||--o{ ATTACHMENT : attaches
    TIMELINE_EVENT }o--|| CUSTOMER : aggregates

    COMMUNICATION {
      uuid id PK
      uuid customer_id FK
      uuid related_loan_id FK
      string channel
      string direction
      string recipient
      string provider_reference
      string delivery_status
      string outcome
      uuid actor_id FK
      timestamptz occurred_at
    }
    FOLLOW_UP {
      uuid id PK
      uuid customer_id FK
      uuid related_loan_id FK
      string purpose
      uuid owner_id FK
      timestamptz due_at
      string priority
      string status
      string outcome
    }
    REMINDER {
      uuid id PK
      uuid follow_up_id FK
      uuid user_id FK
      timestamptz remind_at
      string status
    }
    NOTE {
      uuid id PK
      uuid customer_id FK
      uuid related_loan_id FK
      uuid related_visit_id FK
      uuid author_id FK
      string visibility
      text content
      timestamptz created_at
      uuid corrects_note_id FK
    }
    DOCUMENT {
      uuid id PK
      string document_no UK
      string document_type
      string sensitivity
      string status
      date expires_on
    }
    DOCUMENT_VERSION {
      uuid id PK
      uuid document_id FK
      int version_no
      uuid file_object_id FK
      string checksum
      uuid uploaded_by FK
      timestamptz uploaded_at
    }
    DOCUMENT_LINK {
      uuid id PK
      uuid document_id FK
      string entity_type
      uuid entity_id
      string relationship
    }
    FILE_OBJECT {
      uuid id PK
      string storage_key UK
      string filename
      string mime_type
      bigint size_bytes
      string checksum
      string encryption_key_ref
      string scan_status
    }
    ATTACHMENT {
      uuid id PK
      uuid file_object_id FK
      string entity_type
      uuid entity_id
      string caption
    }
    TIMELINE_EVENT {
      uuid id PK
      uuid customer_id FK
      uuid loan_id FK
      string event_type
      string entity_type
      uuid entity_id
      uuid actor_id FK
      json summary
      timestamptz occurred_at
    }
```

Timeline events may be persisted as a read model/outbox projection from immutable domain events. They do not replace the source tables.

## 8. Approvals, notifications, reports, and audit

```mermaid
erDiagram
    APPROVAL_REQUEST ||--o{ APPROVAL_DECISION : receives
    USER_ACCOUNT ||--o{ APPROVAL_DECISION : decides
    USER_ACCOUNT ||--o{ NOTIFICATION : receives
    REPORT_DEFINITION ||--o{ REPORT_RUN : generates
    REPORT_RUN ||--o{ REPORT_ARTIFACT : produces
    FILE_OBJECT ||--o{ REPORT_ARTIFACT : stores
    REPORT_ARTIFACT ||--o{ REPORT_SHARE : shares
    REPORT_ARTIFACT ||--o{ EMAIL_DELIVERY : emails
    REPORT_DEFINITION ||--o{ REPORT_SCHEDULE : schedules
    USER_ACCOUNT ||--o{ SAVED_VIEW : owns
    USER_ACCOUNT ||--o{ AUDIT_EVENT : acts

    APPROVAL_REQUEST {
      uuid id PK
      string request_no UK
      string entity_type
      uuid entity_id
      string approval_type
      decimal financial_impact
      string status
      uuid requested_by FK
      timestamptz requested_at
      timestamptz due_at
    }
    APPROVAL_DECISION {
      uuid id PK
      uuid request_id FK
      uuid decided_by FK
      string decision
      string reason
      json conditions
      timestamptz decided_at
    }
    NOTIFICATION {
      uuid id PK
      uuid user_id FK
      string category
      string priority
      string entity_type
      uuid entity_id
      string message
      string status
      timestamptz created_at
      timestamptz resolved_at
    }
    REPORT_DEFINITION {
      uuid id PK
      string code UK
      string name
      string category
      int version
      json parameter_schema
      string required_permission
      boolean active
    }
    REPORT_RUN {
      uuid id PK
      string run_no UK
      uuid report_definition_id FK
      int report_version
      uuid requested_by FK
      json parameters
      json scope
      string data_watermark
      json totals
      bigint row_count
      string status
      timestamptz generated_at
    }
    REPORT_ARTIFACT {
      uuid id PK
      uuid report_run_id FK
      uuid file_object_id FK
      string format
      string status
      string checksum
      timestamptz expires_at
    }
    REPORT_SHARE {
      uuid id PK
      uuid artifact_id FK
      string token_hash UK
      json recipient_scope
      int download_limit
      int download_count
      timestamptz expires_at
      timestamptz revoked_at
    }
    EMAIL_DELIVERY {
      uuid id PK
      uuid artifact_id FK
      string provider_reference
      json recipients
      string status
      timestamptz queued_at
      timestamptz delivered_at
    }
    REPORT_SCHEDULE {
      uuid id PK
      uuid report_definition_id FK
      uuid owner_id FK
      json parameters
      string schedule_expression
      json delivery
      boolean active
    }
    SAVED_VIEW {
      uuid id PK
      uuid user_id FK
      string module
      string name
      json filters
      json sorting
      json columns
      string density
    }
    AUDIT_EVENT {
      uuid id PK
      string event_no UK
      uuid actor_id FK
      string actor_role
      string action
      string entity_type
      uuid entity_id
      string result
      string reason
      json before_data
      json after_data
      string correlation_id
      string ip_address
      string device_id
      timestamptz occurred_at
      string integrity_hash
    }
```

## 9. Configuration and lifecycle

Core versioned configuration tables:

- `organization_setting`
- `loan_product`
- `repayment_policy`
- `arrears_policy`
- `approval_policy`
- `receipt_sequence`
- `communication_template`
- `notification_rule`
- `report_definition`
- `retention_policy`
- `integration_config`
- `business_day`
- `configuration_change_request`

Each versioned configuration has draft, approved, scheduled, active, superseded, and revoked states where applicable.

```mermaid
erDiagram
    ORGANIZATION ||--o{ CONFIGURATION_VERSION : configures
    CONFIGURATION_VERSION ||--o{ CONFIGURATION_CHANGE_REQUEST : proposed_by
    CONFIGURATION_CHANGE_REQUEST ||--o| APPROVAL_REQUEST : may_require
    ORGANIZATION ||--o{ BUSINESS_CALENDAR_DAY : schedules
    ORGANIZATION ||--o{ BACKUP_JOB : protects
    BACKUP_JOB ||--o{ BACKUP_ARTIFACT : creates
    FILE_OBJECT ||--o{ BACKUP_ARTIFACT : stores
    ORGANIZATION ||--o{ INTEGRATION_CONFIG : integrates
    INTEGRATION_CONFIG ||--o{ INTEGRATION_JOB : runs
    INTEGRATION_CONFIG ||--o{ WEBHOOK_EVENT : receives
    USER_ACCOUNT ||--o{ DEVICE_REGISTRATION : uses

    CONFIGURATION_VERSION {
      uuid id PK
      uuid organization_id FK
      string config_type
      string config_key
      int version_no
      json value
      string status
      timestamptz effective_from
      timestamptz effective_to
      uuid created_by FK
    }
    CONFIGURATION_CHANGE_REQUEST {
      uuid id PK
      uuid configuration_version_id FK
      string reason
      json impact_summary
      uuid requested_by FK
      string status
      timestamptz requested_at
    }
    BUSINESS_CALENDAR_DAY {
      uuid id PK
      uuid organization_id FK
      date calendar_date
      string day_type
      string description
      boolean collection_allowed
    }
    BACKUP_JOB {
      uuid id PK
      string job_no UK
      uuid organization_id FK
      string backup_type
      string status
      uuid requested_by FK
      timestamptz started_at
      timestamptz completed_at
      string failure_code
    }
    BACKUP_ARTIFACT {
      uuid id PK
      uuid backup_job_id FK
      uuid file_object_id FK
      string checksum
      string encryption_key_ref
      timestamptz expires_at
      string restore_test_status
    }
    INTEGRATION_CONFIG {
      uuid id PK
      uuid organization_id FK
      string provider_type
      string provider_name
      string status
      string secret_reference
      json non_secret_config
      int version
    }
    INTEGRATION_JOB {
      uuid id PK
      uuid integration_config_id FK
      string job_type
      string correlation_id
      string status
      int attempt_no
      timestamptz started_at
      timestamptz completed_at
    }
    WEBHOOK_EVENT {
      uuid id PK
      uuid integration_config_id FK
      string provider_event_id UK
      string event_type
      string signature_status
      string processing_status
      json payload_encrypted
      timestamptz received_at
    }
    DEVICE_REGISTRATION {
      uuid id PK
      uuid user_id FK
      string device_id UK
      string platform
      string push_token_ciphertext
      timestamptz last_seen_at
      timestamptz revoked_at
    }
```

## 10. Critical transaction boundaries

### Payment posting transaction

Atomic:

1. Idempotency check
2. Payment insert
3. Allocation inserts
4. Instalment balances/status update
5. Loan totals/DPD/health update
6. Receipt number and receipt insert
7. Collection task/assignment totals update
8. Domain event/outbox and audit event

### Disbursement transaction

Atomic:

1. Approval/documentation precondition
2. Loan account activation
3. Disbursement insert
4. Repayment schedule generation
5. Assignment creation
6. Timeline/outbox and audit

### Reversal transaction

Atomic linked reversal; original payment and receipt remain immutable.

### Day-close transaction

Close checks, variance approval, close record, business-day lock, report snapshot, and audit must agree.

## 11. Required uniqueness and indexes

- Unique: organization+customer_no, loan_no, application_no, transaction_no, receipt_no, report run/artifact identifiers.
- Unique Aadhaar/identity hash according to organization policy.
- Unique payment idempotency key.
- Customer search: normalized name, mobile, masked identifier suffix, area, route.
- Loan workbench: status, customer, collector, area, product, DPD, maturity.
- Collection queue: business date, collector, route, status, sequence.
- Timeline: customer+occurred_at, loan+occurred_at.
- Follow-up/reminder: owner+status+due_at.
- Audit: occurred_at, actor, entity, action, result, correlation ID.
- Report run/artifact: definition, requested_by, status, generated_at, expiry.

## 12. Privacy and retention

- Aadhaar ciphertext and hash are never returned together to ordinary clients.
- Aadhaar reveal uses a separate authorized service and audit event.
- Document storage keys are never public URLs.
- GPS accuracy/source/consent are stored with coordinates.
- Communications retain consent, provider, and delivery metadata.
- Report snapshots/artifacts inherit field-level masking and retention.
- Audit events are append-only and integrity protected.
- Retention jobs create auditable tombstone/retention events; financial records remain according to statutory policy.

## 13. Current-to-target gap

Existing prototype collections cover users, areas, customers, loans, payments, audit logs, overdue alerts, backups, notifications, and verification events. The target model adds the missing enterprise domains:

- Role permissions and area/route scopes
- Full CRM relationships and communications
- Employment, business, income, expenses
- Explainable risk and credit scores
- Applications, stages, assessments, deviations, approvals
- Repayment instalments and typed allocations
- Payment idempotency and linked reversals
- Routes, tasks, promises, visits, GPS, handovers, reconciliation, day close
- Documents, versions, attachments, and object storage
- Immutable report snapshots, actual artifacts, sharing, and email delivery
- Versioned configuration and approval policies
- Durable notification/task lifecycle
- Correlated immutable audit model

## 14. Database acceptance gate

- Every Screen Map field has a source or explicit derived calculation.
- Every workflow mutation has a transaction boundary and audit event.
- Every status transition is constrained and documented.
- Every sensitive field has encryption, masking, permission, and retention rules.
- Payment/disbursement/reversal/day-close tests prove atomicity and idempotency.
- Report artifacts prove format, snapshot, permission, and retention linkage.
- No production money field uses floating-point storage.
