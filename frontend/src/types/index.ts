export interface User {
  identifier: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_active: boolean
  date_joined: string
  account: Account | null
}

export interface Account {
  identifier: string
  role: Role
  is_active: boolean
}

export interface Role {
  identifier: string
  name: 'admin' | 'analyst' | 'viewer'
  description: string
}

export interface Customer {
  identifier: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  lifecycle_stage: string
  synced_at: string | null
  deal_count: number
}

export interface Deal {
  identifier: string
  customer: string
  customer_email: string
  hubspot_deal_id: string
  deal_name: string
  amount: string
  currency: string
  stage: string
  closed_won_at: string | null
  synced_at: string | null
}

export interface PaymentTransaction {
  identifier: string
  deal: string | null
  customer_email: string
  stripe_payment_intent_id: string
  amount: string
  currency: string
  provider: string
  status: string
  synced_at: string | null
  provider_record: PaymentProviderRecord | null
}

export interface PaymentProviderRecord {
  identifier: string
  provider_payment_id: string
  provider_status: string
  amount_charged: string | null
  webhook_received_at: string | null
}

export interface Anomaly {
  identifier: string
  deal: string | null
  payment_transaction: string | null
  anomaly_type: 'missing_payment' | 'amount_mismatch' | 'overpayment' | 'status_mismatch'
  severity: 'high' | 'medium' | 'low'
  expected_amount: string | null
  actual_amount: string | null
  description: string
  deal_name: string | null
  customer_email: string | null
  is_resolved: boolean
  resolution: Resolution | null
  created: string
}

export interface Resolution {
  identifier: string
  resolution_type: string
  notes: string
  resolved_by_email: string
  resolved_at: string
}

export interface DashboardStats {
  total_anomalies: number
  unresolved_anomalies: number
  resolved_anomalies: number
  by_type: Record<string, number>
  by_severity: Record<string, number>
  last_run_at: string | null
}

export interface AuditLog {
  identifier: string
  action: string
  entity_type: string
  entity_id: string
  user_email: string | null
  old_values: Record<string, unknown> | null
  new_values: Record<string, unknown> | null
  ip_address: string | null
  created: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
