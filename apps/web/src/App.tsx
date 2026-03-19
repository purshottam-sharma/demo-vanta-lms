import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background">
        <header className="border-b">
          <div className="container mx-auto px-4 py-4">
            <h1 className="text-2xl font-bold text-foreground">Vanta LMS</h1>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <p className="text-muted-foreground">Welcome to Vanta LMS</p>
        </main>
      </div>
    </QueryClientProvider>
  );
}
