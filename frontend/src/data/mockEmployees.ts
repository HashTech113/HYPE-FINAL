export interface Employee {
  id: string;
  name: string;
  employeeId: string;
  company: string;
  department: string;
  shift: string;
  role: "Admin" | "Employee";
  password: string;
  dob: string;
}

export const mockEmployees: Employee[] = [
  { id: "1", name: "Akash", employeeId: "EMP-001", company: "WAWU", department: "Engineering", shift: "08:00-17:00", role: "Employee", password: "pass1234", dob: "1990-03-15" },
  { id: "2", name: "Aswin", employeeId: "EMP-002", company: "WAWU", department: "HR", shift: "09:00-18:00", role: "Admin", password: "admin5678", dob: "1988-07-22" },
  { id: "3", name: "Aromal", employeeId: "EMP-003", company: "WAWU", department: "Operations", shift: "07:00-16:00", role: "Employee", password: "aro9012", dob: "1992-11-08" },
  { id: "4", name: "Akhil", employeeId: "EMP-004", company: "WAWU", department: "Finance", shift: "08:00-17:00", role: "Employee", password: "akh3456", dob: "1995-01-30" },
  { id: "5", name: "Greeshma", employeeId: "EMP-005", company: "WAWU", department: "Security", shift: "06:00-14:00", role: "Employee", password: "gre7890", dob: "1985-06-12" },
  { id: "6", name: "Vaishnavi", employeeId: "EMP-006", company: "WAWU", department: "Engineering", shift: "08:00-17:00", role: "Employee", password: "vai1234", dob: "1993-09-25" },
  { id: "7", name: "Maria", employeeId: "EMP-007", company: "WAWU", department: "Logistics", shift: "07:00-16:00", role: "Employee", password: "mar5678", dob: "1991-04-18" },
  { id: "8", name: "Ambika Menon", employeeId: "EMP-008", company: "WAWU", department: "Marketing", shift: "09:00-18:00", role: "Employee", password: "amb9012", dob: "1994-12-05" },
];

