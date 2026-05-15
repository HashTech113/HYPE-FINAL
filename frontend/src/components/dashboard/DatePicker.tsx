import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { SearchableSelect } from "@/components/ui/searchable-select";

export type DatePickerProps = {
  /** ISO date string (YYYY-MM-DD) or empty for no selection. */
  value: string;
  /** Called with a new ISO date string or empty string on clear. */
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  minYear?: number;
  maxYear?: number;
};

function partsFromIso(iso: string): { year: string; month: string; day: string } {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return { year: "", month: "", day: "" };
  return { year: m[1], month: m[2], day: m[3] };
}

const MIN_YEAR = 1900;
const MAX_YEAR = 2100;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] as const;

function daysInMonth(year: number, month1Based: number): number {
  return new Date(year, month1Based, 0).getDate();
}

function asIso(year: string, month: string, day: string): string {
  if (!year || !month || !day) return "";
  const y = Number(year);
  const m = Number(month);
  const d = Number(day);
  if (!Number.isInteger(y) || !Number.isInteger(m) || !Number.isInteger(d)) return "";
  if (m < 1 || m > 12 || d < 1) return "";
  if (d > daysInMonth(y, m)) return "";
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

export function DatePicker({
  value,
  onChange,
  className,
  disabled,
  minYear = MIN_YEAR,
  maxYear = MAX_YEAR,
}: DatePickerProps) {
  const initialParts = useMemo(() => partsFromIso(value), [value]);
  const [year, setYear] = useState<string>(initialParts.year);
  const [month, setMonth] = useState<string>(initialParts.month);
  const [day, setDay] = useState<string>(initialParts.day);

  useEffect(() => {
    const p = partsFromIso(value);
    setYear(p.year);
    setMonth(p.month);
    setDay(p.day);
  }, [value]);

  const yearOptions = useMemo(() => {
    const out: { value: string; label: string }[] = [];
    for (let y = maxYear; y >= minYear; y -= 1) {
      const yy = String(y);
      out.push({ value: yy, label: yy });
    }
    return out;
  }, [maxYear, minYear]);

  const dayOptions = useMemo(() => {
    const y = Number(year);
    const m = Number(month);
    const maxDays = Number.isInteger(y) && Number.isInteger(m) && m >= 1 && m <= 12
      ? daysInMonth(y, m)
      : 31;
    return Array.from({ length: maxDays }, (_, i) => {
      const value = String(i + 1).padStart(2, "0");
      return { value, label: String(i + 1) };
    });
  }, [year, month]);

  const monthOptions = useMemo(
    () =>
      MONTHS.map((label, idx) => ({
        value: String(idx + 1).padStart(2, "0"),
        label,
      })),
    [],
  );

  const update = (next: { year?: string; month?: string; day?: string }) => {
    const nextYear = next.year ?? year;
    const nextMonth = next.month ?? month;
    let nextDay = next.day ?? day;

    if (nextYear && nextMonth && nextDay) {
      const maxDays = daysInMonth(Number(nextYear), Number(nextMonth));
      if (Number(nextDay) > maxDays) nextDay = String(maxDays).padStart(2, "0");
    }

    setYear(nextYear);
    setMonth(nextMonth);
    setDay(nextDay);
    onChange(asIso(nextYear, nextMonth, nextDay));
  };

  return (
    <div
      className={cn(
        "flex h-10 w-full items-center rounded-md border border-input bg-white px-1.5 shadow-sm",
        disabled && "cursor-not-allowed opacity-60",
        className,
      )}
    >
      <SearchableSelect
        value={month}
        options={monthOptions}
        onValueChange={(v) => update({ month: v })}
        placeholder="Mon"
        disabled={disabled}
        clearValue=""
        className="h-8 w-[72px] shrink-0 rounded-none border-0 bg-transparent px-2 text-sm shadow-none focus-visible:ring-0"
        dropdownClassName="max-h-56"
      />
      <div className="h-5 w-px shrink-0 bg-slate-200" />
      <SearchableSelect
        value={day}
        options={dayOptions}
        onValueChange={(v) => update({ day: v })}
        placeholder="Day"
        disabled={disabled}
        clearValue=""
        className="h-8 w-[64px] shrink-0 rounded-none border-0 bg-transparent px-2 text-sm shadow-none focus-visible:ring-0"
        dropdownClassName="max-h-56"
      />
      <div className="h-5 w-px shrink-0 bg-slate-200" />
      <SearchableSelect
        value={year}
        options={yearOptions}
        onValueChange={(v) => update({ year: v })}
        placeholder="Year"
        disabled={disabled}
        clearValue=""
        className="h-8 min-w-0 flex-1 rounded-none border-0 bg-transparent px-2 text-sm shadow-none focus-visible:ring-0"
        dropdownClassName="max-h-56"
      />
    </div>
  );
}
