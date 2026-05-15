export interface HolidayCalendarEntry {
  id: string;
  date: string; // YYYY-MM-DD
  day: string;
  name: string;
  type: "Public Holiday" | "Company Holiday" | "Weekly Off";
}

export const mockHolidayCalendar: HolidayCalendarEntry[] = [
  { id: "hol-2026-01-01", date: "2026-01-01", day: "Thursday", name: "New Year", type: "Public Holiday" },
  { id: "hol-2026-01-04", date: "2026-01-04", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-01-11", date: "2026-01-11", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-01-14", date: "2026-01-14", day: "Wednesday", name: "Maha Sankranti", type: "Public Holiday" },
  { id: "hol-2026-01-18", date: "2026-01-18", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-01-25", date: "2026-01-25", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-01-26", date: "2026-01-26", day: "Monday", name: "Republic Day", type: "Public Holiday" },

  { id: "hol-2026-02-01", date: "2026-02-01", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-02-08", date: "2026-02-08", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-02-15", date: "2026-02-15", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-02-22", date: "2026-02-22", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-03-01", date: "2026-03-01", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-03-08", date: "2026-03-08", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-03-15", date: "2026-03-15", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-03-19", date: "2026-03-19", day: "Thursday", name: "Ugadi", type: "Public Holiday" },
  { id: "hol-2026-03-21", date: "2026-03-21", day: "Saturday", name: "Ramzan", type: "Public Holiday" },
  { id: "hol-2026-03-22", date: "2026-03-22", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-03-29", date: "2026-03-29", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-04-03", date: "2026-04-03", day: "Friday", name: "Good Friday", type: "Public Holiday" },
  { id: "hol-2026-04-05", date: "2026-04-05", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-04-12", date: "2026-04-12", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-04-15", date: "2026-04-15", day: "Wednesday", name: "Vishu", type: "Public Holiday" },
  { id: "hol-2026-04-19", date: "2026-04-19", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-04-26", date: "2026-04-26", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-05-01", date: "2026-05-01", day: "Friday", name: "May Day", type: "Public Holiday" },
  { id: "hol-2026-05-03", date: "2026-05-03", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-05-10", date: "2026-05-10", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-05-17", date: "2026-05-17", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-05-24", date: "2026-05-24", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-05-28", date: "2026-05-28", day: "Thursday", name: "Bakrid (Eid al-Adha)", type: "Public Holiday" },
  { id: "hol-2026-05-31", date: "2026-05-31", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-06-07", date: "2026-06-07", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-06-14", date: "2026-06-14", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-06-21", date: "2026-06-21", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-06-26", date: "2026-06-26", day: "Friday", name: "Muharram", type: "Public Holiday" },
  { id: "hol-2026-06-28", date: "2026-06-28", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-07-05", date: "2026-07-05", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-07-12", date: "2026-07-12", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-07-19", date: "2026-07-19", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-07-26", date: "2026-07-26", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-08-02", date: "2026-08-02", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-08-09", date: "2026-08-09", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-08-15", date: "2026-08-15", day: "Saturday", name: "Independence Day", type: "Public Holiday" },
  { id: "hol-2026-08-16", date: "2026-08-16", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-08-23", date: "2026-08-23", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-08-26", date: "2026-08-26", day: "Wednesday", name: "Onam", type: "Public Holiday" },
  { id: "hol-2026-08-30", date: "2026-08-30", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-09-06", date: "2026-09-06", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-09-13", date: "2026-09-13", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-09-14", date: "2026-09-14", day: "Monday", name: "Ganesh Chaturthi", type: "Public Holiday" },
  { id: "hol-2026-09-20", date: "2026-09-20", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-09-27", date: "2026-09-27", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-10-02", date: "2026-10-02", day: "Friday", name: "Gandhi Jayanti", type: "Public Holiday" },
  { id: "hol-2026-10-04", date: "2026-10-04", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-10-11", date: "2026-10-11", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-10-18", date: "2026-10-18", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-10-20", date: "2026-10-20", day: "Tuesday", name: "Mahanavami / Ayudha Puja", type: "Public Holiday" },
  { id: "hol-2026-10-25", date: "2026-10-25", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-11-01", date: "2026-11-01", day: "Sunday", name: "Kannada Rajyotsava", type: "Public Holiday" },
  { id: "hol-2026-11-08", date: "2026-11-08", day: "Sunday", name: "Diwali / Deepavali", type: "Public Holiday" },
  { id: "hol-2026-11-15", date: "2026-11-15", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-11-22", date: "2026-11-22", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-11-29", date: "2026-11-29", day: "Sunday", name: "Sunday", type: "Weekly Off" },

  { id: "hol-2026-12-06", date: "2026-12-06", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-12-13", date: "2026-12-13", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-12-20", date: "2026-12-20", day: "Sunday", name: "Sunday", type: "Weekly Off" },
  { id: "hol-2026-12-25", date: "2026-12-25", day: "Friday", name: "Christmas", type: "Public Holiday" },
  { id: "hol-2026-12-27", date: "2026-12-27", day: "Sunday", name: "Sunday", type: "Weekly Off" },
];
