"use client";

import { X } from "lucide-react";

import { EmployeePicker } from "@/components/training/employee-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { EventType } from "@/lib/types/attendance";
import type { Employee } from "@/lib/types/employee";

export interface EventFiltersState {
  employee: Employee | null;
  dateFrom: string;
  dateTo: string;
  eventType: EventType | "ALL";
}

interface Props {
  value: EventFiltersState;
  onChange: (next: EventFiltersState) => void;
}

export function EventFilters({ value, onChange }: Props) {
  const isEmpty =
    !value.employee &&
    !value.dateFrom &&
    !value.dateTo &&
    value.eventType === "ALL";

  return (
    <div className="grid gap-3 md:grid-cols-[1.2fr,_1fr,_1fr,_1fr,_auto]">
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground">Employee</Label>
        <EmployeePicker
          value={value.employee}
          onChange={(e) => onChange({ ...value, employee: e })}
        />
      </div>
      <DateInputWithClear
        id="date-from"
        label="From"
        value={value.dateFrom}
        onChange={(v) => onChange({ ...value, dateFrom: v })}
      />
      <DateInputWithClear
        id="date-to"
        label="To"
        value={value.dateTo}
        onChange={(v) => onChange({ ...value, dateTo: v })}
      />
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground">Event type</Label>
        <Select
          value={value.eventType}
          onValueChange={(v) =>
            onChange({ ...value, eventType: v as EventType | "ALL" })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All events</SelectItem>
            <SelectItem value="IN">IN</SelectItem>
            <SelectItem value="BREAK_OUT">Break out</SelectItem>
            <SelectItem value="BREAK_IN">Break in</SelectItem>
            <SelectItem value="OUT">OUT</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="flex items-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            onChange({
              employee: null,
              dateFrom: "",
              dateTo: "",
              eventType: "ALL",
            })
          }
          disabled={isEmpty}
        >
          <X className="h-4 w-4" /> Clear all
        </Button>
      </div>
    </div>
  );
}

function DateInputWithClear({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground" htmlFor={id}>
        {label}
      </Label>
      <div className="relative">
        <Input
          id={id}
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={value ? "pr-9" : undefined}
        />
        {value && (
          <button
            type="button"
            aria-label={`Clear ${label}`}
            title={`Clear ${label}`}
            onClick={() => onChange("")}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex h-6 w-6 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
