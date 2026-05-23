"use client";

import { useState } from "react";
import { Plus, Download, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
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
import { expenses, type ExpenseCategory } from "@/lib/mock-data";
import { formatCurrency, formatDate } from "@/lib/utils";

const categories: Array<"all" | ExpenseCategory> = [
  "all",
  "Software",
  "Travel",
  "Office",
  "Marketing",
  "Utilities",
  "HR",
  "Equipment",
  "Legal",
];

const categoryColors: Record<ExpenseCategory, string> = {
  Software: "bg-indigo-500",
  Travel: "bg-sky-500",
  Office: "bg-zinc-400",
  Marketing: "bg-violet-500",
  Utilities: "bg-amber-500",
  HR: "bg-emerald-500",
  Equipment: "bg-orange-500",
  Legal: "bg-rose-500",
};

function getCategoryTotals() {
  const totals: Partial<Record<ExpenseCategory, number>> = {};
  for (const exp of expenses) {
    totals[exp.category] = (totals[exp.category] ?? 0) + exp.amount;
  }
  const grandTotal = Object.values(totals).reduce((a, b) => a + b, 0);
  return Object.entries(totals)
    .map(([cat, amount]) => ({
      category: cat as ExpenseCategory,
      amount,
      percentage: Math.round((amount / grandTotal) * 100),
    }))
    .sort((a, b) => b.amount - a.amount);
}

export default function ExpensesPage() {
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<"all" | ExpenseCategory>("all");

  const categoryTotals = getCategoryTotals();
  const totalAmount = expenses.reduce((s, e) => s + e.amount, 0);
  const pendingApproval = expenses.filter((e) => !e.approved);

  const filtered = expenses.filter((exp) => {
    const matchesSearch =
      exp.description.toLowerCase().includes(search.toLowerCase()) ||
      exp.vendor.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter === "all" || exp.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-900">Expenses</h2>
          <p className="mt-1 text-sm text-zinc-500">
            {expenses.length} entries · {pendingApproval.length} awaiting approval
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-9 gap-2">
            <Download className="h-4 w-4" /> Export
          </Button>
          <Button size="sm" className="h-9 gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
            <Plus className="h-4 w-4" /> Add Expense
          </Button>
        </div>
      </div>

      {/* Top summary + breakdown */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Total */}
        <div className="rounded-lg border border-zinc-100 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Total Nov 2024</p>
          <p className="mt-2 text-3xl font-bold text-zinc-900">{formatCurrency(totalAmount)}</p>
          <p className="mt-1 text-xs text-zinc-400">
            {formatCurrency(pendingApproval.reduce((s, e) => s + e.amount, 0))} pending approval
          </p>
        </div>

        {/* Category breakdown */}
        <div className="lg:col-span-2 rounded-lg border border-zinc-100 bg-white p-5 shadow-sm">
          <p className="mb-4 text-sm font-semibold text-zinc-900">Breakdown by category</p>
          <div className="space-y-3">
            {categoryTotals.slice(0, 5).map(({ category, amount, percentage }) => (
              <div key={category}>
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`h-2 w-2 rounded-full ${categoryColors[category]}`} />
                    <span className="text-xs font-medium text-zinc-700">{category}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-zinc-500">{percentage}%</span>
                    <span className="text-xs font-semibold text-zinc-900">{formatCurrency(amount)}</span>
                  </div>
                </div>
                <Progress value={percentage} className="h-1.5" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <Input
            placeholder="Search by description or vendor..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={categoryFilter} onValueChange={(v) => setCategoryFilter(v as typeof categoryFilter)}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {categories.map((c) => (
              <SelectItem key={c} value={c}>
                {c === "all" ? "All categories" : c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-zinc-100 bg-white shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-100 hover:bg-transparent">
              <TableHead className="px-5">Description</TableHead>
              <TableHead className="hidden px-5 md:table-cell">Vendor</TableHead>
              <TableHead className="px-5">Category</TableHead>
              <TableHead className="hidden px-5 lg:table-cell">Date</TableHead>
              <TableHead className="px-5 text-right">Amount</TableHead>
              <TableHead className="px-5">Approval</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((exp) => (
              <TableRow key={exp.id} className="border-zinc-50">
                <TableCell className="max-w-[240px] truncate px-5 font-medium text-zinc-900">
                  {exp.description}
                </TableCell>
                <TableCell className="hidden px-5 text-sm text-zinc-500 md:table-cell">
                  {exp.vendor}
                </TableCell>
                <TableCell className="px-5">
                  <div className="flex items-center gap-1.5">
                    <div className={`h-2 w-2 rounded-full ${categoryColors[exp.category]}`} />
                    <span className="text-xs text-zinc-600">{exp.category}</span>
                  </div>
                </TableCell>
                <TableCell className="hidden px-5 text-sm text-zinc-500 lg:table-cell">
                  {formatDate(exp.date)}
                </TableCell>
                <TableCell className="px-5 text-right font-semibold text-zinc-900">
                  {formatCurrency(exp.amount)}
                </TableCell>
                <TableCell className="px-5">
                  <Badge variant={exp.approved ? "success" : "warning"}>
                    {exp.approved ? "Approved" : "Pending"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
