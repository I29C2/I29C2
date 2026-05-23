import { DollarSign, TrendingUp, Receipt, AlertCircle } from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { CashflowChart } from "@/components/dashboard/cashflow-chart";
import { InvoiceTable } from "@/components/dashboard/invoice-table";
import { AiInsightPanel } from "@/components/dashboard/ai-insight-panel";
import { summaryMetrics } from "@/lib/mock-data";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h2 className="text-xl font-bold text-zinc-900">Good morning, Andrei</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Here&apos;s what&apos;s happening at Meridian Solutions today.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Revenue MTD"
          value={summaryMetrics.revenueMTD}
          previousValue={summaryMetrics.revenuePrev}
          icon={DollarSign}
          iconColor="text-indigo-600"
          iconBg="bg-indigo-50"
        />
        <MetricCard
          title="Expenses MTD"
          value={summaryMetrics.expensesMTD}
          previousValue={summaryMetrics.expensesPrev}
          icon={Receipt}
          iconColor="text-red-500"
          iconBg="bg-red-50"
        />
        <MetricCard
          title="Net Cash Flow"
          value={summaryMetrics.netCashFlow}
          previousValue={summaryMetrics.netCashFlowPrev}
          icon={TrendingUp}
          iconColor="text-emerald-600"
          iconBg="bg-emerald-50"
        />
        <MetricCard
          title="Outstanding Invoices"
          value={summaryMetrics.outstandingInvoices}
          icon={AlertCircle}
          iconColor="text-amber-500"
          iconBg="bg-amber-50"
          description={`${summaryMetrics.outstandingCount} invoices · ${summaryMetrics.overdueCount} overdue`}
        />
      </div>

      {/* Charts + AI Insights */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <CashflowChart />
        </div>
        <div className="lg:col-span-1">
          <AiInsightPanel />
        </div>
      </div>

      {/* Recent invoices */}
      <InvoiceTable />
    </div>
  );
}
