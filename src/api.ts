import type {
  CaseItem,
  MiniAppConfig,
  ShopFilters,
  ShopResponse,
} from "./types";

import {
  getInitData,
} from "./telegram";


const API_URL =
  import.meta.env.VITE_API_URL || "";


/* ========================================================
   REQUEST
   ======================================================== */

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {

  const headers =
    new Headers(
      options.headers,
    );

  headers.set(
    "Content-Type",
    "application/json",
  );

  const initData =
    getInitData();

  if (initData) {
    headers.set(
      "X-Telegram-Init-Data",
      initData,
    );
  }

  const response =
    await fetch(
      `${API_URL}${path}`,
      {
        ...options,
        headers,
      },
    );

  if (!response.ok) {

    let message =
      `API error: ${response.status}`;

    try {

      const data =
        await response.json();

      if (
        data?.detail
      ) {
        message =
          data.detail;
      }

    } catch {
      // ignore
    }

    throw new Error(
      message,
    );
  }

  return response.json()
    as Promise<T>;
}


/* ========================================================
   MINI APP
   ======================================================== */

export async function
getMiniAppConfig():
Promise<MiniAppConfig> {

  return request(
    "/api/miniapp/config",
  );
}


/* ========================================================
   CASES
   ======================================================== */

export async function
getCases():
Promise<CaseItem[]> {

  return request(
    "/api/miniapp/cases",
  );
}


export async function
openCase(
  caseId: number,
): Promise<{
  success: boolean;
  reward?: {
    title: string;
    emoji: string;
    reward_type: string;
    amount: number;
    premium_days: number;
  };
  message: string;
}> {

  return request(
    `/api/miniapp/cases/${caseId}/open`,
    {
      method: "POST",
    },
  );
}


/* ========================================================
   SHOP
   ======================================================== */

export async function
getShopListings(
  filters: ShopFilters,
  page: number = 1,
): Promise<ShopResponse> {

  const params =
    new URLSearchParams();

  if (
    filters.search.trim()
  ) {

    params.set(
      "search",
      filters.search.trim(),
    );
  }

  params.set(
    "category",
    filters.category,
  );

  params.set(
    "sort",
    filters.sort,
  );

  params.set(
    "page",
    String(page),
  );

  params.set(
    "per_page",
    "20",
  );

  return request(
    `/api/miniapp/shop?${params.toString()}`,
  );
}


/* ========================================================
   SHOP FAVORITES
   ======================================================== */

export async function
addFavorite(
  listingId: number,
): Promise<{
  success: boolean;
}> {

  return request(
    `/api/miniapp/shop/${listingId}/favorite`,
    {
      method: "POST",
    },
  );
}


export async function
removeFavorite(
  listingId: number,
): Promise<{
  success: boolean;
}> {

  return request(
    `/api/miniapp/shop/${listingId}/favorite`,
    {
      method: "DELETE",
    },
  );
}


/* ========================================================
   SHOP CART
   ======================================================== */

export interface CartItem {
  listing_id: number;
  username: string;
  title: string;
  price_rub: number;
  price_stars: number | null;
}


export interface CartResponse {
  items: CartItem[];
  total_rub: number;
  total_stars: number;
}


export async function
getCart():
Promise<CartResponse> {

  return request(
    "/api/miniapp/shop/cart/current",
  );
}


export async function
addToCart(
  listingId: number,
): Promise<{
  success: boolean;
  added: boolean;
}> {

  return request(
    `/api/miniapp/shop/${listingId}/cart`,
    {
      method: "POST",
    },
  );
}


export async function
removeFromCart(
  listingId: number,
): Promise<{
  success: boolean;
  removed: boolean;
}> {

  return request(
    `/api/miniapp/shop/${listingId}/cart`,
    {
      method: "DELETE",
    },
  );
}


export async function
clearCart():
Promise<{
  success: boolean;
}> {

  return request(
    "/api/miniapp/shop/cart/current",
    {
      method: "DELETE",
    },
  );
}


/* ========================================================
   SHOP LISTING DETAILS
   ======================================================== */

export interface ShopListingDetails {
  id: number;
  username: string;
  title: string;
  description: string | null;

  price_rub: number;
  price_stars: number | null;

  seller_id: number;
  seller_username: string | null;

  category: string | null;

  is_premium: boolean;
  is_verified: boolean;
  is_favorite: boolean;

  created_at: string;

  views: number;
  favorites_count: number;

  status: string;
}


export async function
getShopListing(
  listingId: number,
):
Promise<ShopListingDetails> {

  return request(
    `/api/miniapp/shop/${listingId}`,
  );
}


/* ========================================================
   CREATE LISTING
   ======================================================== */

export interface CreateListingPayload {
  username: string;
  title: string;
  description?: string | null;

  price_rub: number;
  price_stars?: number | null;

  category?: string | null;

  is_premium?: boolean;
}


export async function
createShopListing(
  payload: CreateListingPayload,
): Promise<{
  success: boolean;
  listing_id: number;
  status: string;
  message: string;
}> {

  return request(
    "/api/miniapp/shop/listings",
    {
      method: "POST",
      body: JSON.stringify(
        payload,
      ),
    },
  );
}
