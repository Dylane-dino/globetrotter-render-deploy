export interface Destination {
  id: string;
  name: string;
  category: string;
  tags: string[];
  description: string;
  neighborhood: string;
  rating: number;
  avg_cost_fcfa: number;
  lat: number;
  lng: number;
  images: string[];
  review_count: number;
  like_count: number;
  liked_by_current_user: boolean;
}

export interface RecommendedDestination extends Destination {
  score: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  preferred_tags: string[];
  budget_level: "low" | "medium" | "high" | string;
  bio: string;
  avatar_url?: string | null;
  favorites: string[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
export interface OtpChallenge { email: string; expires_in_seconds: number; message: string; }
export interface DestinationReview { id: string; destination_id: string; user_id: string; user_name: string; rating: number; comment: string; created_at: string; }

export interface ItineraryItem {
  destination_id: string;
  day: number;
  note?: string | null;
}

export interface Itinerary {
  id: string;
  user_id: string;
  title: string;
  items: ItineraryItem[];
  shared_with: string[];
}

export interface ApiErrorBody {
  detail?: string;
}

export interface CommunityComment { id: string; user_name: string; timestamp: string; body: string; }
export interface CommunityPost { id: string; user_name: string; timestamp: string; location_tag: string; title: string; body: string; comments: CommunityComment[]; }
export interface TransportEstimate { mode: string; duration_minutes: number; estimated_cost_fcfa: number; notes: string; }
export interface DestinationHighlight { id: string; name: string; latitude: number; longitude: number; special_highlight: string; best_time_to_visit: string; estimated_stay_duration: string; transport: TransportEstimate[]; }
export interface ChatResponse { message: string; suggested_destinations: DestinationHighlight[]; }
export interface ChatHistoryItem { role: "user" | "assistant"; message: string; }
