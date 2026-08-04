"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";
import { formatDateTime } from "@/lib/format";

export function SettingsPageContent() {
  const { data: user, isLoading, isError, refetch } = useCurrentUser();
  const logoutMutation = useLogout();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="Settings"
          description="Manage your account and preferences."
        />
        <LoadingGrid count={2} className="max-w-3xl" />
      </>
    );
  }

  if (isError || !user) {
    return (
      <>
        <PageHeader title="Settings" />
        <ErrorState
          message="We couldn't load your profile."
          onRetry={() => void refetch()}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your account and preferences."
      />

      <div className="mx-auto max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>Your MedVault account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p className="font-medium">Full name</p>
              <p className="text-muted-foreground">{user.full_name}</p>
            </div>
            <div>
              <p className="font-medium">Email</p>
              <p className="text-muted-foreground">{user.email}</p>
            </div>
            <div>
              <p className="font-medium">Member since</p>
              <p className="text-muted-foreground">
                {formatDateTime(user.created_at)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Choose how MedVault looks on this device</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Label htmlFor="theme">Theme</Label>
            <Select
              value={mounted ? (theme ?? "system") : "system"}
              onValueChange={setTheme}
            >
              <SelectTrigger id="theme" className="w-full sm:w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session</CardTitle>
            <CardDescription>Sign out of MedVault on this device</CardDescription>
          </CardHeader>
          <CardContent>
            <Separator className="mb-4" />
            <Button
              variant="destructive"
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
            >
              {logoutMutation.isPending ? "Signing out..." : "Sign out"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
