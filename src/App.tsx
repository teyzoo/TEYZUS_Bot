import {
  useEffect,
  useState
} from "react";

import type {
  MiniAppConfig,
  Page
} from "./types";

import {
  getMiniAppConfig
} from "./api";

import PageLoader from "./components/PageLoader";
import BottomNav from "./components/BottomNav";

import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import ShopPage from "./pages/ShopPage";
import CasesPage from "./pages/CasesPage";
import ProfilePage from "./pages/ProfilePage";
import AdminPage from "./pages/AdminPage";

const fallbackConfig:
  MiniAppConfig = {
    user: {
      id: 1,

      telegram_id: 1,

      username: "user",

      first_name:
        "Пользователь",

      last_name: null,

      role: "user",

      premium_active: false,

      premium_until: null,

      balance_rub: 0,

      stars_balance: 0,

      searches: 0,

      traps: 0
    },

    home: {
      title: "TEYZUS",

      subtitle: "",

      welcome_title:
        "👋 Добро пожаловать!",

      welcome_text:
        "TEYZUS — платформа для поиска, анализа, покупки и продажи Telegram username.",

      banner_enabled: false,

      banner_image: null,

      info_blocks: [
        {
          id: 1,

          emoji: "🔎",

          title:
            "Поиск username",

          text:
            "Находи интересные Telegram username и анализируй их.",

          enabled: true
        },

        {
          id: 2,

          emoji: "🏪",

          title:
            "TEYZUS SHOP",

          text:
            "Покупай и продавай username через безопасные сделки.",

          enabled: true
        },

        {
          id: 3,

          emoji: "🎁",

          title:
            "Кейсы",

          text:
            "Открывай кейсы и получай случайные награды.",

          enabled: true
        }
      ]
    },

    navigation: [
      {
        id: "home",

        title: "Главная",

        icon: "🏠",

        enabled: true,

        page: "home"
      },

      {
        id: "search",

        title: "Поиск",

        icon: "🔎",

        enabled: true,

        page: "search"
      },

      {
        id: "shop",

        title: "SHOP",

        icon: "🏪",

        enabled: true,

        page: "shop"
      },

      {
        id: "cases",

        title: "Кейсы",

        icon: "🎁",

        enabled: true,

        page: "cases"
      },

      {
        id: "profile",

        title: "Профиль",

        icon: "👤",

        enabled: true,

        page: "profile"
      }
    ]
  };

function App() {
  const [
    config,
    setConfig
  ] =
    useState<MiniAppConfig | null>(
      null
    );

  const [
    page,
    setPage
  ] =
    useState<Page>("home");

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const data =
        await getMiniAppConfig();

      setConfig(data);
    } catch {
      /*
       * Временный fallback.
       *
       * После подключения
       * backend эта конфигурация
       * будет приходить из PostgreSQL.
       */

      setConfig(
        fallbackConfig
      );
    }
  }

  if (!config) {
    return <PageLoader />;
  }

  const isOwner =
    config.user.role ===
    "owner";

  const isAdmin =
    config.user.role ===
      "admin" ||
    isOwner;

  function renderPage() {
    switch (page) {

      case "search":
        return (
          <SearchPage />
        );

      case "shop":
        return (
          <ShopPage />
        );

      case "cases":
        return (
          <CasesPage />
        );

      case "profile":
        return (
          <ProfilePage
            user={
              config.user
            }
          />
        );

      case "admin":

        if (!isAdmin) {
          return (
            <HomePage
              user={
                config.user
              }
              config={
                config.home
              }
            />
          );
        }

        return (
          <AdminPage
            user={
              config.user
            }
          />
        );

      case "home":

      default:
        return (
          <HomePage
            user={
              config.user
            }
            config={
              config.home
            }
          />
        );
    }
  }

  /*
   * =======================================================
   * BOTTOM NAVIGATION
   * =======================================================
   */

  let navigation =
    config.navigation.filter(
      item => item.enabled
    );

  /*
   * Обычный пользователь:
   *
   * Главная
   * Поиск
   * SHOP
   * Кейсы
   * Профиль
   */

  navigation =
    navigation.filter(
      item =>
        item.page !==
        "admin"
    );

  /*
   * Owner/Admin получает
   * специальную кнопку.
   *
   * Она добавляется только
   * после проверки роли.
   */

  if (isOwner) {

    navigation.push({
      id: "owner",

      title: "Owner",

      icon: "👑",

      enabled: true,

      page: "admin"
    });

  } else if (
    config.user.role ===
    "admin"
  ) {

    navigation.push({
      id: "admin",

      title: "Admin",

      icon: "🛡️",

      enabled: true,

      page: "admin"
    });
  }

  /*
   * В нижней панели всегда
   * максимум 5 элементов.
   */

  navigation =
    navigation.slice(0, 5);

  return (
    <div className="app">

      <main className="app-content">
        {renderPage()}
      </main>

      <BottomNav
        user={
          config.user
        }

        navigation={
          navigation
        }

        currentPage={
          page
        }

        onNavigate={
          setPage
        }
      />

    </div>
  );
}

export default App;
