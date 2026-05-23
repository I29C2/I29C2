"use client";

import { useState } from "react";
import { FileText, Upload, Search, FileCheck, FileBarChart, File } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { documents, type Document } from "@/lib/mock-data";
import { formatDate } from "@/lib/utils";

const typeConfig: Record<Document["type"], { label: string; icon: React.ElementType; color: string }> = {
  contract: { label: "Contract", icon: FileText, color: "text-indigo-600" },
  invoice: { label: "Invoice", icon: FileCheck, color: "text-emerald-600" },
  report: { label: "Report", icon: FileBarChart, color: "text-amber-500" },
  other: { label: "Other", icon: File, color: "text-zinc-500" },
};

export default function DocumentsPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | Document["type"]>("all");

  const filtered = documents.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(search.toLowerCase()) ||
      doc.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
    const matchesType = typeFilter === "all" || doc.type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-900">Documents</h2>
          <p className="mt-1 text-sm text-zinc-500">
            {documents.length} files · contracts, invoices, reports
          </p>
        </div>
        <Button size="sm" className="h-9 gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
          <Upload className="h-4 w-4" /> Upload document
        </Button>
      </div>

      {/* Type filters */}
      <div className="flex flex-wrap gap-2">
        {(["all", "contract", "invoice", "report", "other"] as const).map((type) => (
          <button
            key={type}
            onClick={() => setTypeFilter(type)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              typeFilter === type
                ? "bg-indigo-600 text-white"
                : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
            }`}
          >
            {type === "all" ? "All" : typeConfig[type].label}
            <span className="ml-1.5 opacity-60">
              {type === "all" ? documents.length : documents.filter((d) => d.type === type).length}
            </span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
        <Input
          placeholder="Search by name or tag..."
          className="pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((doc) => {
          const { icon: Icon, color, label } = typeConfig[doc.type];
          return (
            <div
              key={doc.id}
              className="group cursor-pointer rounded-lg border border-zinc-100 bg-white p-4 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md"
            >
              <div className="mb-3 flex items-start justify-between">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-50 ${color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <Badge variant="outline" className="text-xs">
                  {label}
                </Badge>
              </div>
              <p className="mb-1 text-sm font-medium text-zinc-900 leading-snug line-clamp-2">
                {doc.name}
              </p>
              <p className="text-xs text-zinc-400">{doc.size}</p>

              <div className="mt-3 flex flex-wrap gap-1">
                {doc.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              <div className="mt-3 border-t border-zinc-50 pt-3">
                <p className="text-xs text-zinc-400">
                  {doc.uploadedBy} · {formatDate(doc.uploadedAt)}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="rounded-lg border border-zinc-100 bg-white py-16 text-center shadow-sm">
          <p className="text-sm text-zinc-400">No documents match your search.</p>
        </div>
      )}
    </div>
  );
}
