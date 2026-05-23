"use client";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, TrendingDown, ArrowUpRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cashflowData } from "@/lib/mock-data";
import { formatCurrency } from "@/lib/utils";

interface TooltipPayload {
  name: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-zinc-100 bg-white px-3 py-2.5 shadow-lg">
      <p className="mb-1.5 text-xs font-semibold text-zinc-700">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="capitalize text-zinc-500">{entry.name}</span>
          </div>
          <span className="font-semibold text-zinc-900">{formatCurrency(entry.value)}</span>
        </div>
      ))}
    </div>
  );
}

const lastMonth = cashflowData[cashflowData.length - 1];
const prevMonth = cashflowData[cashflowData.length - 2];
const netChange = lastMonth.net - prevMonth.net;
const netChangePct = Math.round(((lastMonth.net - prevMonth.net) / prevMonth.net) * 100);

export default function CashflowPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-zinc-900">Cash Flow</h2>
        <p className="mt-1 text-sm text-zinc-500">
          6-month overview — income, expenses, and net position
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-zinc-100 shadow-sm">
          <CardContent className="p-5">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Income (Nov)</p>
            <p className="mt-2 text-2xl font-bold text-zinc-900">
              {formatCurrency(lastMonth.income)}
            </p>
            <div className="mt-1 flex items-center gap-1 text-xs text-emerald-600">
              <TrendingUp className="h-3 w-3" />
              <span>+9.6% vs Oct</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-zinc-100 shadow-sm">
          <CardContent className="p-5">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Expenses (Nov)
            </p>
            <p className="mt-2 text-2xl font-bold text-zinc-900">
              {formatCurrency(lastMonth.expenses)}
            </p>
            <div className="mt-1 flex items-center gap-1 text-xs text-emerald-600">
              <TrendingDown className="h-3 w-3" />
              <span>−24.6% vs Oct</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-zinc-100 shadow-sm">
          <CardContent className="p-5">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Net Cash Flow (Nov)
            </p>
            <p className="mt-2 text-2xl font-bold text-emerald-700">
              {formatCurrency(lastMonth.net)}
            </p>
            <div className="mt-1 flex items-center gap-1 text-xs text-emerald-600">
              <ArrowUpRight className="h-3 w-3" />
              <span>+{netChangePct}% · {formatCurrency(netChange)} more than Oct</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="area">
        <TabsList className="bg-zinc-100">
          <TabsTrigger value="area">Area chart</TabsTrigger>
          <TabsTrigger value="bar">Bar chart</TabsTrigger>
        </TabsList>

        <TabsContent value="area" className="mt-4">
          <Card className="border-zinc-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-zinc-900">
                Income vs Expenses — Area
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={cashflowData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="incGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f87171" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#f87171" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#34d399" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11, fill: "#a1a1aa" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#a1a1aa" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="income" stroke="#6366f1" strokeWidth={2} fill="url(#incGrad)" dot={false} />
                  <Area type="monotone" dataKey="expenses" stroke="#f87171" strokeWidth={2} fill="url(#expGrad)" dot={false} />
                  <Area type="monotone" dataKey="net" stroke="#34d399" strokeWidth={2} fill="url(#netGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bar" className="mt-4">
          <Card className="border-zinc-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-zinc-900">
                Income vs Expenses — Grouped Bars
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={cashflowData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" vertical={false} />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11, fill: "#a1a1aa" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#a1a1aa" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="income" fill="#6366f1" radius={[3, 3, 0, 0]} maxBarSize={36} />
                  <Bar dataKey="expenses" fill="#f87171" radius={[3, 3, 0, 0]} maxBarSize={36} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Monthly table */}
      <Card className="border-zinc-100 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-zinc-900">Monthly Summary</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-100 text-left">
                <th className="px-5 py-3 text-xs font-medium text-zinc-500">Month</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-zinc-500">Income</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-zinc-500">Expenses</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-zinc-500">Net</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-zinc-500">Margin</th>
              </tr>
            </thead>
            <tbody>
              {cashflowData.map((row, i) => {
                const margin = Math.round((row.net / row.income) * 100);
                const isLast = i === cashflowData.length - 1;
                return (
                  <tr
                    key={row.month}
                    className={`border-b border-zinc-50 ${isLast ? "bg-indigo-50/40 font-semibold" : "hover:bg-zinc-50"}`}
                  >
                    <td className="px-5 py-3 text-zinc-900">{row.month} 2024</td>
                    <td className="px-5 py-3 text-right text-zinc-700">{formatCurrency(row.income)}</td>
                    <td className="px-5 py-3 text-right text-red-500">{formatCurrency(row.expenses)}</td>
                    <td className={`px-5 py-3 text-right ${row.net > 0 ? "text-emerald-600" : "text-red-500"}`}>
                      {formatCurrency(row.net)}
                    </td>
                    <td className="px-5 py-3 text-right text-zinc-500">{margin}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
