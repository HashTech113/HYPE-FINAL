import { useState } from "react";
import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { PromoteToNewPayload } from "@/lib/types/unknowns";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clusterId: number | null;
  submitting: boolean;
  onSubmit: (payload: PromoteToNewPayload) => void;
};

/** Promote an unknown cluster to a brand-new employee. The form mirrors the
 *  minimum fields the Employee model needs; the backend fills the rest with
 *  sensible defaults (auto-generates employee_code, marks active, etc.).
 */
export function PromoteNewDialog({ open, onOpenChange, clusterId, submitting, onSubmit }: Props) {
  const [name, setName] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [department, setDepartment] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  function reset() {
    setName("");
    setEmployeeCode("");
    setDepartment("");
    setCompany("");
    setEmail("");
    setPhone("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    const payload: PromoteToNewPayload = {
      name: name.trim(),
      employee_code: employeeCode.trim() || undefined,
      department: department.trim() || undefined,
      company: company.trim() || undefined,
      email: email.trim() || undefined,
      phone: phone.trim() || undefined,
    };
    onSubmit(payload);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) reset();
        onOpenChange(next);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add as new employee</DialogTitle>
          <DialogDescription>
            {clusterId !== null
              ? `Create an employee from unknown cluster #${clusterId}. The cluster's best face captures will be used as training images.`
              : "Create an employee from this cluster."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="unk-promote-name">Name *</Label>
            <Input
              id="unk-promote-name"
              required
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alice Singh"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="unk-promote-code">Employee ID</Label>
              <Input
                id="unk-promote-code"
                value={employeeCode}
                onChange={(e) => setEmployeeCode(e.target.value)}
                placeholder="auto"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="unk-promote-dept">Department</Label>
              <Input
                id="unk-promote-dept"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="e.g. Engineering"
              />
            </div>
          </div>
          <div className="space-y-1">
            <Label htmlFor="unk-promote-company">Company</Label>
            <Input
              id="unk-promote-company"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g. Grow"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="unk-promote-email">Email</Label>
              <Input
                id="unk-promote-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="optional"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="unk-promote-phone">Phone</Label>
              <Input
                id="unk-promote-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="optional"
              />
            </div>
          </div>
          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || !name.trim()}>
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Add employee
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
