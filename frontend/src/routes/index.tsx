import { createFileRoute } from '@tanstack/react-router';
import LoginPage from '@/pages/LoginPage';
import { requireGuest } from '@/lib/auth-guard';

export const Route = createFileRoute('/')({
  beforeLoad: requireGuest,
  component: LoginPage,
});
