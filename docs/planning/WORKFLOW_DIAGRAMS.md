# Sakthi Ledger — Workflow Diagrams

## 1. Customer onboarding and KYC

```mermaid
flowchart TD
    A[Click New Customer] --> B[Identity and phone]
    B --> C{Potential duplicate?}
    C -- Yes --> D[Review matching customers]
    D --> E{Same person?}
    E -- Yes --> F[Open existing Customer 360 or request merge]
    E -- No --> G[Record duplicate resolution]
    C -- No --> H[Address area and route]
    G --> H
    H --> I[KYC documents and consent]
    I --> J[Employment business income household]
    J --> K[Family guarantor references]
    K --> L[Review completeness and declarations]
    L --> M{Save or submit?}
    M -- Save draft --> N[Draft work queue]
    M -- Submit --> O[KYC verification queue]
    O --> P{Decision}
    P -- Verify --> Q[Verified Customer 360]
    P -- Correction --> R[Return with required corrections]
    P -- Fail --> S[Failed status reason and escalation]
    P -- Manual approval --> T[Authorized decision and audit]
```

Controls: Aadhaar hash duplicate check, ciphertext storage, masked UI, consent, reason capture, role permission, audit.

## 2. Loan origination to disbursement

```mermaid
flowchart TD
    A[Click New Loan] --> B[Open staged wide drawer]
    B --> C[Select customer and review exposure]
    C --> D{KYC complete?}
    D -- No --> E[Save draft and create KYC blocker]
    D -- Yes --> F[Select scheme and terms]
    F --> G[Calculate schedule and affordability]
    G --> H[Verification guarantor documents visits]
    H --> I[Risk credit score and recommendation]
    I --> J{Policy deviation?}
    J -- Yes --> K[Capture deviation and reason]
    J -- No --> L[Review application]
    K --> L
    L --> M[Submit for review]
    M --> N[Manager review]
    N --> O{Decision}
    O -- Return --> P[Applicant owner rework]
    P --> L
    O -- Reject --> Q[Close application with reason]
    O -- Escalate --> R[Higher approval queue]
    O -- Approve --> S[Documentation checklist]
    R --> S
    S --> T{Complete?}
    T -- No --> U[Document blocker]
    T -- Yes --> V[Maker enters disbursement]
    V --> W[Checker authorization if required]
    W --> X[Atomic loan schedule and disbursement posting]
    X --> Y[Loan 360 receipt agreement timeline audit]
```

## 3. Payment posting and receipt

```mermaid
sequenceDiagram
    actor User
    participant UI as Payment drawer
    participant API as Payment service
    participant DB as Transactional database
    participant ART as Receipt service
    participant AUD as Audit/outbox

    User->>UI: New Payment
    UI->>API: Lookup customer/loan due state
    API-->>UI: Identity, outstanding, schedule, duplicate context
    User->>UI: Amount and mode
    UI->>API: Allocation preview request
    API-->>UI: Principal/interest/charges/remaining
    User->>UI: Confirm exact payment
    UI->>API: Post with idempotency key
    API->>DB: Begin transaction
    DB->>DB: Insert payment and allocations
    DB->>DB: Update instalments, loan, collection totals
    DB->>DB: Create receipt number
    DB->>AUD: Write domain/audit event
    DB-->>API: Commit confirmed state
    API->>ART: Generate confirmed receipt artifact
    API-->>UI: Transaction, balance, receipt, delivery state
    UI-->>User: Animated confirmed receipt
```

Failure branches:

- Before commit → “Payment was not posted. No money was recorded.”
- Commit confirmed, artifact failed → payment succeeds; receipt regeneration available.
- Unknown network outcome → verification by idempotency/correlation ID before retry.

## 4. Collector daily operations

```mermaid
flowchart LR
    subgraph Manager
      A[Open business day] --> B[Calculate demand]
      B --> C[Assign routes and collectors]
    end
    subgraph Collector
      C --> D[Sync mobile route]
      D --> E[Visit or contact customer]
      E --> F{Outcome}
      F -- Payment --> G[Post payment and receipt]
      F -- Promise --> H[Promise and reminder]
      F -- No contact --> I[Visit outcome and note]
      F -- Dispute or hardship --> J[Escalation]
      G --> K[Route progress]
      H --> K
      I --> K
      J --> K
      K --> L{Route complete?}
      L -- No --> E
      L -- Yes --> M[Review cash digital exceptions]
      M --> N[Cash handover]
    end
    subgraph Accountant
      N --> O[Count verify and reconcile]
      O --> P{Variance?}
      P -- Yes --> Q[Resolve or request approval]
      P -- No --> R[Accept handover]
      Q --> R
    end
```

## 5. Delinquency and recovery

```mermaid
stateDiagram-v2
    [*] --> Current
    Current --> DueSoon: approaching due
    DueSoon --> Current: payment received
    DueSoon --> DPD_1_30: due missed
    DPD_1_30 --> Current: cured
    DPD_1_30 --> DPD_31_60: ageing
    DPD_31_60 --> Current: cured
    DPD_31_60 --> DPD_61_90: ageing
    DPD_61_90 --> Current: cured
    DPD_61_90 --> DPD_91_120: ageing
    DPD_91_120 --> Current: cured
    DPD_91_120 --> DPD_120_PLUS: ageing
    DPD_120_PLUS --> Restructured: approved restructure
    DPD_120_PLUS --> WrittenOff: approved write-off
    Restructured --> Current: revised schedule current
    WrittenOff --> Recovery: recovery action
    Recovery --> Closed: recovered/settled
    Current --> Closed: fully paid
```

Each transition records DPD, amount at risk, policy version, actor/system source, strategy, and timeline/audit event.

## 6. Promise and follow-up

```mermaid
flowchart TD
    A[Record promise or follow-up] --> B[Owner due date channel amount/outcome]
    B --> C[Calendar notification and work queue]
    C --> D{At due time}
    D --> E[Contact or collection action]
    E --> F{Outcome}
    F -- Completed --> G[Capture outcome and next action]
    F -- Paid --> H[Link confirmed payment]
    F -- Snoozed --> I[New due time and reason]
    F -- Missed/broken --> J[Escalate priority and risk signal]
    G --> K[Timeline update]
    H --> K
    I --> C
    J --> L[Delinquency queue]
```

## 7. Payment reversal approval

```mermaid
sequenceDiagram
    actor Requester
    participant PAY as Payment/Receipt
    participant APR as Approval service
    actor Approver
    participant DB as Transactional database

    Requester->>PAY: Request reversal with reason/evidence
    PAY->>APR: Financial impact and policy route
    APR-->>Approver: Approval task
    Approver->>APR: Review original, reconciliation, close impact
    alt Rejected
      APR-->>Requester: Rejected with reason
    else Approved
      APR->>DB: Atomic linked reversal
      DB->>DB: Reverse allocations and balances
      DB->>DB: Mark receipt reversed, preserve original
      DB-->>APR: Reversal transaction reference
      APR-->>Requester: Confirmed reversal and updated balance
    end
```

## 8. Cash reconciliation and day close

```mermaid
flowchart TD
    A[Business day open] --> B[Opening cash]
    B --> C[Payments handovers deposits expenses]
    C --> D[Calculate expected close]
    D --> E[Record physical close]
    E --> F{Variance or unresolved items?}
    F -- No --> G[Run close checks]
    F -- Yes --> H[Match resolve or explain]
    H --> I{Above threshold?}
    I -- Yes --> J[Approval request]
    I -- No --> G
    J --> K{Approved?}
    K -- No --> H
    K -- Yes --> G
    G --> L{All checks pass?}
    L -- No --> H
    L -- Yes --> M[Confirm close summary]
    M --> N[Lock business day]
    N --> O[Close report snapshot and audit]
```

## 9. Report generation and delivery

```mermaid
flowchart TD
    A[Select report and parameters] --> B[Validate permission and scope]
    B --> C[Create immutable report run]
    C --> D[Query calculate format snapshot]
    D --> E{Generation status}
    E -- Failed --> F[Stage-specific error and retry]
    E -- Ready --> G[Designed Preview]
    G --> H{Action}
    H -- PDF --> I[Generate valid PDF artifact]
    H -- Excel --> J[Generate valid XLSX artifact]
    H -- CSV --> K[Generate CSV or ZIP artifact]
    H -- Print --> L[Dedicated print document]
    H -- Share --> M[Generate/select artifact and secure link]
    H -- Email --> N[Generate/select artifact and server delivery]
    I --> O[Artifact validation checksum history audit]
    J --> O
    K --> O
    M --> O
    N --> O
    L --> P[Print outcome audit]
```

## 10. Customer communication and visit

```mermaid
flowchart TD
    A[Customer 360 or route] --> B{Action}
    B -- Call --> C[Consent contact and call outcome]
    B -- SMS --> D[Template language delivery status]
    B -- WhatsApp --> E[Template/provider delivery status]
    B -- Visit --> F[Purpose GPS accuracy photos outcome]
    C --> G{Follow-up needed?}
    D --> G
    E --> G
    F --> G
    G -- Yes --> H[Create follow-up/reminder]
    G -- No --> I[Complete event]
    H --> J[Calendar queue notification]
    I --> K[Communication/Master Timeline]
    J --> K
```

## 11. Configuration change

```mermaid
flowchart TD
    A[Open setting] --> B[Review current version and dependencies]
    B --> C[Propose value and effective date]
    C --> D[Preview impact]
    D --> E[Capture reason]
    E --> F{Approval required?}
    F -- No --> G[Schedule/activate new version]
    F -- Yes --> H[Approval queue]
    H --> I{Decision}
    I -- Return --> C
    I -- Reject --> J[Close request]
    I -- Approve --> G
    G --> K[Supersede prior version]
    K --> L[Notify affected users/services]
    L --> M[Configuration and audit timeline]
```

## 12. Audit event pipeline

```mermaid
flowchart LR
    ACTION[Authenticated action or system job] --> CORR[Correlation and actor context]
    CORR --> TX[Business transaction]
    TX --> EVENT[Domain event/outbox]
    EVENT --> AUDIT[Append-only audit event]
    EVENT --> TIME[Customer/loan timeline projection]
    EVENT --> NOTIFY[Notification/task rules]
    EVENT --> ANALYTICS[Analytical/read model refresh]
    AUDIT --> VERIFY[Integrity and retention controls]
```

## 13. Offline collection sync

```mermaid
stateDiagram-v2
    [*] --> Online
    Online --> Offline: connection lost
    Offline --> Queued: safe local action saved
    Queued --> Syncing: connection restored
    Syncing --> Confirmed: server accepts idempotent request
    Syncing --> Conflict: server state changed
    Syncing --> Failed: validation or permission failure
    Conflict --> Review: user/manager resolution
    Review --> Syncing: corrected retry
    Failed --> Review
    Confirmed --> Online
```

Money is never shown as server-confirmed while only queued locally. Local and server references remain distinct until reconciliation.

## 14. Workflow acceptance

Every implemented workflow must match its diagram and include:

- Entry permission
- Preconditions
- State transitions
- Validation
- Confirmation/consequence
- Transaction/idempotency boundary
- Success evidence
- Failure and uncertain outcome
- Notification/timeline/audit effects
- Mobile/offline/reduced-motion behavior
