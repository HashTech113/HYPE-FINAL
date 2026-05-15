export interface Request {
  id: string;
  employeeName: string;
  employeeId: string;
  type: "Leave (Annual)" | "Leave (Sick)" | "Attendance Correction" | "Shift Change";
  message: string;
  date: string;
  status: "Pending" | "Approved" | "Denied";
}

export const mockRequests: Request[] = [
  { id: "1", employeeName: "Akash", employeeId: "EMP-001", type: "Leave (Annual)", message: "Family event, requires 3 days...", date: "2025-04-10", status: "Approved" },
  { id: "2", employeeName: "Aswin", employeeId: "EMP-002", type: "Attendance Correction", message: "Punch-out missed on 04/08...", date: "2025-04-09", status: "Pending" },
  { id: "3", employeeName: "Aromal", employeeId: "EMP-003", type: "Leave (Sick)", message: "Doctors appointment...", date: "2025-04-11", status: "Denied" },
  { id: "4", employeeName: "Akhil", employeeId: "EMP-004", type: "Leave (Annual)", message: "Punch-out requires request", date: "2025-04-12", status: "Approved" },
  { id: "5", employeeName: "Greeshma", employeeId: "EMP-005", type: "Leave (Annual)", message: "Punch-out missed on 04/15...", date: "2025-04-09", status: "Pending" },
  { id: "6", employeeName: "Vaishnavi", employeeId: "EMP-006", type: "Leave (Sick)", message: "Doctors appointment...", date: "2025-04-10", status: "Pending" },
  { id: "7", employeeName: "Maria", employeeId: "EMP-007", type: "Leave (Annual)", message: "Doctors appointment...", date: "2025-04-10", status: "Pending" },
  { id: "8", employeeName: "Ambika Menon", employeeId: "EMP-008", type: "Shift Change", message: "Request to change shift to 09:00–18:00", date: "2025-04-13", status: "Pending" },
];
