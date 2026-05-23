import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { invoices } from "@/lib/mock-data";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { InvoiceStatus } from "@/lib/mock-data";

const statusConfig: Record<InvoiceStatus, { label: string; variant: "success" | "warning" | "destructive" | "outline" }> = {
  paid: { label: "Paid", variant: "success" },
  pending: { label: "Pending", variant: "warning" },
  overdue: { label: "Overdue", variant: "destructive" },
};

const recentInvoices = invoices.slice(0, 5);

export function InvoiceTable() {
  return (
    <Card className="border-zinc-100 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold text-zinc-900">Recent Invoices</CardTitle>
            <p className="mt-0.5 text-xs text-zinc-500">Last 5 invoices issued</p>
          </div>
          <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs text-indigo-600 hover:text-indigo-700" asChild>
            <Link href="/invoices">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-100 hover:bg-transparent">
              <TableHead className="px-5 text-xs">Invoice</TableHead>
              <TableHead className="px-5 text-xs">Client</TableHead>
              <TableHead className="hidden px-5 text-xs md:table-cell">Due date</TableHead>
              <TableHead className="px-5 text-right text-xs">Amount</TableHead>
              <TableHead className="px-5 text-xs">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recentInvoices.map((invoice) => {
              const { label, variant } = statusConfig[invoice.status];
              return (
                <TableRow key={invoice.id} className="border-zinc-50 text-sm">
                  <TableCell className="px-5 font-mono text-xs text-zinc-500">
                    {invoice.number}
                  </TableCell>
                  <TableCell className="px-5 font-medium text-zinc-900">
                    {invoice.client}
                  </TableCell>
                  <TableCell className="hidden px-5 text-zinc-500 md:table-cell">
                    {formatDate(invoice.dueDate)}
                  </TableCell>
                  <TableCell className="px-5 text-right font-semibold text-zinc-900">
                    {formatCurrency(invoice.amount)}
                  </TableCell>
                  <TableCell className="px-5">
                    <Badge variant={variant} className="text-xs">
                      {label}
                    </Badge>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
