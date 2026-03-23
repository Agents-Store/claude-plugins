# Multi-Bank Account Manager — Broadcast Architecture

## High-Level Architecture

```
                    ┌──────────────────────┐
                    │    Bank MCP Tools     │
                    │ (Monobank, PrivatBank)│
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Bank Sync Module    │
                    │  - Fetch balances     │
                    │  - Fetch transactions │
                    │  - Handle OAuth       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Event Publisher     │
                    │  (Broadcast Hub)      │
                    │                       │
                    │  Events:              │
                    │  • balance_updated    │
                    │  • transaction_added  │
                    │  • budget_alert       │
                    │  • sync_complete      │
                    └──┬────┬────┬────┬────┘
                       │    │    │    │
          ┌────────────┘    │    │    └────────────┐
          │           ┌─────┘    └─────┐           │
          ▼           ▼                ▼           ▼
   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   │  Balance   │ │Transaction │ │  Budget    │ │   Sync     │
   │  Widget    │ │   Feed     │ │  Monitor   │ │  Status    │
   │            │ │            │ │            │ │            │
   │ Subscribes:│ │ Subscribes:│ │ Subscribes:│ │ Subscribes:│
   │ balance_   │ │ transaction│ │ budget_    │ │ sync_      │
   │ updated    │ │ _added     │ │ alert      │ │ complete   │
   └────────────┘ └────────────┘ └────────────┘ └────────────┘
```

## Event Flow Sequence

```
1. User triggers /sync-accounts
2. Bank Sync Module calls MCP balance tools for each bank
3. For each account with changed balance:
   → Publisher emits balance_updated event
   → All subscribers with matching accountFilter receive it
4. Bank Sync Module calls MCP statement tools (last 24h)
5. For each new transaction:
   → Auto-categorize using merchant patterns
   → Publisher emits transaction_added event
   → Budget Monitor checks against thresholds
   → If threshold crossed: Publisher emits budget_alert event
6. After all accounts processed:
   → Publisher emits sync_complete event
```

## Delivery Mechanisms

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  Publisher   │────▶│  Delivery Layer                      │
│             │     │                                      │
│  emit()     │     │  1. WebSocket (real-time, <5s)       │
│             │     │     ws://localhost:8765/events        │
│             │     │                                      │
│             │     │  2. Polling (HTTP fallback)           │
│             │     │     GET /api/events?since=<timestamp> │
│             │     │                                      │
│             │     │  3. File-based (CLI consumers)        │
│             │     │     ~/.multi-bank/events.jsonl        │
└─────────────┘     └──────────────────────────────────────┘
```

## Subscription Model

```
Subscriber registers:
{
  subscriberId: "dashboard-widget-1",
  eventTypes: ["balance_updated", "budget_alert"],
  accountFilter: ["acc_mono_1234", "acc_privat_3456"],
  callbackType: "websocket",
  callbackTarget: "ws://localhost:8765"
}

Publisher maintains registry:
┌──────────────────────────────────────────────┐
│  Subscription Registry                        │
│                                               │
│  widget-1  → [balance_updated] → [mono,privat] │
│  feed-1    → [transaction_added] → [all]      │
│  monitor-1 → [budget_alert] → [all]           │
│  status-1  → [sync_complete] → [all]          │
└──────────────────────────────────────────────┘

On event emit:
  for each subscriber in registry:
    if event.type in subscriber.eventTypes:
      if subscriber.accountFilter is empty OR event.accountId in subscriber.accountFilter:
        deliver(subscriber, event)
```

## Data Flow

```
Bank MCP ──▶ Raw Data ──▶ Encrypted Cache ──▶ Event Publisher ──▶ Subscribers
                              │
                              ▼
                     ~/.multi-bank/data/
                     ├── accounts.enc      (AES-256-GCM)
                     ├── transactions.enc  (AES-256-GCM)
                     ├── budgets.enc       (AES-256-GCM)
                     └── events.jsonl      (append-only log)
```
