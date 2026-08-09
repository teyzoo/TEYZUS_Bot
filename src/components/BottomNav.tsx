import type {
  MiniAppUser,
  NavigationItem,
  Page
} from "../types";

import {
  haptic
} from "../telegram";

interface BottomNavProps {
  user: MiniAppUser;

  navigation: NavigationItem[];

  currentPage: Page;

  onNavigate: (
    page: Page
  ) => void;
}

export default function BottomNav({
  navigation,
  currentPage,
  onNavigate
}: BottomNavProps) {
  const items =
    navigation.filter(
      item => item.enabled
    );

  return (
    <nav className="bottom-nav">

      {items.map(item => {

        const active =
          currentPage ===
          item.page;

        return (
          <button
            key={item.id}
            className={
              active
                ? "bottom-nav-item active"
                : "bottom-nav-item"
            }
            onClick={() => {
              haptic("light");

              onNavigate(
                item.page
              );
            }}
          >

            <span className="bottom-nav-icon">
              {item.icon}
            </span>

            <span className="bottom-nav-title">
              {item.title}
            </span>

          </button>
        );
      })}

    </nav>
  );
}
