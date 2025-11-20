import { createFileRoute } from '@tanstack/react-router';
import BienvenidaPage from '@/pages/BienvenidaPage';

export const Route = createFileRoute('/')({
  component: BienvenidaPage,
});
