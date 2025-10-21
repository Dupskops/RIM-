import { createFileRoute } from '@tanstack/react-router';
import LoginPage from '@/pages/LoginPage';
import { requireGuest } from '@/lib/auth-guard';

export const Route = createFileRoute('/login')({
  beforeLoad: requireGuest,
  component: LoginPage,
});
