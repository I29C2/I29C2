"use client";

import { Bell, Menu, Search } from "lucide-react";
import { useAppStore } from "@/store/app-store";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import Link from "next/link";

export function Header({ title }: { title?: string }) {
  const { user, sidebarOpen, toggleSidebar, unreadCount, searchQuery, setSearchQuery } =
    useAppStore();

  return (
    <header className="flex h-14 items-center justify-between border-b border-zinc-100 bg-white px-4 md:px-6">
      {/* Left: toggle + title */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="h-8 w-8 text-zinc-500"
        >
          <Menu className="h-4 w-4" />
        </Button>
        {title && (
          <h1 className="text-sm font-semibold text-zinc-900 md:text-base">{title}</h1>
        )}
      </div>

      {/* Center: Search */}
      <div className="hidden max-w-sm flex-1 px-4 md:flex">
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
          <Input
            placeholder="Search invoices, clients, documents..."
            className="h-8 bg-zinc-50 pl-8 text-xs border-zinc-200 focus-visible:ring-indigo-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <Link href="/notifications">
          <Button variant="ghost" size="icon" className="relative h-8 w-8 text-zinc-500">
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </Button>
        </Link>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-zinc-50 transition-colors">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-indigo-100 text-indigo-700 text-xs font-semibold">
                  {user.avatarInitials}
                </AvatarFallback>
              </Avatar>
              <div className="hidden text-left md:block">
                <p className="text-xs font-medium text-zinc-900 leading-none">{user.name}</p>
                <p className="text-xs text-zinc-500 leading-none mt-0.5">{user.role}</p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel className="font-normal">
              <div>
                <p className="text-sm font-semibold">{user.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{user.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile settings</DropdownMenuItem>
            <DropdownMenuItem>Company settings</DropdownMenuItem>
            <DropdownMenuItem>Billing & plan</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600">Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
