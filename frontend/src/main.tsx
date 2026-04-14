import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

//query Client na potrzeby cachowania danych z backendu odmulamy ec2
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // dane 5 min
            gcTime: 1000 * 60 * 30,    // zachowuj dane 30 min
            retry: 2,                 // Ponów 2 razy w przypadku bledu
            refetchOnWindowFocus: false, // Nie odświeżaj przy powrocie do karty
        },
    },
})

// wrapujemy App przez queryClient
createRoot(document.getElementById('root')!).render(
  <StrictMode>
      <QueryClientProvider client={queryClient}>
          <App />
      </QueryClientProvider>
  </StrictMode>,
)
