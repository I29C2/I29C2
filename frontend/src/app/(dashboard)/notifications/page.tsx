"use client";

import { Bell, FileText, CreditCard, AlertTriangle, Info, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/store/app-store";
import { formatRelativeDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Notification } from "@/lib/mock-data";

const typeConfig: Record<
  Notification["type"],
  { icon: React.ElementType; iconColor: string; iconBg: string }
> = {
  invoice: { icon: FileText, iconColor: "text-indigo-600", iconBg: "bg-indigo-50" },
  expense: { icon: CreditCard, iconColor: "text-amber-500", iconBg: "bg-amber-50" },
  alert: { icon: AlertTriangle, iconColor: "text-red-500", iconBg: "bg-red-50" },
  info: { icon: Info, iconColor: "text-zinc-500", iconBg: "bg-zinc-100" },
};

export default function NotificationsPage() {
  const { notifications, unreadCount, markNotificationRead, markAllRead } = useAppStore();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-900">Notifications</h2>
          <p className="mt-1 text-sm text-zinc-500">
            {unreadCount > 0 ? `${unreadCount} unread` : "All caught up!"}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            className="h-9 gap-2 text-xs"
            onClick={markAllRead}
          >
            <CheckCheck className="h-4 w-4" /> Mark all read
          </Button>
        )}
      </div>

      {/* Notifications list */}
      <div className="space-y-2">
        {notifications.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-zinc-100 bg-white py-16">
            <Bell className="mb-3 h-8 w-8 text-zinc-300" />
            <p className="text-sm text-zinc-400">No notifications yet</p>
          </div>
        )}

        {notifications.map((notification) => {
          const { icon: Icon, iconColor, iconBg } = typeConfig[notification.type];
          return (
            <div
              key={notification.id}
              onClick={() => markNotificationRead(notification.id)}
              className={cn(
                "flex cursor-pointer items-start gap-4 rounded-lg border p-4 transition-colors",
                notification.read
                  ? "border-zinc-100 bg-white hover:bg-zinc-50"
                  : "border-indigo-100 bg-indigo-50/40 hover:bg-indigo-50/70"
              )}
            >
              <div
                className={cn(
                  "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                  iconBg
                )}
              >
                <Icon className={cn("h-4 w-4", iconColor)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p
                    className={cn(
                      "text-sm",
                      notification.read
                        ? "font-medium text-zinc-700"
                        : "font-semibold text-zinc-900"
                    )}
                  >
                    {notification.title}
                  </p>
                  <div className="flex shrink-0 items-center gap-2">
                    {!notification.read && (
                      <div className="h-2 w-2 rounded-full bg-indigo-600" />
                    )}
                    <span className="whitespace-nowrap text-xs text-zinc-400">
                      {formatRelativeDate(notification.createdAt)}
                    </span>
                  </div>
                </div>
                <p className="mt-0.5 text-sm text-zinc-500">{notification.body}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Unread count badge at bottom if needed */}
      {notifications.filter((n) => !n.read).length === 0 && notifications.length > 0 && (
        <div className="flex items-center justify-center gap-2 py-4">
          <CheckCheck className="h-4 w-4 text-emerald-500" />
          <p className="text-sm text-zinc-400">All notifications have been read</p>
        </div>
      )}
    </div>
  );
}
