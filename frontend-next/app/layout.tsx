import './globals.css';
import { QueryClientWrapper } from '@/components/QueryClientWrapper';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <QueryClientWrapper>
          <div className="flex h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col">
              <Header />
              <main className="flex-1 overflow-auto p-6">{children}</main>
            </div>
          </div>
        </QueryClientWrapper>
      </body>
    </html>
  );
}
