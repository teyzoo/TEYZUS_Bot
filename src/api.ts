import type {
  CaseItem,
  MiniAppConfig,
  ShopFilters,
  ShopResponse,
  TaskItem,
} from "./types";

import {
  getInitData,
} from "./telegram";


const API_URL =
  import.meta.env.VITE_API_URL ||
  "";


async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {

  const headers =
    new Headers(
      options.headers
    );

  headers.set(
    "Content-Type",
    "application/json"
  );

  const initData =
    getInitData();

  if (initData) {

    headers.set(
      "X-Telegram-Init-Data",
      initData
    );

  }

  const response =
    await fetch(
      `${API_URL}${path}`,
      {
        ...options,
        headers,
      }
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
          String(
            data.detail
          );
      }

    } catch {
      // ignore
    }

    throw new Error(
      message
    );
  }


  return response.json()
    as Promise<T>;
}


// =========================================================
// MINI APP
// =========================================================

export async function
getMiniAppConfig():
Promise<MiniAppConfig> {

  return request<MiniAppConfig>(
    "/api/miniapp/config"
  );
}


// =========================================================
// CASES
// =========================================================

export async function
getCases():
Promise<CaseItem[]> {

  return request<CaseItem[]>(
    "/api/miniapp/cases"
  );
}


export async function
openCase(
  caseId: number
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
    }
  );
}


// =========================================================
// SHOP
// =========================================================

export async function
getShopListings(
  filters: ShopFilters,
  page: number = 1
): Promise<ShopResponse> {

  const params =
    new URLSearchParams();

  if (
    filters.search.trim()
  ) {

    params.set(
      "search",
      filters.search.trim()
    );

  }

  params.set(
    "category",
    filters.category
  );

  params.set(
    "sort",
    filters.sort
  );

  params.set(
    "page",
    String(page)
  );

  params.set(
    "per_page",
    "20"
  );


  return request<ShopResponse>(
    `/api/miniapp/shop?${params.toString()}`
  );
}


export async function
addFavorite(
  listingId: number
): Promise<{
  success: boolean;
}> {

  return request(
    `/api/miniapp/shop/${listingId}/favorite`,
    {
      method: "POST",
    }
  );
}


export async function
removeFavorite(
  listingId: number
): Promise<{
  success: boolean;
}> {

  return request(
    `/api/miniapp/shop/${listingId}/favorite`,
    {
      method: "DELETE",
    }
  );
}


// =========================================================
// TASKS
// =========================================================

export async function
getTasks():
Promise<TaskItem[]> {

  return request<TaskItem[]>(
    "/api/miniapp/tasks"
  );
}


export async function
completeTask(
  taskId: number
): Promise<{
  success: boolean;

  message: string;

  reward_type?: string;

  reward_amount?: number;

  premium_days?: number;
}> {

  return request(
    `/api/miniapp/tasks/${taskId}/complete`,
    {
      method: "POST",
    }
  );
}
