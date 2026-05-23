"use client";

import { useState } from "react";
import { Plus, Download, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { invoices, type InvoiceStatus } from "@/lib/mock-data";
import { formatCurrency, formatDate } from "@/lib/utils";

const statusConfig: Record<InvoiceStatus, { label: string; variant: "success" | "warning" | "destructive" }> = {
  paid: { label: "Paid", variant: "success" },
  pending: { label: "Pending", variant: "warning" },
  overdue: { label: "Overdue", variant: "destructive" },
};

const totalsByStatus = {
  all: invoices.reduce((s, i) => s + i.amount, 0),
  paid: invoices.filter((i) => i.status === "paid").reduce((s, i) => s + i.amount, 0),
  pending: invoices.filter((i) => i.status === "pending").reduce((s, i) => s + i.amount, 0),
  overdue: invoices.filter((i) => i.status === "overdue").reduce((s, i) => s + i.amount, 0),
};

export default function InvoicesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | InvoiceStatus>("all");

  const filtered = invoices.filter((inv) => {
    const matchesSearch =
      inv.client.toLowerCase().includes(search.toLowerCase()) ||
      inv.number.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-900">Invoices</h2>
          <p className="mt-1 text-sm text-zinc-500">
            {invoices.length} invoices · {invoices.filter((i) => i.status === "overdue").length} overdue
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-9 gap-2">
            <Download className="h-4 w-4" /> Export
          </Button>
          <Button size="sm" className="h-9 gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
            <Plus className="h-4 w-4" /> New Invoice
          </Button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {(["all", "paid", "pending", "overdue"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-lg border p-4 text-left transition-colors ${
              statusFilter === s
                ? "border-indigo-200 bg-indigo-50"
                : "border-zinc-100 bg-white hover:border-zinc-200"
            }`}
          >
            <p className="text-xs font-medium capitalize text-zinc-500">{s === "all" ? "All invoices" : s}</p>
            <p className="mt-1 text-lg font-bold text-zinc-900">
              {formatCurrency(totalsByStatus[s])}
            </p>
            <p className="text-xs text-zinc-400">
              {s === "all" ? invoices.length : invoices.filter((i) => i.status === s).length} invoices
            </p>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            placeholder="Search by client or invoice number..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
          <SelectTrigger className="w-full sm:w-[160px]">
            <Filter className="mr-2 h-4 w-4 text-zinc-400" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-zinc-100 bg-white shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-100 hover:bg-transparent">
              <TableHead className="px-5">Invoice #</TableHead>
              <TableHead className="px-5">Client</TableHead>
              <TableHead className="hidden px-5 md:table-cell">Description</TableHead>
              <TableHead className="hidden px-5 lg:table-cell">Issue date</TableHead>
              <TableHead className="px-5">Due date</TableHead>
              <TableHead className="px-5 text-right">Amount</TableHead>
              <TableHead className="px-5">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="py-12 text-center text-sm text-zinc-400">
                  No invoices found matching your criteria.
                </TableCell>
              </TableRow>
            )}
            {filtered.map((invoice) => {
              const { label, variant } = statusConfig[invoice.status];
              return (
                <TableRow key={invoice.id} className="cursor-pointer border-zinc-50 hover:bg-zinc-50">
                  <TableCell className="px-5 font-mono text-xs text-zinc-500">
                    {invoice.number}
                  </TableCell>
                  <TableCell className="px-5 font-medium text-zinc-900">{invoice.client}</TableCell>
                  <TableCell className="hidden max-w-[220px] truncate px-5 text-sm text-zinc-500 md:table-cell">
                    {invoice.description}
                  </TableCell>
                  <TableCell className="hidden px-5 text-sm text-zinc-500 lg:table-cell">
                    {formatDate(invoice.issueDate)}
                  </TableCell>
                  <TableCell className="px-5 text-sm text-zinc-700">
                    {formatDate(invoice.dueDate)}
                  </TableCell>
                  <TableCell className="px-5 text-right font-semibold text-zinc-900">
                    {formatCurrency(invoice.amount)}
                  </TableCell>
                  <TableCell className="px-5">
                    <Badge variant={variant}>{label}</Badge>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
