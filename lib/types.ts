export interface Genre {
  id: number;
  name_ar: string;
  name_en: string;
  slug: string;
  is_active: boolean;
  event_count?: number;
}

export type HydrationStatus = "READY" | "DISCOVERED" | "HYDRATING" | "FAILED" | "PARTIAL";
export type EventStatus = "AVAILABLE" | "SOLD_OUT" | "GHOST" | "UPCOMING";

export interface SeatSection {
  id: string;
  name: string;
  category_name: string;
  price: number;
  available_seats: number;
  total_seats: number;
  color?: string;
}

export interface LiveEvent {
  id: number;
  webook_id: string;
  genre_id?: number | null;
  genre_slug?: string;
  title_ar: string;
  title_en: string;
  slug: string;
  status: EventStatus;
  hydration_status: HydrationStatus;
  venue_name: string;
  venue_address?: string;
  city?: string;
  starts_at?: string;
  ends_at?: string;
  min_price?: number;
  max_price?: number;
  image_url?: string;
  chart_token?: string;
  chart_key?: string;
  seats_provider?: string;
  synced_at: string;
  sections?: SeatSection[];
  description?: string;
}

export type TaskStatus =
  | "CREATED"
  | "QUEUED"
  | "SEARCHING"
  | "PROCESSING"
  | "RUNNING"
  | "HOLDING"
  | "RESERVED"
  | "SUCCESS"
  | "COMPLETED"
  | "FAILED"
  | "RETRYING"
  | "EXPIRED"
  | "CANCELLED";

export interface TaskLogEntry {
  timestamp: string;
  state: string;
  message: string;
}

export interface ReservationTask {
  id: number;
  user_id: number;
  account_id?: string;
  event_slug: string;
  event_title?: string;
  category?: string;
  timeslot_id?: string;
  zone?: string;
  seat_count: number;
  status: TaskStatus;
  worker_id?: string;
  hold_token?: string;
  reservation_id?: string;
  hold_expires_at?: string;
  retry_count: number;
  sniper_mode: boolean;
  error_message?: string;
  created_at: string;
  updated_at: string;
  logs?: TaskLogEntry[];
}

export interface IngestionStats {
  total_events: number;
  ready_events: number;
  discovered_events: number;
  failed_events: number;
  categorized: number;
  uncategorized: number;
  hydrated: number;
  "403_failed": number;
  duplicate_skipped: number;
}

export interface SniperCartItem {
  id: string;
  event_id?: number;
  event_slug: string;
  event_title?: string;
  event_title_ar?: string;
  event_title_en?: string;
  genre_slug?: string;
  category_name?: string;
  venue_name?: string;
  city?: string;
  seat_count: number;
  selected_section: string;
  price_per_seat: number;
  image_url?: string;
  sniper_mode?: boolean;
  sniper_speed?: string;
  added_at?: string;
  status: "IDLE" | "PENDING" | "RUNNING" | "LOCKED" | "FAILED" | "READY";
  hold_token?: string;
  hold_expires_at?: string;
  checkout_url?: string;
  assigned_seats?: string[];
  latency_ms?: number;
  error_message?: string;
  logs?: string[];
}

export interface BatchSniperResult {
  total_requested: number;
  total_succeeded: number;
  total_failed: number;
  duration_ms: number;
  items: SniperCartItem[];
}

export type AccountStatus = "ACTIVE" | "LOGGED_IN" | "LOCKED" | "EXPIRED" | "DISABLED";

export interface WebookAccount {
  id: string;
  email: string;
  phone?: string;
  password?: string;
  token: string;
  status: AccountStatus;
  proxy?: string;
  allocated_seats?: string[];
  hold_token?: string;
  expires_in_sec?: number;
  last_used?: string;
  name?: string;
  notes?: string;
  max_seats?: number;
  created_at?: string;
}
