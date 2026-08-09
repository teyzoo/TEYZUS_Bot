export type UserRole =
  | "user"
  | "admin"
  | "owner";

export type Page =
  | "home"
  | "search"
  | "shop"
  | "cases"
  | "profile"
  | "admin";

export interface MiniAppUser {
  id: number;
  telegram_id: number;

  username: string | null;
  first_name: string | null;
  last_name: string | null;

  role: UserRole;

  premium_active: boolean;
  premium_until: string | null;

  balance_rub: number;
  stars_balance: number;

  searches: number;
  traps: number;
}

export interface HomeConfig {
  title: string;
  subtitle: string;

  welcome_title: string;
  welcome_text: string;

  banner_enabled: boolean;
  banner_image: string | null;

  info_blocks: InfoBlock[];
}

export interface InfoBlock {
  id: number;

  emoji: string;
  title: string;
  text: string;

  enabled: boolean;
}

export interface NavigationItem {
  id: string;

  title: string;
  icon: string;

  enabled: boolean;

  page: Page;
}

export interface MiniAppConfig {
  user: MiniAppUser;

  home: HomeConfig;

  navigation: NavigationItem[];
}

export interface CaseReward {
  id: number;

  title: string;
  emoji: string;

  reward_type: string;

  amount: number;

  premium_days: number;

  chance: number;
}

export interface CaseItem {
  id: number;

  title: string;
  description: string;

  image: string | null;

  price_stars: number;

  enabled: boolean;

  rewards: CaseReward[];
}

/*
 * =========================================================
 * TEYZUS SHOP
 * =========================================================
 */

export interface ShopListing {
  id: number;

  username: string;

  price_rub: number;
  price_stars: number | null;

  seller_id: number;

  seller_username: string | null;

  description: string | null;

  category: string | null;

  is_premium: boolean;

  is_verified: boolean;

  is_favorite: boolean;

  created_at: string;
}

export interface ShopResponse {
  items: ShopListing[];

  total: number;

  page: number;

  per_page: number;
}

export interface ShopFilters {
  search: string;

  category:
    | "all"
    | "popular"
    | "new"
    | "cheap"
    | "premium";

  sort:
    | "new"
    | "price_asc"
    | "price_desc"
    | "popular";
}
