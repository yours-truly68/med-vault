"use client";

import { motion } from "framer-motion";
import { User, Stethoscope, Building2, FileHeart, Calendar, Pill, Activity, ShieldCheck } from "lucide-react";
import type { ChatAskResponse } from "@/types/api";
import { StructuredLabValuesGrid } from "./lab-values-grid";

export function SupportingDetailsCards({
  details,
}: {
  details: NonNullable<ChatAskResponse["supporting_details"]>;
}) {
  if (!details) return null;

  const keyMeta = [
    { label: "Patient", value: details.patient, icon: User },
    { label: "Doctor", value: details.doctor, icon: Stethoscope },
    { label: "Hospital / Lab", value: details.hospital, icon: Building2 },
    { label: "Diagnosis", value: details.diagnosis, icon: FileHeart },
    { label: "Follow-up", value: details.follow_up, icon: Calendar },
  ].filter((item) => Boolean(item.value));

  const medicines = details.medicines || [];
  const procedures = details.procedures || [];
  const labValues = details.lab_values || [];

  if (keyMeta.length === 0 && medicines.length === 0 && procedures.length === 0 && labValues.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-3.5 border-t border-border/50 pt-3.5"
    >
      <div className="flex items-center gap-1.5">
        <ShieldCheck className="size-3.5 text-brand-accent" />
        <span className="text-xs font-semibold text-muted-foreground">
          Extracted Clinical Context
        </span>
      </div>

      {/* Key Metadata Cards */}
      {keyMeta.length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {keyMeta.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.15, delay: idx * 0.03 }}
                className="flex items-start gap-2.5 rounded-xl border border-border/60 bg-card p-3 shadow-xs"
              >
                <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
                  <Icon className="size-3.5" />
                </div>
                <div className="min-w-0">
                  <dt className="text-[0.6875rem] font-medium text-muted-foreground">
                    {item.label}
                  </dt>
                  <dd className="mt-0.5 text-xs font-semibold text-foreground line-clamp-2">
                    {item.value}
                  </dd>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : null}

      {/* Structured Lab Values Grid */}
      {labValues.length > 0 ? (
        <StructuredLabValuesGrid items={labValues} />
      ) : null}

      {/* Medicines & Procedures Lists */}
      {medicines.length > 0 || procedures.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {medicines.length > 0 ? (
            <div className="rounded-xl border border-border/60 bg-card p-3 space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                <Pill className="size-3.5 text-primary" />
                <span>Prescribed Medications ({medicines.length})</span>
              </div>
              <ul className="space-y-1 pl-1">
                {medicines.map((med, idx) => (
                  <li
                    key={idx}
                    className="inline-flex items-center gap-1.5 rounded-md bg-muted/40 px-2 py-1 text-xs font-medium text-foreground mr-1.5 mb-1"
                  >
                    <span className="size-1.5 rounded-full bg-brand-accent" />
                    {typeof med === "string" ? med : String(med)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {procedures.length > 0 ? (
            <div className="rounded-xl border border-border/60 bg-card p-3 space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                <Activity className="size-3.5 text-primary" />
                <span>Procedures ({procedures.length})</span>
              </div>
              <ul className="space-y-1">
                {procedures.map((proc, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-foreground bg-muted/30 px-2 py-1 rounded border border-border/40"
                  >
                    {typeof proc === "string" ? proc : String(proc)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </motion.div>
  );
}
