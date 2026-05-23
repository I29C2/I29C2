"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  CreditCard,
  TrendingUp,
  FolderOpen,
  BarChart3,
  Bell,
  Settings,
  Building2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";
import { Separator } from "@/components/ui/separator";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const primaryNav: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Invoices", href: "/invoices", icon: FileText },
  { label: "Expenses", href: "/expenses", icon: CreditCard },
  { label: "Cash Flow", href: "/cashflow", icon: TrendingUp },
  { label: "Documents", href: "/documents", icon: FolderOpen },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
];

const secondaryNav: NavItem[] = [
  { label: "Notifications", href: "/notifications", icon: Bell },
  { label: "Settings", href: "/settings", icon: Settings },
];

function NavLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-zinc-800 text-zinc-100"
          : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-100",
        collapsed && "justify-center px-2"
      )}
      title={collapsed ? item.label : undefined}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-30 flex h-full flex-col bg-zinc-900 transition-all duration-300",
          sidebarOpen ? "w-56" : "w-0 md:w-16",
          "md:relative md:flex"
        )}
      >
        <div
          className={cn(
            "flex h-full flex-col overflow-hidden",
            !sidebarOpen && "md:overflow-visible"
          )}
        >
          {/* Logo */}
          <div
            className={cn(
              "flex h-14 items-center border-b border-zinc-800 px-4",
              !sidebarOpen && "md:justify-center md:px-2"
            )}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600">
              <Building2 className="h-4 w-4 text-white" />
            </div>
            {sidebarOpen && (
              <span className="ml-3 truncate text-sm font-semibold text-zinc-100">
                Control Hub
              </span>
            )}
            {sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(false)}
                className="ml-auto text-zinc-500 hover:text-zinc-300 md:hidden"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Primary nav */}
          <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-4">
            {primaryNav.map((item) => (
              <NavLink key={item.href} item={item} collapsed={!sidebarOpen} />
            ))}

            <div className="my-3 px-1">
              <Separator className="bg-zinc-800" />
            </div>

            {secondaryNav.map((item) => (
              <NavLink key={item.href} item={item} collapsed={!sidebarOpen} />
            ))}
          </nav>

          {/* Footer */}
          {sidebarOpen && (
            <div className="border-t border-zinc-800 px-3 py-3">
              <p className="truncate text-xs text-zinc-600">Meridian Solutions SRL</p>
              <p className="text-xs text-zinc-700">v0.1.0</p>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
