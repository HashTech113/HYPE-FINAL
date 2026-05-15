export interface Alert {
  id: string;
  type: "warning" | "critical" | "info";
  title: string;
  description: string;
  timestamp: string;
  employee?: string;
}

export const mockAlerts: Alert[] = [
  { id: "1", type: "critical", title: "Unauthorized Entry Detected", description: "Unknown badge scanned at Gate B — no match in system", timestamp: "2025-04-13T14:32:00", employee: "Unknown" },
  { id: "2", type: "warning", title: "Late Arrival Pattern", description: "Employee has been late 5 days this week", timestamp: "2025-04-13T09:20:00", employee: "Aswin" },
  { id: "3", type: "info", title: "Shift Change Approved", description: "Ambika Menon's shift updated to 09:00–18:00", employee: "Ambika Menon", timestamp: "2025-04-13T08:00:00" },
  { id: "4", type: "warning", title: "After-Hours Access", description: "Greeshma accessed building at 22:45", employee: "Greeshma", timestamp: "2025-04-12T22:45:00" },
  { id: "5", type: "critical", title: "Camera Offline", description: "Gate C camera offline for 2+ hours", timestamp: "2025-04-13T12:00:00" },
  { id: "6", type: "info", title: "New Employee Added", description: "Maria was added to WAWU – Logistics", employee: "Maria", timestamp: "2025-04-12T10:00:00" },
];

export const alertRules = {
  lateThreshold: 15,
  earlyExitThreshold: 30,
  multipleExitsThreshold: 3,
  afterHoursStart: "20:00",
  afterHoursEnd: "06:00",
};
