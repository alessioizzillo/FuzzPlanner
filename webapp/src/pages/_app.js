import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { StoreProvider } from '@/store'
import '@/styles/globals.css'
import 'reactflow/dist/style.css'

export default function App ({ Component, pageProps }) {
  const [queryClient] = React.useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 20
      }
    }
  }))
  return (
    <QueryClientProvider client={queryClient}>
      <StoreProvider>
        <Component {...pageProps} />
      </StoreProvider>
    </QueryClientProvider>
  )
}
