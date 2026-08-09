import {
  useEffect,
  useState
} from "react";

import type {
  ShopFilters,
  ShopListing
} from "../types";

import {
  getShopListings,
  addFavorite,
  removeFavorite
} from "../api";

import {
  haptic
} from "../telegram";

const DEFAULT_FILTERS:
  ShopFilters = {
    search: "",

    category: "all",

    sort: "new"
  };

export default function ShopPage() {
  const [
    listings,
    setListings
  ] = useState<ShopListing[]>([]);

  const [
    filters,
    setFilters
  ] = useState<ShopFilters>(
    DEFAULT_FILTERS
  );

  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    error,
    setError
  ] = useState<string | null>(
    null
  );

  const [
    searchValue,
    setSearchValue
  ] = useState("");

  const [
    favoritesLoading,
    setFavoritesLoading
  ] = useState<number | null>(
    null
  );

  useEffect(() => {
    loadListings();
  }, [
    filters.category,
    filters.sort
  ]);

  async function loadListings() {
    setLoading(true);
    setError(null);

    try {
      const response =
        await getShopListings(
          filters,
          1
        );

      setListings(
        response.items
      );
    } catch {
      /*
       * Пока backend SHOP ещё
       * не подключён, показываем
       * пустое состояние.
       */
      setListings([]);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch() {
    setFilters(
      previous => ({
        ...previous,

        search:
          searchValue.trim()
      })
    );

    haptic("light");
  }

  async function toggleFavorite(
    item: ShopListing
  ) {
    if (
      favoritesLoading !== null
    ) {
      return;
    }

    setFavoritesLoading(
      item.id
    );

    haptic("light");

    try {
      if (item.is_favorite) {
        await removeFavorite(
          item.id
        );
      } else {
        await addFavorite(
          item.id
        );
      }

      setListings(
        previous =>
          previous.map(
            listing =>
              listing.id ===
              item.id
                ? {
                    ...listing,
                    is_favorite:
                      !listing.is_favorite
                  }
                : listing
          )
      );
    } catch {
      /*
       * Ошибку можно будет
       * показать Toast позже.
       */
    } finally {
      setFavoritesLoading(
        null
      );
    }
  }

  function selectCategory(
    category: ShopFilters["category"]
  ) {
    haptic("light");

    setFilters(
      previous => ({
        ...previous,
        category
      })
    );
  }

  function setSort(
    sort: ShopFilters["sort"]
  ) {
    setFilters(
      previous => ({
        ...previous,
        sort
      })
    );
  }

  return (
    <div className="page shop-page">

      <div className="shop-top">

        <div>
          <div className="section-title">
            🏪 TEYZUS SHOP
          </div>

          <div className="section-subtitle">
            Покупай и продавай
            Telegram username.
          </div>
        </div>

      </div>

      <div className="shop-search">

        <div className="shop-search-input">

          <span>
            🔎
          </span>

          <input
            value={searchValue}
            onChange={event =>
              setSearchValue(
                event.target.value
              )
            }
            onKeyDown={event => {
              if (
                event.key ===
                "Enter"
              ) {
                handleSearch();
              }
            }}
            placeholder="Найти username..."
            autoComplete="off"
            spellCheck={false}
          />

          {searchValue && (
            <button
              className="clear-search"
              onClick={() => {
                setSearchValue("");
                setFilters(
                  previous => ({
                    ...previous,
                    search: ""
                  })
                );
              }}
            >
              ×
            </button>
          )}

        </div>

        <button
          className="shop-search-button"
          onClick={
            handleSearch
          }
        >
          Найти
        </button>

      </div>

      <div className="shop-categories">

        <button
          className={
            filters.category ===
            "all"
              ? "shop-category active"
              : "shop-category"
          }
          onClick={() =>
            selectCategory(
              "all"
            )
          }
        >
          🏪 Все
        </button>

        <button
          className={
            filters.category ===
            "popular"
              ? "shop-category active"
              : "shop-category"
          }
          onClick={() =>
            selectCategory(
              "popular"
            )
          }
        >
          🔥 Популярные
        </button>

        <button
          className={
            filters.category ===
            "new"
              ? "shop-category active"
              : "shop-category"
          }
          onClick={() =>
            selectCategory(
              "new"
            )
          }
        >
          🆕 Новые
        </button>

        <button
          className={
            filters.category ===
            "cheap"
              ? "shop-category active"
              : "shop-category"
          }
          onClick={() =>
            selectCategory(
              "cheap"
            )
          }
        >
          💰 Дешёвые
        </button>

        <button
          className={
            filters.category ===
            "premium"
              ? "shop-category active"
              : "shop-category"
          }
          onClick={() =>
            selectCategory(
              "premium"
            )
          }
        >
          💎 Premium
        </button>

      </div>

      <div className="shop-toolbar">

        <span>
          {filters.search
            ? `Поиск: ${filters.search}`
            : "Все username"}
        </span>

        <select
          value={filters.sort}
          onChange={event =>
            setSort(
              event.target
                .value as ShopFilters["sort"]
            )
          }
        >
          <option value="new">
            Новые
          </option>

          <option value="price_asc">
            Дешевле
          </option>

          <option value="price_desc">
            Дороже
          </option>

          <option value="popular">
            Популярные
          </option>
        </select>

      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loader-spinner" />

          <p>
            Загружаем TEYZUS SHOP...
          </p>
        </div>
      ) : error ? (
        <div className="empty-state">

          <div className="empty-icon">
            ⚠️
          </div>

          <strong>
            Не удалось загрузить
            магазин
          </strong>

          <button
            className="primary-button"
            onClick={
              loadListings
            }
          >
            Повторить
          </button>

        </div>
      ) : listings.length ===
        0 ? (
        <div className="empty-state">

          <div className="empty-icon">
            🏪
          </div>

          <strong>
            Пока нет объявлений
          </strong>

          <p>
            Здесь будут появляться
            username из TEYZUS SHOP.
          </p>

        </div>
      ) : (
        <div className="shop-list">

          {listings.map(item => (
            <article
              className="shop-listing"
              key={item.id}
            >

              <div className="shop-listing-main">

                <div className="shop-listing-username">
                  @{item.username}
                </div>

                <div className="shop-listing-meta">

                  {item.is_verified && (
                    <span>
                      ✓ Проверен
                    </span>
                  )}

                  {item.is_premium && (
                    <span>
                      💎 Premium
                    </span>
                  )}

                </div>

                {item.description && (
                  <p>
                    {item.description}
                  </p>
                )}

                <div className="shop-listing-seller">
                  Продавец:{" "}
                  {item.seller_username
                    ? `@${item.seller_username}`
                    : "скрыт"}
                </div>

              </div>

              <div className="shop-listing-right">

                <button
                  className="favorite-button"
                  disabled={
                    favoritesLoading ===
                    item.id
                  }
                  onClick={() =>
                    toggleFavorite(
                      item
                    )
                  }
                >
                  {item.is_favorite
                    ? "❤️"
                    : "🤍"}
                </button>

                <div className="shop-price">
                  {item.price_rub.toLocaleString(
                    "ru-RU"
                  )} ₽
                </div>

                {item.price_stars !==
                  null && (
                  <div className="shop-stars">
                    ⭐{" "}
                    {
                      item.price_stars
                    }
                  </div>
                )}

                <button
                  className="shop-open-button"
                  onClick={() =>
                    haptic(
                      "light"
                    )
                  }
                >
                  Подробнее
                </button>

              </div>

            </article>
          ))}

        </div>
      )}

      <div className="shop-bottom-menu">

        <button>
          🛒
          <span>
            Корзина
          </span>
        </button>

        <button>
          ❤️
          <span>
            Избранное
          </span>
        </button>

        <button>
          📦
          <span>
            Мои покупки
          </span>
        </button>

        <button>
          🏷️
          <span>
            Мои объявления
          </span>
        </button>

      </div>

    </div>
  );
}
