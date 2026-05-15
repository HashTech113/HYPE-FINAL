import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Download, Search, Settings as SettingsIcon, Users } from "lucide-react";
import { useEmployees } from "@/contexts/EmployeesContext";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { EmployeeManagementTabs } from "@/components/dashboard/EmployeeManagementTabs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { COMPANY_OPTIONS } from "@/components/dashboard/EmployeeForm";
import { formatShiftTo12Hour } from "@/components/dashboard/ShiftTimingPicker";

export const Route = createFileRoute("/_dashboard/employees")({
  component: EmployeesPage,
});

function EmployeesPage() {
  const { employees, scopedCompany, error: loadError, isStale, reload } = useEmployees();
  // HR users see only their own company's roster, so the Company filter and
  // Company column are redundant — hide both.
  const isCompanyScoped = scopedCompany !== null;

  const [selectedCompany, setSelectedCompany] = useState<string>("all");
  const [selectedDepartment, setSelectedDepartment] = useState<string>("all");
  const [selectedEmployee, setSelectedEmployee] = useState<string>("all");

  const companyOptions = useMemo(() => {
    const fromData = Array.from(new Set(employees.map((employee) => employee.company)));
    return Array.from(new Set([...COMPANY_OPTIONS, ...fromData])).sort((a, b) =>
      a.localeCompare(b, undefined, { sensitivity: "base" }),
    );
  }, [employees]);

  const employeesForSelectedCompany = useMemo(
    () =>
      selectedCompany === "all"
        ? employees
        : employees.filter((employee) => employee.company === selectedCompany),
    [employees, selectedCompany]
  );

  const departmentOptions = useMemo(() => {
    const unique = new Set<string>();
    for (const e of employeesForSelectedCompany) {
      const dept = (e.department ?? "").trim();
      if (dept) unique.add(dept);
    }
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [employeesForSelectedCompany]);

  useEffect(() => {
    if (selectedDepartment === "all") return;
    if (!departmentOptions.includes(selectedDepartment)) setSelectedDepartment("all");
  }, [departmentOptions, selectedDepartment]);

  useEffect(() => {
    if (selectedEmployee === "all") return;
    const exists = employeesForSelectedCompany.some((e) => e.employeeId === selectedEmployee);
    if (!exists) setSelectedEmployee("all");
  }, [employeesForSelectedCompany, selectedEmployee]);

  const filtered = useMemo(() => {
    return employeesForSelectedCompany.filter((employee) => {
      if (selectedEmployee !== "all" && employee.employeeId !== selectedEmployee) return false;
      if (selectedDepartment !== "all" && (employee.department ?? "").trim() !== selectedDepartment) return false;
      return true;
    });
  }, [employeesForSelectedCompany, selectedEmployee, selectedDepartment]);
  const employeeFilterOptions = useMemo(
    () => [
      { value: "all", label: "All Employees" },
      ...[...employeesForSelectedCompany]
        .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }))
        .map((emp) => ({
        value: emp.employeeId,
        label: emp.name,
      })),
    ],
    [employeesForSelectedCompany],
  );
  const companyFilterOptions = useMemo(
    () => [
      { value: "all", label: "All Companies" },
      ...companyOptions.map((company) => ({ value: company, label: company })),
    ],
    [companyOptions],
  );
  const departmentFilterOptions = useMemo(
    () => [
      { value: "all", label: "All Employee Roles" },
      ...departmentOptions.map((department) => ({ value: department, label: department })),
    ],
    [departmentOptions],
  );

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Employee Management"
        icon={<Users className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        inlineActions
        actions={
          <>
            <EmployeeManagementTabs />
            <div className="flex w-full flex-wrap items-center gap-2 md:ml-auto md:w-auto md:gap-3">
              <Link to="/settings">
                <Button size="sm" className="h-10 gap-1.5 px-4">
                  <SettingsIcon className="h-4 w-4" />
                  Manage in Settings
                </Button>
              </Link>
              <Button variant="outline" size="sm" className="h-10 gap-1.5 px-4">
                <Download className="h-4 w-4" />Export
              </Button>
            </div>
          </>
        }
      >
      {loadError ? (
        <div
          role="alert"
          className={`mb-3 flex flex-wrap items-center gap-3 rounded-xl border px-4 py-3 text-sm ${
            isStale
              ? "border-amber-200 bg-amber-50 text-amber-800"
              : "border-rose-200 bg-rose-50 text-rose-800"
          }`}
        >
          <span className="flex-1 min-w-[12rem]">{loadError}</span>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => reload()}
            className="h-8 px-3"
          >
            Retry
          </Button>
        </div>
      ) : null}
      <Card className="flex min-h-0 flex-1 flex-col">
        <CardContent className="flex min-h-0 flex-1 flex-col gap-3 px-0 pt-4">
          {/* Filter row — stacks vertically on phones so each label/select
              pair occupies its own full-width row and all selects line up at
              the same right edge. From sm+ it returns to a flex-wrap row. */}
          <div className="flex flex-col gap-2 border-b border-slate-200 pb-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
            <Search className="hidden h-5 w-5 text-primary sm:block" />

            <div className="flex w-full items-center gap-2 sm:w-auto">
              <span className="w-[120px] shrink-0 whitespace-nowrap text-sm font-semibold text-sky-900 sm:w-auto">Employees</span>
              <SearchableSelect
                value={selectedEmployee}
                onValueChange={setSelectedEmployee}
                options={employeeFilterOptions}
                clearValue="all"
                placeholder="All Employees"
                className="h-9 min-w-0 flex-1 border-sky-200 focus-visible:ring-sky-300 sm:w-[160px] sm:flex-initial"
              />
            </div>

            {!isCompanyScoped ? (
              <div className="flex w-full items-center gap-2 sm:w-auto">
                <span className="w-[120px] shrink-0 whitespace-nowrap text-sm font-semibold text-[#393E2E] sm:w-auto">Companies</span>
                <SearchableSelect
                  value={selectedCompany}
                  onValueChange={setSelectedCompany}
                  options={companyFilterOptions}
                  clearValue="all"
                  placeholder="All Companies"
                  className="h-9 min-w-0 flex-1 border-indigo-200 focus-visible:ring-indigo-300 sm:w-[150px] sm:flex-initial"
                />
              </div>
            ) : null}

            <div className="flex w-full items-center gap-2 sm:w-auto">
              <span className="w-[120px] shrink-0 whitespace-nowrap text-sm font-semibold text-emerald-900 sm:w-auto">Employee Roles</span>
              <SearchableSelect
                value={selectedDepartment}
                onValueChange={setSelectedDepartment}
                options={departmentFilterOptions}
                clearValue="all"
                placeholder="All Employee Roles"
                className="h-9 min-w-0 flex-1 border-emerald-200 focus-visible:ring-emerald-300 sm:w-[180px] sm:flex-initial"
              />
            </div>

            <div className="flex items-center gap-2 self-start rounded-lg border border-slate-200 bg-white px-3 py-1.5 sm:ml-auto sm:self-auto">
              <Users className="h-4 w-4 text-primary" />
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Total Employees:
              </span>
              <span className="text-sm font-bold text-slate-900">{filtered.length}</span>
              {filtered.length !== employees.length ? (
                <span className="text-xs font-medium text-slate-400">/ {employees.length}</span>
              ) : null}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-auto">
            <Table className="min-w-[910px] table-fixed">
              <TableHeader>
                <TableRow className="bg-slate-50/60 hover:bg-slate-50/80">
                  <TableHead className="w-14 whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-slate-700 last:border-r-0">S/N</TableHead>
                  <TableHead className="w-[220px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Employee Name</TableHead>
                  <TableHead className="w-[160px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-indigo-700 last:border-r-0">Company</TableHead>
                  <TableHead className="w-[140px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-slate-700 last:border-r-0">Employee ID</TableHead>
                  <TableHead className="w-[160px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-emerald-700 last:border-r-0">Employee Role</TableHead>
                  <TableHead className="w-[150px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-amber-700 last:border-r-0">Shift</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((employee, index) => (
                  <TableRow key={employee.id} className="transition-colors hover:bg-slate-50/60">
                    <TableCell className="border-r border-slate-200 py-2 align-middle text-slate-500 last:border-r-0">{index + 1}</TableCell>
                    <TableCell className="border-r border-slate-200 py-2 align-middle last:border-r-0">
                      <div className="flex min-w-0 items-center gap-3">
                        {employee.imageUrl ? (
                          <img
                            src={employee.imageUrl}
                            alt={employee.name}
                            className="h-10 w-10 shrink-0 rounded-full border border-sky-200 object-cover"
                            loading="lazy"
                          />
                        ) : (
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-500">
                            {(employee.name.trim().charAt(0) || "?").toUpperCase()}
                          </div>
                        )}
                        <span className="min-w-0 break-words whitespace-normal font-medium leading-5 text-foreground">
                          {employee.name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-medium text-indigo-700 last:border-r-0">{employee.company || "—"}</TableCell>
                    <TableCell className="border-r border-slate-200 py-2 align-middle text-slate-500 last:border-r-0">{employee.employeeId}</TableCell>
                    <TableCell className="border-r border-slate-200 py-2 align-middle font-medium leading-5 whitespace-normal break-words text-emerald-700 last:border-r-0">{employee.department || "—"}</TableCell>
                    <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle text-amber-700 last:border-r-0">{formatShiftTo12Hour(employee.shift)}</TableCell>
                  </TableRow>
                ))}
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                      No employees match the current filters.
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      </SectionShell>
    </div>
  );
}
