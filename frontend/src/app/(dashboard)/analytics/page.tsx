"use client";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { invoices, expenses, cashflowData } from "@/lib/mock-data";
import { formatCurrency } from "@/lib/utils";

// Revenue by client (top 8)
const revenueByClient = invoices
  .filter((i) => i.status === "paid")
  .reduce<Record<string, number>>((acc, inv) => {
    acc[inv.client] = (acc[inv.client] ?? 0) + inv.amount;
    return acc;
  }, {});

const topClients = Object.entries(revenueByClient)
  .map(([client, revenue]) => ({ client: client.split(" ")[0], revenue }))
  .sort((a, b) => b.revenue - a.revenue)
  .slice(0, 8);

// Expenses by category
const expensesByCategory = expenses.reduce<Record<string, number>>((acc, exp) => {
  acc[exp.category] = (acc[exp.category] ?? 0) + exp.amount;
  return acc;
}, {});

const expensePieData = Object.entries(expensesByCategory)
  .map(([name, value]) => ({ name, value }))
  .sort((a, b) => b.value - a.value);

const PIE_COLORS = ["#6366f1", "#f87171", "#34d399", "#fbbf24", "#a78bfa", "#60a5fa", "#f472b6", "#4ade80"];

// Invoice status distribution
const invoiceStatusData = [
  { name: "Paid", value: invoices.filter((i) => i.status === "paid").length, color: "#34d399" },
  { name: "Pending", value: invoices.filter((i) => i.status === "pending").length, color: "#fbbf24" },
  { name: "Overdue", value: invoices.filter((i) => i.status === "overdue").length, color: "#f87171" },
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color?: string }>;
  label?: string;
}

function BarTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-zinc-100 bg-white px-3 py-2 shadow-lg">
      <p className="mb-1 text-xs font-semibold text-zinc-700">{label}</p>
      <p className="text-xs text-indigo-600 font-semibold">{formatCurrency(payload[0].value)}</p>
    </div>
  );
}

function PieTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-zinc-100 bg-white px-3 py-2 shadow-lg">
      <p className="text-xs font-semibold text-zinc-900">{payload[0].name}</p>
      <p className="text-xs text-zinc-600">{formatCurrency(payload[0].value)}</p>
    </div>
  );
}

export default function AnalyticsPage() {
  const totalRevenue = invoices.filter((i) => i.status === "paid").reduce((s, i) => s + i.amount, 0);
  const totalExpenses = expenses.reduce((s, e) => s + e.amount, 0);
  const avgMonthlyNet = Math.round(cashflowData.reduce((s, m) => s + m.net, 0) / cashflowData.length);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-zinc-900">Analytics</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Business performance overview — revenue, expenses, and invoice metrics
        </p>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-zinc-100 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Total Revenue Collected</p>
          <p className="mt-2 text-2xl font-bold text-zinc-900">{formatCurrency(totalRevenue)}</p>
          <p className="mt-1 text-xs text-zinc-400">From {invoices.filter((i) => i.status === "paid").length} paid invoices</p>
        </div>
        <div className="rounded-lg border border-zinc-100 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Total Expenses</p>
          <p className="mt-2 text-2xl font-bold text-zinc-900">{formatCurrency(totalExpenses)}</p>
          <p className="mt-1 text-xs text-zinc-400">Across {expenses.length} entries</p>
        </div>
        <div className="rounded-lg border border-zinc-100 bg-white p-5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Avg Monthly Net</p>
          <p className="mt-2 text-2xl font-bold text-emerald-700">{formatCurrency(avgMonthlyNet)}</p>
          <p className="mt-1 text-xs text-zinc-400">6-month average</p>
        </div>
      </div>

      {/* Charts */}
      <Tabs defaultValue="revenue">
        <TabsList className="bg-zinc-100">
          <TabsTrigger value="revenue">Revenue by client</TabsTrigger>
          <TabsTrigger value="expenses">Expense mix</TabsTrigger>
          <TabsTrigger value="invoices">Invoice status</TabsTrigger>
        </TabsList>

        {/* Revenue by client */}
        <TabsContent value="revenue" className="mt-4">
          <Card className="border-zinc-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-zinc-900">
                Revenue by Client (paid invoices)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topClients} layout="vertical" margin={{ top: 0, right: 16, left: 16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" horizontal={false} />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 11, fill: "#a1a1aa" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
                  />
                  <YAxis
                    type="category"
                    dataKey="client"
                    tick={{ fontSize: 11, fill: "#71717a" }}
                    axisLine={false}
                    tickLine={false}
                    width={72}
                  />
                  <Tooltip content={<BarTooltip />} />
                  <Bar dataKey="revenue" fill="#6366f1" radius={[0, 4, 4, 0]} maxBarSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Expenses pie */}
        <TabsContent value="expenses" className="mt-4">
          <Card className="border-zinc-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-zinc-900">Expense Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-8 lg:flex-row lg:items-center">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={expensePieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={110}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {expensePieData.map((_, index) => (
                        <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<PieTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-2 gap-x-6 gap-y-2 lg:w-72 lg:shrink-0">
                  {expensePieData.map((item, i) => (
                    <div key={item.name} className="flex items-center gap-2">
                      <div
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                      />
                      <div>
                        <p className="text-xs font-medium text-zinc-700">{item.name}</p>
                        <p className="text-xs text-zinc-400">{formatCurrency(item.value)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invoice status */}
        <TabsContent value="invoices" className="mt-4">
          <Card className="border-zinc-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-zinc-900">Invoice Status Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-8 lg:flex-row lg:items-center">
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={invoiceStatusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {invoiceStatusData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-4 lg:w-64 lg:shrink-0">
                  {invoiceStatusData.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-sm text-zinc-700">{item.name}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-zinc-900">{item.value}</p>
                        <p className="text-xs text-zinc-400">invoices</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
