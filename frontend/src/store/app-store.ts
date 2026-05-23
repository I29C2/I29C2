import { create } from "zustand";
import { notifications as mockNotifications } from "@/lib/mock-data";
import type { Notification } from "@/lib/mock-data";

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarInitials: string;
  company: string;
}

interface AppState {
  // User
  user: User;
  setUser: (user: User) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;

  // Notifications
  notifications: Notification[];
  unreadCount: number;
  markNotificationRead: (id: string) => void;
  markAllRead: () => void;

  // Global search
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // ── User ────────────────────────────────────────────────────────────────────
  user: {
    id: "usr-001",
    name: "Andrei Popescu",
    email: "admin@meridiansolutions.ro",
    role: "Administrator",
    avatarInitials: "AP",
    company: "Meridian Solutions SRL",
  },
  setUser: (user) => set({ user }),

  // ── Sidebar ─────────────────────────────────────────────────────────────────
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // ── Notifications ────────────────────────────────────────────────────────────
  notifications: mockNotifications,
  unreadCount: mockNotifications.filter((n) => !n.read).length,
  markNotificationRead: (id) =>
    set((state) => {
      const updated = state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      );
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.read).length,
      };
    }),
  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),

  // ── Search ───────────────────────────────────────────────────────────────────
  searchQuery: "",
  setSearchQuery: (searchQuery) => set({ searchQuery }),
}));
