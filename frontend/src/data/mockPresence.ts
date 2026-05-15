export interface PresenceRecord {
  id: string;
  employeeName: string;
  employeeId: string;
  entryTime: string;
  exitTime: string | null;
  totalHours: string;
  status: "Present" | "Late" | "Early Exit" | "Absent" | "WFH" | "Paid Leave" | "LOP" | "Holiday";
  date: string;
  entryImage?: string;
  exitImage?: string;
  lateEntryMinutes?: number;
  lateEntrySeconds?: number;
  earlyExitMinutes?: number;
  earlyExitSeconds?: number;
  totalBreakTime?: string;
}

export const mockPresence: PresenceRecord[] = [
  { id: "1", employeeName: "Akash", employeeId: "EMP-001", entryTime: "08:02", exitTime: "17:05", totalHours: "9h 03m", status: "Present", date: "2025-04-13" },
  { id: "2", employeeName: "Aswin", employeeId: "EMP-002", entryTime: "09:15", exitTime: "18:00", totalHours: "8h 45m", status: "Late", date: "2025-04-13" },
  { id: "3", employeeName: "Aromal", employeeId: "EMP-003", entryTime: "07:00", exitTime: "14:30", totalHours: "7h 30m", status: "Early Exit", date: "2025-04-13" },
  { id: "4", employeeName: "Akhil", employeeId: "EMP-004", entryTime: "—", exitTime: null, totalHours: "—", status: "Absent", date: "2025-04-13" },
  { id: "5", employeeName: "Greeshma", employeeId: "EMP-005", entryTime: "06:00", exitTime: "14:00", totalHours: "8h 00m", status: "Present", date: "2025-04-13" },
  { id: "6", employeeName: "Vaishnavi", employeeId: "EMP-006", entryTime: "08:00", exitTime: null, totalHours: "—", status: "Present", date: "2025-04-13" },
  { id: "7", employeeName: "Maria", employeeId: "EMP-007", entryTime: "07:05", exitTime: "16:00", totalHours: "8h 55m", status: "Present", date: "2025-04-13" },
  { id: "8", employeeName: "Ambika Menon", employeeId: "EMP-008", entryTime: "09:00", exitTime: "18:10", totalHours: "9h 10m", status: "Present", date: "2025-04-13" },
];

// Extended history for individual employee view
export const mockPresenceHistory: PresenceRecord[] = [
  // Akash history
  { id: "h1", employeeName: "Akash", employeeId: "EMP-001", entryTime: "08:02", exitTime: "17:05", totalHours: "9h 03m", status: "Present", date: "2025-04-13" },
  { id: "h2", employeeName: "Akash", employeeId: "EMP-001", entryTime: "08:00", exitTime: "17:00", totalHours: "9h 00m", status: "Present", date: "2025-04-12" },
  { id: "h3", employeeName: "Akash", employeeId: "EMP-001", entryTime: "08:10", exitTime: "17:00", totalHours: "8h 50m", status: "Late", date: "2025-04-11" },
  { id: "h4", employeeName: "Akash", employeeId: "EMP-001", entryTime: "08:00", exitTime: "17:00", totalHours: "9h 00m", status: "Present", date: "2025-04-10" },
  { id: "h5", employeeName: "Akash", employeeId: "EMP-001", entryTime: "—", exitTime: null, totalHours: "—", status: "Absent", date: "2025-04-09" },
  { id: "h6", employeeName: "Akash", employeeId: "EMP-001", entryTime: "08:01", exitTime: "17:02", totalHours: "9h 01m", status: "Present", date: "2025-04-08" },
  { id: "h7", employeeName: "Akash", employeeId: "EMP-001", entryTime: "07:58", exitTime: "17:00", totalHours: "9h 02m", status: "Present", date: "2025-04-07" },
  // Aswin history
  { id: "h8", employeeName: "Aswin", employeeId: "EMP-002", entryTime: "09:15", exitTime: "18:00", totalHours: "8h 45m", status: "Late", date: "2025-04-13" },
  { id: "h9", employeeName: "Aswin", employeeId: "EMP-002", entryTime: "09:20", exitTime: "18:00", totalHours: "8h 40m", status: "Late", date: "2025-04-12" },
  { id: "h10", employeeName: "Aswin", employeeId: "EMP-002", entryTime: "09:00", exitTime: "18:00", totalHours: "9h 00m", status: "Present", date: "2025-04-11" },
  { id: "h11", employeeName: "Aswin", employeeId: "EMP-002", entryTime: "09:00", exitTime: "18:00", totalHours: "9h 00m", status: "Present", date: "2025-04-10" },
  // Aromal history
  { id: "h12", employeeName: "Aromal", employeeId: "EMP-003", entryTime: "07:00", exitTime: "14:30", totalHours: "7h 30m", status: "Early Exit", date: "2025-04-13" },
  { id: "h13", employeeName: "Aromal", employeeId: "EMP-003", entryTime: "07:00", exitTime: "16:00", totalHours: "9h 00m", status: "Present", date: "2025-04-12" },
  { id: "h14", employeeName: "Aromal", employeeId: "EMP-003", entryTime: "07:05", exitTime: "16:00", totalHours: "8h 55m", status: "Present", date: "2025-04-11" },
  // Vaishnavi history
  { id: "h15", employeeName: "Vaishnavi", employeeId: "EMP-006", entryTime: "08:00", exitTime: "17:00", totalHours: "9h 00m", status: "Present", date: "2025-04-12" },
  { id: "h16", employeeName: "Vaishnavi", employeeId: "EMP-006", entryTime: "08:15", exitTime: "17:00", totalHours: "8h 45m", status: "Late", date: "2025-04-11" },
  // Greeshma history
  { id: "h17", employeeName: "Greeshma", employeeId: "EMP-005", entryTime: "06:00", exitTime: "14:00", totalHours: "8h 00m", status: "Present", date: "2025-04-13" },
  { id: "h18", employeeName: "Greeshma", employeeId: "EMP-005", entryTime: "06:05", exitTime: "14:00", totalHours: "7h 55m", status: "Present", date: "2025-04-12" },
  // Maria history
  { id: "h19", employeeName: "Maria", employeeId: "EMP-007", entryTime: "07:05", exitTime: "16:00", totalHours: "8h 55m", status: "Present", date: "2025-04-13" },
  { id: "h20", employeeName: "Maria", employeeId: "EMP-007", entryTime: "—", exitTime: null, totalHours: "—", status: "Absent", date: "2025-04-12" },
  // Ambika Menon history
  { id: "h21", employeeName: "Ambika Menon", employeeId: "EMP-008", entryTime: "09:00", exitTime: "18:10", totalHours: "9h 10m", status: "Present", date: "2025-04-13" },
  { id: "h22", employeeName: "Ambika Menon", employeeId: "EMP-008", entryTime: "09:05", exitTime: "18:00", totalHours: "8h 55m", status: "Present", date: "2025-04-12" },
  // Akhil history
  { id: "h23", employeeName: "Akhil", employeeId: "EMP-004", entryTime: "—", exitTime: null, totalHours: "—", status: "Absent", date: "2025-04-13" },
  { id: "h24", employeeName: "Akhil", employeeId: "EMP-004", entryTime: "08:00", exitTime: "17:00", totalHours: "9h 00m", status: "Present", date: "2025-04-12" },
];

export const presenceTrendData = [
  { day: "Mon", present: 142, late: 8, absent: 5 },
  { day: "Tue", present: 148, late: 5, absent: 2 },
  { day: "Wed", present: 145, late: 6, absent: 4 },
  { day: "Thu", present: 140, late: 10, absent: 5 },
  { day: "Fri", present: 138, late: 7, absent: 10 },
  { day: "Sat", present: 50, late: 2, absent: 103 },
  { day: "Sun", present: 12, late: 0, absent: 143 },
];
