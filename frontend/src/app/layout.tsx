import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { InteractiveAmbientBackground } from '@/components/ui/InteractiveAmbientBackground';
import { CosmicCompanion } from '@/components/ui/CosmicCompanion';

export const metadata: Metadata = {
  title: 'Dhruva.AI — Institutional Intelligence Operating System',
  description:
    'Multi-tenant institutional learning, curriculum governance, mastery measurement, and career intelligence platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div style={{ position: 'relative', minHeight: '100vh', backgroundColor: 'transparent' }}>
          <InteractiveAmbientBackground />
          <AuthProvider>
            <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
            <CosmicCompanion />
          </AuthProvider>
        </div>
      </body>
    </html>
  );
}
